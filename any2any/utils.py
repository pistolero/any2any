# -*- coding: utf-8 -*-
import copy
try:
    import abc
except ImportError:
    from compat import abc


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

    def __lt__(self, other):
        # *other* can include self, only if *other* is not a singleton.
        # So there are only 2 cases where self < other:
        # A) {self.klass} < other.klass
        # B) self.klass < other.klass
        if other.singleton:
            return False
        elif issubclass(self.klass, other.klass) and not other == self:
            return True
        else:
            return False

    def __gt__(self, other):
        if self.singleton:
            return False
        elif issubclass(other.klass, self.klass) and not other == self:
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
    #TODO: refactor for having sets, and single mm
    def __init__(self, from_=None, to=None, from_any=None, to_any=None):
        if not from_any and not from_:
            from_any = object
        elif from_any and from_:
            raise TypeError("Arguments 'from_any' and 'from_' cannot be provided at the same time")
        else:
            pass
        if not to_any and not to:
            to_any = object
        elif to_any and to:
            raise TypeError("Arguments 'to_any' and 'to' cannot be provided at the same time")
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


class SpecializedType(abc.ABCMeta):
    """
    A metaclass for building specialized types.

        >>> PositiveInt = SpecializedType(int, greater_than=0)
        >>> issubclass(PositiveInt, int)
        True
        >>> PositiveInt.greater_than
        0
    """

    defaults = {}

    def __new__(cls, base, **features):
        name = 'SpzOf%s' % base.__name__.capitalize()
        bases = (base,)
        attrs = copy.copy(cls.defaults)
        attrs['base'] = base
        attrs['features'] = features
        new_spz = super(SpecializedType, cls).__new__(cls, name, bases, attrs)
        new_spz.__subclasshook__ = classmethod(cls.__subclasshook__)
        return new_spz

    def __init__(self, base, **features):
        for name, value in features.items():
            setattr(self, name, value)

    def __subclasshook__(self, C):
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, SpecializedType):
            return (self.__bases__ == other.__bases__) and (self.features == other.features)
        else:
            return False

            
def closest_parent(klass, other_classes):
    """
    Returns:
        The closest parent of *klass* picked from the list *other_classes*. If no parent was found in *other_classes*, returns *object*.
    """
    #We select only the super classes of *klass*
    candidates = []
    for oclass in other_classes:
        if issubclass(klass, oclass):
            candidates.append(oclass)

    #This is used to sort the list and take the closer parent of *klass*
    class K(object):
        def __init__(self, klass):
            self.klass = klass
        def __lt__(self, other):
            return issubclass(self.klass, other.klass)
        def __eq__(self, other):
            return self.klass == other.klass
        def __gt__(self, other):
            return issubclass(other.klass, klass.klass)
    
    if not candidates:
        return object
    else:
        return sorted(candidates, key=K)[0]
