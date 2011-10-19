# -*- coding: utf-8 -*-
import copy
import collections
import types
import functools
try:
    import abc
except ImportError:
    from compat import abc


def classproperty(func):
    class _classproperty(property):
        def __get__(self, cls, owner):
            return self.fget.__get__(None, owner)()
    return _classproperty(classmethod(func))


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
            return WrappedObject.issubclass(self.klass, other.klass) and not other == self
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
            return WrappedObject.issubclass(self.klass, other.klass)
        else:
            return False

    def __repr__(self):
        return u"'%s'" % self.klass.__name__


class Mm(object):
    """
    A metamorphosis between two types. For example :

        >>> mm1 = Mm(LoisClark, Superman)
        >>> mm2 = Mm(from_any=Human, to_any=SuperHero)
        >>> mm1 < mm2 # i.e. <mm1> is included in <mm2>
        True

    Kwargs:
        - from_(type). Metamorphosis only from type `from_` (and no subclass).
        - to(type). Metamorphosis only to type `to` (and no subclass).
        - from_any(type). Metamorphosis from type `from_any` and subclasses.
        - to_any(type). Metamorphosis from type `to_any` and subclasses.
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
        super_mms = set(filter(self.__le__, mms))
        for m1 in super_mms.copy():
            for m2 in super_mms.copy():
                if m1 <= m2 and not m1 is m2:
                    super_mms.discard(m2)
        return list(super_mms)

    def __lt__ (self, other):
        return self != other and self._from_set <= other._from_set and self._to_set <= other._to_set

    def __gt__ (self, other):
        return self != other and self._from_set >= other._from_set and self._to_set >= other._to_set

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def __eq__(self, other):
        if isinstance(other, Mm):
            return self._from_set == other._from_set and self._to_set == other._to_set
        else:
            return NotImplemented
 
    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return 'Mm(%s, %s)' % (self._from_set, self._to_set)

    def __hash__(self):
        return (self.from_, self.to, self.from_any, self.to_any).__hash__()


class WrappedObject(object):
    """
    Subclass `WrappedObject` to create a placeholder containing extra-information on a type. e.g. :

        >>> class WrappedInt(WrappedObject):
        ...
        ...     klass = int
        ...     greater_than = 0
        ...

    A subclass of `WrappedObject` can also providing informations on the wrapped type's instances' :

        - attribute schema - :meth:`default_schema`
        - attribute access - :meth:`setattr` and :meth:`getattr`
        - creation of new instances - :meth:`new`
    """
    #TODO: Wrap(atype) doesn't match to Mm(atype), but Mm(from_any=atype) -> change WrappedObject.__eq__ (or .issubclass ?)
    
    klass = object
    """type. The wrapped type."""

    factory = None
    """type. The type used for instance creation :

            >>> class WrappedBS(WrappedObject):
            ...     klass = basestring
            ...     factory = str
            ...
            >>> a_str = WrappedBS("blabla")
            >>> type(a_str) == str
            True
    """

    superclasses = ()
    """tuple. Allows to customize :meth:`WrappedObject.issubclass` behaviour :

            >>> class WrappedStr(WrappedObject):
            ...     klass=str
            ...     superclasses=(MyStr, AllStrings)
            ... 
            >>> WrappedObject.issubclass(WrappedStr, str), WrappedObject.issubclass(WrappedStr, MyStr), # ...
            (True, True)
    """

    extra_schema = {}
    """dict. ``{<attribute_name>: <attribute_type>}``. Allows to update the default schema, see :meth:`get_schema`."""

    include = []
    """list. The list of attributes to include in the schema see, :meth:`get_schema`."""

    exclude = []
    """list. The list of attributes to exclude from the schema see, :meth:`get_schema`."""

    def __new__(cls, *args, **kwargs):
        return cls.new(*args, **kwargs)

    @classmethod
    def get_superclasses(cls):
        return (cls.klass,) + tuple(cls.superclasses)

    @classmethod
    def __superclasshook__(cls, C):
        if issubclass(C, WrappedObject): C = C.klass
        # `C` is superclass of `cls`,
        # if `C` is superclass of one of `cls`'s superclasses.
        for parent in cls.get_superclasses():
            if WrappedObject.issubclass(parent, C):
                return True
        return False

    @staticmethod
    def issubclass(c1, c2s):
        if not isinstance(c2s, tuple): c2s = (c2s,)
        # If `c1` is a `WrappedObject`, we use its `__superclasshook__`
        if issubclass(c1, WrappedObject):
            for c2 in c2s:
                if c1.__superclasshook__(c2):
                    return True
        else:
            for c2 in c2s:
                # `WrappedObject` cannot be a superclass of a normal class
                if issubclass(c2, WrappedObject):
                    return False
                elif issubclass(c1, c2):
                    return True
        return False

    @classmethod
    def get_class(cls, key):
        """
        Returns the class of attribute `key`, as found from the schema, see :meth:`get_schema`.
        """
        schema = cls.get_schema()
        if key in schema:
            return schema[key]
        else:
            raise KeyError("'%s' not in schema" % key)
    
    @classmethod
    def get_schema(cls):
        """
        Returns the full schema ``{<attribute_name>: <attribute_type>}`` of an instance, taking into account (respectively) : `default_schema`, `extra_schema`, `include` and `exclude`.
        """
        schema = cls.default_schema()
        schema.update(cls.extra_schema)
        if cls.include:
            [schema.setdefault(k, NotImplemented) for k in cls.include]
            [schema.pop(k) for k in schema.keys() if k not in cls.include]
        if cls.exclude:
            [schema.pop(k, None) for k in cls.exclude]
        for key, cls in schema.iteritems():
            schema[key] = cls
        return schema

    @classmethod
    def default_schema(cls):
        """
        Returns the schema - known a priori - of an instance. Must return a dictionary with the format ``{<attribute_name>: <attribute_type>}``. 
        """
        return {}

    @classmethod
    def setattr(cls, instance, name, value):
        """
        Sets the attribute `name` on `instance`, with value `value`. If the calling :class:`WrappedObject` has a method `set_<name>`, this method will be used to set the attribute.
        """
        if hasattr(cls, 'set_%s' % name):
            getattr(cls, 'set_%s' % name)(instance, value)
        else:
            setattr(instance, name, value)

    @classmethod
    def getattr(cls, instance, name):
        """
        Gets the attribute `name` from `instance`. If the calling :class:`WrappedObject` has a method `get_<name>`, this method will be used to get the attribute.
        """
        if hasattr(cls, 'get_%s' % name):
            return getattr(cls, 'get_%s' % name)(instance)
        else:
            return getattr(instance, name)

    @classmethod
    def new(cls, *args, **kwargs):
        """
        Creates and returns a new instance of the wrapped type.
        """
        return (cls.factory or cls.klass)(*args, **kwargs)


def closest_parent(klass, other_classes):
    """
    Returns the closest parent of `klass` picked from the list `other_classes`. If no parent was found in `other_classes`, returns `object`.
    """
    #We select only the super classes of `klass`
    candidates = []
    for oclass in other_classes:
        if WrappedObject.issubclass(klass, oclass):
            candidates.append(oclass)

    #This is used to sort the list and take the closer parent of `klass`
    class K(object):
        def __init__(self, klass):
            self.klass = klass
        def __lt__(self, other):
            return WrappedObject.issubclass(self.klass, other.klass)
        def __eq__(self, other):
            return self.klass == other.klass
        def __gt__(self, other):
            return WrappedObject.issubclass(other.klass, klass.klass)
    
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
        @functools.wraps(method)
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
