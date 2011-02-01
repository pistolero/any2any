FROM = 0
TO = 1

def closest_conversion(conversion, from_choices):
    """
    .. todo:: if triangle, then random choice will be picked ...
    """
    candidates = [choice for choice in from_choices if\
        issubclass(conversion[FROM], choice[FROM]) and\
        issubclass(conversion[TO], choice[TO])]

    #This is used to sort the list and take the closer parent of *klass*
    class K(object):
        def __init__(self, conversion):
            self.conversion = conversion
        def __lt__(self, other):
            issub = issubclass(self.conversion[FROM], other.conversion[FROM])
            if issub and self.conversion[FROM] != other.conversion[FROM]:
                return True
            elif self.conversion[FROM] == other.conversion[FROM]:
                return issubclass(self.conversion[TO], other.conversion[TO])
            else:
                return False    
        def __gt__(self, other):
            return other < self
        def __eq__(self, other):
            return self.conversion == other.conversion
    
    if not candidates:
        raise ValueError('') #TODO : good message in there
    else:
        return sorted(candidates, key=K)[0]

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
