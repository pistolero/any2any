FROM = 0
TO = 1

def closest_conversion(converts, from_choices):
    """
    .. todo:: if triangle, then random choice will be picked ...
    """
    candidates = [choice for choice in from_choices if\
        issubclass(converts[FROM], choice[FROM]) and\
        issubclass(choice[TO], converts[TO])]

    #This is used to sort the list and take the closer parent of *klass*
    class K(object):
        def __init__(self, converts):
            self.converts = converts
        def __lt__(self, other):
            issub = issubclass(self.converts[FROM], other.converts[FROM])
            if issub and self.converts[FROM] != other.converts[FROM]:
                return True
            elif self.converts[FROM] == other.converts[FROM]:
                return issubclass(other.converts[TO], self.converts[TO])
            else:
                return False    
        def __gt__(self, other):
            return other < self
        def __eq__(self, other):
            return self.converts == other.converts
    
    if not candidates:
        raise ValueError('') #TODO : good message in there
    else:
        return sorted(candidates, key=K)[FROM]

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
    class K(object):
        def __init__(self, klass):
            self.klass = klass
        def __lt__(self, other):
            return issubclass(self.klass, other.klass)
        def __gt__(self, other):
            return issubclass(other.klass, self.klass)
        def __eq__(self, other):
            return self.klass == other.klass
    
    if not candidates:
        return object
    else:
        return sorted(candidates, key=K)[0]

def specialize(klass, afeature):
    class sclass(klass):
        feature = afeature
    return sclass
