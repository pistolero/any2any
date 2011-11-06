# -*- coding: utf-8 -*-
from utils import ClassSet


class FactoryError(TypeError): pass


class Bundle(object):

    class KeyFinal(object): pass
    class KeyAny(object): pass
    class ValueUnknown(object): pass

    klass = ValueUnknown
    schema = {}
    """dict. ``{<attribute_name>: <attribute_type>}``. Allows to update the default schema, see :meth:`get_schema`."""

    include = []
    """list. The list of attributes to include in the schema see, :meth:`get_schema`."""

    exclude = []
    """list. The list of attributes to exclude from the schema see, :meth:`get_schema`."""

    access = {KeyAny: 'rw'}

    def __init__(self, obj):
        self.obj = obj

    def __iter__(self):
        for key, value in self.iter():
            if self.is_readable(key):
                yield key, value 

    @classmethod
    def build(cls, items_iter):
        def generator():
            for key, value in items_iter:
                if cls.is_writable(key):
                    yield key, value
        return cls.factory(generator())

    @classmethod
    def get_schema(cls):
        """
        Returns the full schema ``{<attribute_name>: <attribute_type>}`` of an instance, taking into account (respectively) : `default_schema`, `schema`, `include` and `exclude`.
        """
        schema = cls.default_schema()
        schema.update(cls.schema or {})
        if cls.include:
            [schema.setdefault(k, cls.ValueUnknown) for k in cls.include]
            [schema.pop(k) for k in schema.keys() if k not in cls.include]
        if cls.exclude:
            [schema.pop(k, None) for k in cls.exclude]
        for key, cls in schema.iteritems():
            schema[key] = cls
        return schema

    @classmethod
    def get_access(cls):
        access = cls.default_access()
        access.update(cls.access)
        return access

    @classmethod
    def get_subclass(cls, **attrs):
        return type(cls.__name__, (cls,), attrs)

    @classmethod
    def is_readable(cls, key):
        access = cls.get_access()
        if key in access:
            return 'r' in access[key]
        elif cls.KeyAny in access:
            return 'r' in access[cls.KeyAny]
        else:
            return False

    @classmethod
    def is_writable(cls, key):
        access = cls.get_access()
        if key in access:
            return 'w' in access[key]
        elif cls.KeyAny in access:
            return 'w' in access[cls.KeyAny]
        else:
            return False

    def get_actual_schema(self):
        schema = {}
        for k, v in iter(self):
            schema[k] = type(v)
        return schema

    @classmethod
    def default_access(cls):
        return {cls.KeyAny: 'rw'}

    @classmethod
    def default_schema(cls):
        raise NotImplementedError()

    def iter(self):
        # TODO: name unpack ?
        raise NotImplementedError()

    @classmethod
    def factory(cls, items_iter):
        # TODO: name pack ?
        raise NotImplementedError()


class IdentityBundle(Bundle):

    @classmethod
    def get_schema(cls):
        return {cls.KeyFinal: cls.klass}

    def iter(self):
        yield self.KeyFinal, self.obj

    @classmethod
    def factory(cls, items_iter):
        try:
            key, obj = items_iter.next()
        except StopIteration:
            raise FactoryError("empty iterator received")
        return cls(obj)


class ContainerBundle(Bundle):

    value_type = Bundle.ValueUnknown

    @classmethod
    def default_schema(cls):
        return {cls.KeyAny: cls.value_type}


class IterableBundle(ContainerBundle):

    klass = list

    def iter(self):
        return enumerate(self.obj)

    @classmethod
    def factory(cls, items_iter):
        # TODO: needs ordered dict to pass data between bundles
        items_iter = sorted(items_iter, key=lambda i: i[0])
        obj = cls.klass((v for k, v in items_iter))
        return cls(obj)


class MappingBundle(ContainerBundle):
    
    klass = dict

    def iter(self):
        return ((k, self.obj[k]) for k in self.obj)

    @classmethod
    def factory(cls, items_iter):
        obj = cls.klass(items_iter)
        return cls(obj)


class ObjectBundle(Bundle):
    """
    A subclass of `WrappedObject` can also provide informations on the wrapped type's instances' :

        - attribute schema - :meth:`default_schema`
        - attribute access - :meth:`setattr` and :meth:`getattr`
        - creation of new instances - :meth:`new`
    """
    
    klass = object

    def iter(self):
        for name in self.get_schema():
            if self.is_readable(name):
                yield name, self.getattr(name)
    
    @classmethod
    def factory(cls, items_iter):
        """
        Creates and returns a new instance of the wrapped type.
        """
        obj = cls.klass(**dict(items_iter))
        return cls(obj)

    @classmethod
    def default_schema(cls):
        """
        Returns the schema - known a priori - of an instance. Must return a dictionary with the format ``{<attribute_name>: <attribute_type>}``. 
        """
        return {}

    def setattr(self, name, value):
        """
        Sets the attribute `name` on `instance`, with value `value`. If the calling :class:`WrappedObject` has a method `set_<name>`, this method will be used to set the attribute.
        """
        if hasattr(self, 'set_%s' % name):
            getattr(self, 'set_%s' % name)(value)
        else:
            setattr(self.obj, name, value)

    def getattr(self, name):
        """
        Gets the attribute `name` from `instance`. If the calling :class:`WrappedObject` has a method `get_<name>`, this method will be used to get the attribute.
        """
        if hasattr(self, 'get_%s' % name):
            return getattr(self, 'get_%s' % name)()
        else:
            return getattr(self.obj, name)


class NoSuitableBundleClass(Exception): pass


class ValueInfo(object):

    def __new__(cls, val, *args, **kwargs):
        if cls._should_bypass(val):
            return val
        else:
            return super(ValueInfo, cls).__new__(cls, val, *args, **kwargs)

    def __init__(self, class_or_bundle_class, lookup_with=(), schema=None, access='rw'):
        if self._should_bypass(class_or_bundle_class):
            return
        elif issubclass(class_or_bundle_class, Bundle):
            self._raw_bundle_class = class_or_bundle_class
        else:
            self._klass = class_or_bundle_class
        self._schema = schema
        self._lookup_with = lookup_with
        if not (set(access) & set('rw')) == set(access):
            raise ValueError("'access' can contain only chars 'r' and 'w'")
        self.access = access
        self._bundle_class_map = {}

    @property
    def schema(self):
        return self.bundle_class.get_schema()

    @property
    def bundle_class(self):
        # Finding a bundle class, if we don't have one yet
        if not hasattr(self, '_bundle_class'):
            if not hasattr(self, '_raw_bundle_class'):
                exc = None
                for k in self.lookup_with:
                    try:
                        bundle_class = ClassSet.pick_best(
                            k, self.bundle_class_map,
                            exc_type=NoSuitableBundleClass
                        )
                    except NoSuitableBundleClass as exc:
                        pass
                    else:
                        exc = None
                        break
                if exc: raise exc
            else:
                bundle_class = self._raw_bundle_class
            # customizing the bundle class
            attrs = {}
            hasattr(self, '_klass') and attrs.update({'klass': self._klass})
            (self._schema is not None) and attrs.update({'schema': self._schema})
            self._bundle_class = bundle_class.get_subclass(**attrs)
        return self._bundle_class

    @property
    def bundle_class_map(self):
        return self._bundle_class_map

    @bundle_class_map.setter
    def bundle_class_map(self, new_map):
        if hasattr(self, '_bundle_class'):
            del self._bundle_class
        self._bundle_class_map = new_map

    @property
    def klass(self):
        if hasattr(self, '_klass'):
            return self._klass
        else:
            return self.bundle_class.klass

    @property
    def lookup_with(self):
        return self._lookup_with or (self.klass,)

    @staticmethod
    def _should_bypass(val):
        if val is Bundle.ValueUnknown:
            return True
        elif isinstance(val, ValueInfo):
            return True
        return False

