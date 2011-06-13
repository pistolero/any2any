# -*- coding: utf-8 -*-
import copy

class ClassSet(object):

    def __init__(self, klass, singleton=False):
        self.klass = klass
        self.singleton = singleton

    def __eq__(self, other):
        if isinstance(other, ClassSet):
            return (self.klass, self.singleton) == (other.klass, other.singleton)
        else:
            return NotImplemented
        
    def __ne__(self, other):
        return not self == other

    # NB : We cannot use total_ordering,
    # because there are cases where two sets are not comparable
    def __lt__(self, other):
        # *other* can include self, only if *other* is not a singleton.
        # So there are only 2 cases where self < other:
        # A) {self.klass} < other.klass
        # B) self.klass < other.klass
        if other.singleton:
            return False
        elif Spz.issubclass(self.klass, other.klass) and not other == self:
            return True
        else:
            return False

    def __gt__(self, other):
        if self.singleton:
            return False
        elif Spz.issubclass(other.klass, self.klass) and not other == self:
            return True
        else:
            return False

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def __repr__(self):
        return u'%s' % self.klass if self.singleton else u'Any %s' % self.klass


class Metamorphosis(object):
    """
    A metamorphosis between two types :

        >>> mm = Metamorphosis(Mammal, Human)

    This represents the metamorphosis from a Mammal to a Human.

    Kwargs:
        from_(type). Metamorphosis only from type *from_* (and no subclass).
        to(type). Metamorphosis only to type *to* (and no subclass).
        from_any(type). Metamorphosis from type *from_any* and subclasses.
        to_any(type). Metamorphosis from type *to_any* and subclasses.
    """

    def __init__(self, from_=None, to=None, from_any=None, to_any=None):
        if from_any and from_:
            raise TypeError("Arguments 'from_any' and 'from_' cannot be provided at the same time")
        elif not from_any and not from_:
            raise TypeError("You must provide 'from_' or 'from_any'")
        else:
            pass
        if to_any and to:
            raise TypeError("Arguments 'to_any' and 'to' cannot be provided at the same time")
        elif not to_any and not to:
            raise TypeError("You must provide 'to' or 'to_any'")
        else:
            pass
        # Sets used for easier comparison 
        self._to_set = ClassSet(to or to_any, singleton=bool(to))
        self._from_set = ClassSet(from_ or from_any, singleton=bool(from_))
        # Keeping the arguments at hand
        self.from_any = from_any
        self.from_ = from_
        self.to_any = to_any
        self.to = to

    def pick_closest_in(self, choice_list):
        """
        Given a list of metamorphoses, returns the one that is the closest to the calling metamorphosis.
        """
        # When picking-up a metamorphosis in choice_list:
        # if 
        candidates = filter(self.included_in, choice_list)
        if not candidates:
            raise ValueError("No suitable metamorphosis found for '%s'" % self)
        else:
            return sorted(candidates)[0]

    def included_in(self, other, strict=False):
        if strict and self != other:
            return False
        return self._from_set <= other._from_set and self._to_set <= other._to_set

    @staticmethod
    def most_precise(m1, m2):
        """
        Returns:
            Metamorphosis. The most precise metamorphosis between m1 and m2
        """
        # There are 10 cases (excluding symetric cases):
        # A) m1 = m2                                    -> None
        #
        # B) m1 C m2
        #   m1.from < m2.from, m1.to < m2.to            -> m1
        #   m1.from = m2.from, m1.to < m2.to            -> m1
        #   m1.from < m2.from, m1.to = m2.to            -> m1
        #
        # C) m1 ? m2
        #   a) m1.from > m2.from, m1.to < m2.to         -> m1
        #   b) m1.from ? m2.from, m1.to < m2.to         -> m1
        #   c) m1.from < m2.from, m1.to ? m2.to         -> m1
        #   d) m1.from ? m2.from, m1.to ? m2.to         -> None
        #   e) m1.from ? m2.from, m1.to = m2.to         -> None
        #   f) m1.from = m2.from, m1.to ? m2.to         -> None

        if m1 == m2:# A)
            return None

        elif m1.included_in(m2) or m2.included_in(m1):# B)
            return m1 if m1.included_in(m2) else m2

        elif m1._to_set < m2._to_set or m2._to_set < m1._to_set:# C) : a), b)
            return m1 if m1._to_set < m2._to_set else m2

        elif m1._from_set < m2._from_set or m2._from_set < m1._from_set:#C) : c)
            return m1 if m1._from_set < m2._from_set else m2

        else: #C) : d), e), f)
            return None

    def __lt__(self, other):
        return self.most_precise(self, other) == self

    def __gt__(self, other):
        return self.most_precise(self, other) == other

    def __le__(self, other):
        return self.most_precise(self, other) == self or self == other

    def __ge__(self, other):
        return self.most_precise(self, other) == other or self == other

    def __eq__(self, other):
        if isinstance(other, Metamorphosis):
            return self._from_set == other._from_set and self._to_set == other._to_set
        else:
            return NotImplemented
 
    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return 'Mm(%s, %s)' % (self._from_set, self._to_set)

    def __hash__(self):
        return (self.from_, self.to, self.from_any, self.to_any).__hash__()
Mm = Metamorphosis


class Specialization(type):
    """
    A class for building specialized classes. For example, this allows to define ``a list of int`` :

        >>> int_list = Spz(list, int)
        >>> object_list = Spz(list, object)
        
    Then, using :meth:`Spz.issubclass` :
        
        >>> Spz.issubclass(int_list, list)
        True
        >>> Spz.issubclass(list, int_list)
        False
        >>> Spz.issubclass(int_list, object_list)
        True
        >>> Spz.issubclass(object_list, int_list)
        False
    """

    defaults = {}

    def __new__(cls, *args, **kwargs):
        new_spz = super(Specialization, cls).__new__(cls)
        new_spz._features = copy.copy(cls.defaults)
        return new_spz

    def __init__(self, base, **features):
        self.base = base
        unknown_features = set(features) - set(self._features)
        if unknown_features:
            raise TypeError("%s are not valid features for %s"\
            % (','.join(unknown_features), type(self)))
        self._features.update(features)

    def __getattr__(self, name):
        try:
            return self._features[name]
        except KeyError:
            return self.__getattribute__(name)

    def issuperclass(self, C):
        if isinstance(C, Spz):
            return Spz.issubclass(C.base, self.base)
        else:
            return False

    @staticmethod
    def issubclass(C1, C2):
        if isinstance(C2, Spz):
            return C2.issuperclass(C1)
        elif isinstance(C1, Spz):
            return issubclass(C1.base, C2)
        else:
            return issubclass(C1, C2)

    def __repr__(self):
        return 'Spz(%s, %s)' % (self.base, self.feature)

    def __eq__(self, other):
        return Spz.issubclass(self, other) and Spz.issubclass(other, self) 
Spz = Specialization


def closest_parent(klass, other_classes):
    """
    Returns:
        The closest parent of *klass* picked from the list *other_classes*. If no parent was found in *other_classes*, returns *object*.
    """
    #We select only the super classes of *klass*
    candidates = []
    for oclass in other_classes:
        if Spz.issubclass(klass, oclass):
            candidates.append(oclass)

    #This is used to sort the list and take the closer parent of *klass*
    class K(object):
        def __init__(self, klass):
            self.klass = klass
        def __lt__(self, other):
            return Spz.issubclass(self.klass, other.klass)
        def __eq__(self, other):
            return self.klass == other.klass
        def __gt__(self, other):
            return Spz.issubclass(other.klass, klass.klass)
    
    if not candidates:
        return object
    else:
        return sorted(candidates, key=K)[0]


def copied_values(dict_iter):
    for name, value in dict_iter:
        try:
            yield name, copy.copy(value)
        except:
            yield name, value
    raise StopIteration
