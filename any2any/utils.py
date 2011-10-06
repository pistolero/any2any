# -*- coding: utf-8 -*-
# TODO: cleaning, clarifying and refactoring
import copy
import collections
try:
    import abc
except ImportError:
    from compat import abc

class ClassSet(object):

    def __init__(self, klass):
        self.klass = klass

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        other = self.default_to_singleton(other)
        return not self == other and other < self

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def default_to_singleton(self, klass):
        if not isinstance(klass, ClassSet):
            return Singleton(klass)
        else:
            return klass

class AllSubSetsOf(ClassSet):

    def __eq__(self, other):
        if isinstance(other, AllSubSetsOf):
            return self.klass == other.klass
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, AllSubSetsOf):
            return Wrap.issubclass(self.klass, other.klass) and not other == self
        else:
            return False

    def __repr__(self):
        return u"Any '%s'" % self.klass.__name__

class Singleton(ClassSet):

    def __eq__(self, other):
        other = self.default_to_singleton(other)
        return self.klass == other.klass

    def __lt__(self, other):
        if isinstance(other, AllSubSetsOf):
            return Wrap.issubclass(self.klass, other.klass)
        else:
            return False

    def __repr__(self):
        return u"'%s'" % self.klass.__name__

class Metamorphosis(object):
    """
    A metamorphosis between two types :

        >>> mm = Metamorphosis(Mammal, Human)

    This represents the metamorphosis from a Mammal to a Human.

    Kwargs:
        from_(type). Metamorphosis only from type `from_` (and no subclass).
        to(type). Metamorphosis only to type `to` (and no subclass).
        from_any(type). Metamorphosis from type `from_any` and subclasses.
        to_any(type). Metamorphosis from type `to_any` and subclasses.
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
        self._to_set = Singleton(to) if to else AllSubSetsOf(to_any)
        self._from_set = Singleton(from_) if from_ else AllSubSetsOf(from_any)
        # Keeping the arguments at hand
        self.from_any = from_any
        self.from_ = from_
        self.to_any = to_any
        self.to = to

    def super_mms(self, mms):
        """
        Given a list of metamorphoses `mms`, returns the super-metamorphoses (i.e. "superset")
        of the calling instance, and filters out the possible duplicates and supersets of supersets. 
        """
        super_mms = set(filter(self.included_in, mms))
        for m1 in super_mms.copy():
            for m2 in super_mms.copy():
                if m1.included_in(m2) and not m1 is m2:
                    super_mms.discard(m2)
        return list(super_mms)

    def included_in(self, other, strict=False):
        if strict and self != other:
            return False
        return self._from_set <= other._from_set and self._to_set <= other._to_set

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

class Wrap(object):
    """
    """
    #TODO: Wrap(atype) doesn't match to Mm(atype), but Mm(from_any=atype) -> change Wrap.__eq__

    defaults = {'factory': None}

    def __init__(self, *superclasses, **features):
        # handling superclasses
        if len(superclasses) == 0:
            raise TypeError("You must provide at least one superclass.")
        self.superclasses = superclasses
        if not 'factory' in features:
            features['factory'] = superclasses[0]
        # handling features
        self.features = features
        attrs = copy.copy(self.defaults)
        attrs.update(features)
        for name, value in attrs.items():
            if not name in self.defaults:
                raise TypeError("Unvalid feature '%s'" % name)
            setattr(self, name, value)

    @property
    def base(self):
        return self.superclasses[0]

    def __call__(self, *args, **kwargs):
        return self.factory(*args, **kwargs)

    def __repr__(self):
        return 'Wrapped%s' % self.base.__name__.capitalize()

    def __getattr__(self, name):
        try:
            return getattr(self.base, name)
        except AttributeError:
            return self.__getattribute__(name)

    def __eq__(self, other):
        if isinstance(other, Wrap):
            return (self.superclasses == other.superclasses 
            and self.features == other.features)
        else:
            return False

    def __superclasshook__(self, C):
        if isinstance(C, Wrap): C = C.base
        # `C` is superclass of `self`,
        # if `C` is superclass of one of `self.superclasses` 
        for parent in self.superclasses:
            if Wrap.issubclass(parent, C):
                return True
        return False

    @staticmethod
    def issubclass(c1, c2s):
        if not isinstance(c2s, tuple): c2s = (c2s,)
        # If `c1` is `Wrap`, we use its `__superclasshook__`
        if isinstance(c1, Wrap):
            for c2 in c2s:
                if c1.__superclasshook__(c2):
                    return True
        else:
            for c2 in c2s:
                # `Wrap` cannot be a superclass of a normal class
                if isinstance(c2, Wrap):
                    return False
                elif issubclass(c1, c2):
                    return True
        return False

def closest_parent(klass, other_classes):
    """
    Returns:
        The closest parent of `klass` picked from the list `other_classes`. If no parent was found in `other_classes`, returns `object`.
    """
    #We select only the super classes of `klass`
    candidates = []
    for oclass in other_classes:
        if Wrap.issubclass(klass, oclass):
            candidates.append(oclass)

    #This is used to sort the list and take the closer parent of `klass`
    class K(object):
        def __init__(self, klass):
            self.klass = klass
        def __lt__(self, other):
            return Wrap.issubclass(self.klass, other.klass)
        def __eq__(self, other):
            return self.klass == other.klass
        def __gt__(self, other):
            return Wrap.issubclass(other.klass, klass.klass)
    
    if not candidates:
        return object
    else:
        return sorted(candidates, key=K)[0]

class memoize(object):
    """
    Decorator for memoizing a method return value.

    Kwargs:
        key(function). A function ``key_func(args, kwargs)`` generating a caching key for the ``*args, **kwargs`` the decorated function is called with.
    """
    #TODO: make memoize suitable for settings
    def __init__(self, key=None):
        self.key = key

    def __call__(self, method):
        # Creates a decorator that memoizes result of the decorated function   
        def _decorated_method(cast, *args, **kwargs):
            cache = self.get_cache(cast, method)
            key = self.generate_key(args, kwargs)
            if not key in cache:
                cache[key] = method(cast, *args, **kwargs)
            return cache[key]
        return _decorated_method

    def generate_key(self, args, kwargs):
        # Default generates a key with `args` and `kwargs`
        if self.key:
            return self.key(args, kwargs)
        else:
            return (tuple(args), tuple(sorted(kwargs.iteritems())))

    def get_cache(self, cast, method):
        # Gets and returns from `cast` the dict containing cache for `method`
        return cast._cache.setdefault(method, {})

class Iter(object):
    """
    Simple wrapper around the function :func:`iter` in order to make instantiable. 
    """

    def __init__(self, iterator):
        self.iterator = iterator

    def __iter__(self):
        return iter(self.iterator)
