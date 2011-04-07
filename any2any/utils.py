"""
"""

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

    def __init__(self, from_any, to):
        self.from_any = from_any
        self.to = to

    def pick_closest_in(self, choice_list):
        """
        .. todo:: if triangle, then random choice will be picked ...
        """
        candidates = filter(self.included_in, choice_list)
        if not candidates:
            raise ValueError('No suitable metamorphosis found') #TODO : good message in there
        else:
            return sorted(candidates)[0]

    def included_in(self, other):
        """
        Return:
            bool. True if calling metamorphosis is a super-metamorphosis of *other*.
        """
        return issubclass(self.from_any, other.from_any) and issubclass(other.to, self.to)

    @staticmethod
    def most_precise(m1, m2):
        """
        Returns:
            Metamorphosis. The most precise metamorphose between m1 and m2
        """
        # There are 7 cases (excluding symetric cases):
        # A) m1 = m2                                        -> None
        #
        # B) m1 C m2
        #   m1.from_any < m2.from_any, m2.to < m1.to        -> m1
        #   m1.from_any = m2.from_any, m2.to < m1.to        -> m1
        #   m1.from_any < m2.from_any, m2.to = m1.to        -> m1
        #
        # C) m1 & m2 = {}
        #   m1.from_any > m2.from_any, m2.to < m1.to        -> m1
        #   m1.from_any = m2.from_any, m2.to < m1.to        -> m1
        #   m1.from_any < m2.from_any, m2.to = m1.to        -> m1
        if m1 == m2:# A)
            return None
        elif m1.included_in(m2):# B)
            return m1
        elif m2.included_in(m1):
            return m2
        else:# C)
            if m1.to != m2.to:
                # more general is best
                if issubclass(m1.to, m2.to):
                    return m2
                else:
                    return m1
            else:
                # more precise is best
                if issubclass(m1.from_any, m2.from_any):
                    return m1
                else:
                    return m2

    def __lt__(self, other):
        return self.most_precise(self, other) == self

    def __gt__(self, other):
        return self.most_precise(self, other) == other

    def __eq__(self, other):
        return self.from_any == other.from_any and self.to == other.to

    def __repr__(self):
        return 'Mm(%s, %s)' % (self.from_any, self.to)

    def __hash__(self):
        return (self.from_any, self.to).__hash__()
Mm = Metamorphosis

def closest_parent(klass, other_classes):
    """
    Returns:
        The closer parent of *klass* picked from the list *other_classes*. If no parent was found in *other_classes*, returns *object*.
    """
    #We select only the super classes of *klass*
    candidates = []
    for oclass in other_classes:
        if issubclass(klass, oclass):
            candidates.append(oclass)

    #This is used to sort the list and take the closer parent of *klass*
    @total_ordering
    class K(object):
        def __init__(self, klass):
            self.klass = klass
        def __lt__(self, other):
            return issubclass(self.klass, other.klass)
        def __eq__(self, other):
            return self.klass == other.klass
    
    if not candidates:
        return object
    else:
        return sorted(candidates, key=K)[0]

class SpecMetaclass(type):
    def __repr__(cls):
        return '%s of %s' % (cls.base, cls.feature)
    def __eq__(cls, other):
        return isinstance(other, SpecMetaclass) and\
        other.feature == cls.feature and\
        other.base == cls.base

def specialize(klass, afeature): 
    class sclass(klass):
        __metaclass__ = SpecMetaclass
        feature = afeature
        base = klass
    return sclass

def copied_values(dict_iter):
    for name, value in dict_iter:
        try:
            yield name, copy.copy(value)
        except:
            yield name, value
    raise StopIteration
