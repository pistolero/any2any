"""
"""

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

    This represents the metamorphosis from any instance of Mammal to an instance of Human.

    Now let's say I want to cast a Shark to a Human ... but, I can get a cast from any Animal, to a Salesman ::

        Mm_I_want =     FROM   Shark   TO   Human
                                |             A
                                V             |
        Mm_I_can_get =  FROM   Animal  TO   Salesman

    I'll say that this will fit my needs, because after all a Shark is an animal, and a Salesman is a Human. In other words :

        >>> Metamorphosis(Shark, Human).included_in(Metamorphosis(Animal, Salesman))
        True
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
        .. todo:: if triangle, then random choice will be picked ...
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
        # A) m1 = m2                                        -> None
        #
        # B) m1 C m2
        #   m1.from < m2.from, m1.to < m2.to        -> m1
        #   m1.from = m2.from, m1.to < m2.to        -> m1
        #   m1.from < m2.from, m1.to = m2.to        -> m1
        #
        # C) m1 ? m2
        #   a) m1.from > m2.from, m1.to < m2.to        -> m1
        #   b) m1.from ? m2.from, m1.to < m2.to        -> m1
        #   c) m1.from < m2.from, m1.to ? m2.to        -> m1
        #   d) m1.from ? m2.from, m1.to ? m2.to        -> None
        #   e) m1.from ? m2.from, m1.to = m2.to        -> None
        #   f) m1.from = m2.from, m1.to ? m2.to        -> None

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
        return 'Mm(%s, %s)' % (self.from_any, self.to)

    def __hash__(self):
        return (self.from_any, self.to).__hash__()
Mm = Metamorphosis


class Specialization(object):
    
    def __init__(self, base, feature):
        self.base = base
        self.feature = feature

    @staticmethod
    def issubclass(c1, c2):
        c1_is_spz, c2_is_spz = isinstance(c1, Spz), isinstance(c2, Spz)
        if c1_is_spz and c2_is_spz:
            return Spz.issubclass(c1.base, c2.base) and Spz.issubclass(c1.feature, c2.feature)
        elif c1_is_spz:
            return issubclass(c1.base, c2)
        elif c2_is_spz:
            return False
        else:
            return issubclass(c1, c2)

    def __repr__(self):
        return 'Spz(%s, %s)' % (self.base, self.feature)

    def __eq__(self, other):
        return Spz.issubclass(self, other) and Spz.issubclass(other, self) 
Spz = Specialization


def closest_parent(klass, other_classes):
    """
    Returns:
        The closer parent of *klass* picked from the list *other_classes*. If no parent was found in *other_classes*, returns *object*.
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
