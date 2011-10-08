# -*- coding: utf-8 -*-
import copy
import collections
import types
try:
    import abc
except ImportError:
    from compat import abc


class ClassSet(object):
    # Set of classes, allowing to easily calculate inclusions
    # with comparison operators : `a < B` <=> "A strictly included in B"

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

    Kwargs:
        from_(type). Metamorphosis only from type `from_` (and no subclass).
        to(type). Metamorphosis only to type `to` (and no subclass).
        from_any(type). Metamorphosis from type `from_any` and subclasses.
        to_any(type). Metamorphosis from type `to_any` and subclasses.
    """

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


class WrapMeta(type):
    # Just a metaclass for allowing inheritance of defaults

    def __new__(cls, name, bases, attrs):
        new_defaults = attrs.pop('defaults', None)
        new_wrap = super(WrapMeta, cls).__new__(cls, name, bases, attrs)
        if new_defaults:
            new_wrap.defaults = dict(getattr(new_wrap, 'defaults', {}), **new_defaults)
        return new_wrap


class Wrap(object):
    """
    Wrapper allowing to provide extra-information on a type.

    Kwargs:

        superclasses(tuple). Allows to customize :meth:`Wrap.issubclass` behaviour :

            >>> Wrapped = Wrap(str, superclasses=(MyStr, AllStrings))
            >>> Wrap.issubclass(Wrapped, str), Wrap.issubclass(Wrapped, MyStr), # ...
            (True, True)

        factory(type). The type used for instance creation :

            >>> Wrapped = Wrap(basestring, factory=str)
            >>> a_str = Wrapped("blabla")
            >>> type(a_str) == str
            True
    """
    #TODO: Wrap(atype) doesn't match to Mm(atype), but Mm(from_any=atype) -> change Wrap.__eq__

    __metaclass__ = WrapMeta

    defaults = {'factory': None, 'superclasses': ()}

    def __init__(self, klass, **features):
        features.setdefault('factory', klass)
        features['superclasses'] = (klass,) + tuple(features.get('superclasses', ())) 
        self.features = features
        self.klass = klass
        features = dict(copy.copy(self.defaults), **features)
        for name, value in features.items():
            if not name in self.defaults:
                raise TypeError("Unvalid feature '%s'" % name)
            setattr(self, name, value)

    def __call__(self, *args, **kwargs):
        return self.factory(*args, **kwargs)

    def __repr__(self):
        return 'Wrapped%s' % self.klass.__name__.capitalize()

    def __getattr__(self, name):
        try:
            return getattr(self.klass, name)
        except AttributeError:
            return self.__getattribute__(name)

    def __eq__(self, other):
        if isinstance(other, Wrap):
            return (self.klass == other.klass 
            and self.features == other.features)
        else:
            return False

    def __superclasshook__(self, C):
        if isinstance(C, Wrap): C = C.klass
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


def declarative_wrap_type(wrap_type):
    # slightly modifies a wrap type, so that it can be reused easily
    # with a declarative syntax.

    attrs = {}
    name = 'Declarative%s' % wrap_type.__name__
    bases = (wrap_type,)

    class Empty(object): pass


    def __new__(kls, name, bases, attrs):
        for b in bases:
            if hasattr(b, 'makes_sense'):
                import pdb; pdb.set_trace()
                attrs['blobloblo'] = 1234
        new_wrapped = super(kls, kls).__new__(kls, name, bases, attrs)
        for name, value in attrs.items():
            if isinstance(value, types.FunctionType):
                raise TypeError('You cannot declare instance methods here')
            elif isinstance(value, classmethod):
                # this is a ugly hack allowing to declare classmethods on the Wrapped. 
                def closure(class_meth):
                    def fake_class_method(*args, **kwargs):
                        return class_meth.__func__(new_wrapped, *args, **kwargs)
                    return fake_class_method
                setattr(new_wrapped, name, closure(value))
        return new_wrapped

    def __init__(self, name, bases, attrs):
        # collecting features and klass
        meta = attrs.get('Meta', Empty())
        features = dict(filter(lambda(k, v): not k.startswith('_'), meta.__dict__.items()))
        try:
            klass = features.pop('klass')
        except KeyError:
            raise TypeError("Meta must contain a 'klass' attribute")
        wrap_type.__init__(self, klass, **features)

    attrs['__init__'] = __init__
    attrs['__new__'] = __new__
    return type(name, bases, attrs)


class Wrapped(object):
    """
    Subclass this to create a wrapped type using a declarative syntax, e.g. :

        >>> class WrappedInt(Wrapped):
        ...
        ... class Meta:
        ...     klass = int
        ... 

    Which is equivalent to :

        >>> Wrap(int)
    """

    __metaclass__ = declarative_wrap_type(Wrap)

    class Meta:
        klass = object


def closest_parent(klass, other_classes):
    """
    Returns the closest parent of `klass` picked from the list `other_classes`. If no parent was found in `other_classes`, returns `object`.
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
