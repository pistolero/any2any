# -*- coding: utf-8 -*-
from utils import ClassSet, ClassSetDict, SmartDict, AllSubSetsOf


class FactoryError(TypeError): pass


class Bundle(object):

    klass = SmartDict.ValueUnknown
    schema = {}
    """dict. ``{<attribute_name>: <attribute_type>}``. Allows to update the default schema, see :meth:`get_schema`."""

    include = []
    """list. The list of attributes to include in the schema see, :meth:`get_schema`."""

    exclude = []
    """list. The list of attributes to exclude from the schema see, :meth:`get_schema`."""

    access = {SmartDict.KeyAny: 'rw', SmartDict.KeyFinal: 'rw'}

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
            [schema.setdefault(k, SmartDict.ValueUnknown) for k in cls.include]
            [schema.pop(k) for k in schema.keys() if k not in cls.include]
        if cls.exclude:
            [schema.pop(k, None) for k in cls.exclude]
        for key, cls in schema.iteritems():
            schema[key] = cls
        return SmartDict(schema)

    @classmethod
    def get_access(cls):
        access = cls.default_access()
        access.update(cls.access)
        return SmartDict(access)

    @classmethod
    def get_subclass(cls, **attrs):
        return type(cls.__name__, (cls,), attrs)

    @classmethod
    def is_readable(cls, key):
        access = cls.get_access()
        try:
            return 'r' in access[key]
        except KeyError:
            return False

    @classmethod
    def is_writable(cls, key):
        access = cls.get_access()
        try:
            return 'w' in access[key]
        except KeyError:
            return False

    def get_actual_schema(self):
        schema = {}
        for k, v in iter(self):
            schema[k] = type(v)
        return SmartDict(schema)

    @classmethod
    def default_access(cls):
        return {SmartDict.KeyAny: 'rw'}

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
        return SmartDict({SmartDict.KeyFinal: cls.klass})

    def iter(self):
        yield SmartDict.KeyFinal, self.obj

    @classmethod
    def factory(cls, items_iter):
        try:
            key, obj = items_iter.next()
        except StopIteration:
            raise FactoryError("empty iterator received")
        return cls(obj)


class ContainerBundle(Bundle):

    value_type = SmartDict.ValueUnknown

    @classmethod
    def default_schema(cls):
        return {SmartDict.KeyAny: cls.value_type}


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


class BundleInfo(object):

    def __init__(self, wished, schema=None, access='rw'):
        # Dealing with various kwargs        
        self._schema = schema
        if not (set(access) & set('rw')) == set(access):
            raise ValueError("'access' can contain only chars 'r' and 'w'")
        self.access = access

        # Dealing with `wished`, which can be of many different types
        self._lookup_with = ClassSetDict()
        if isinstance(wished, (list, tuple)):
            for klass in wished:
                self._lookup_with[AllSubSetsOf(klass)] = klass
            # We use the last class of the list as a fallback
            if not AllSubSetsOf(object) in self._lookup_with:
                self._lookup_with[AllSubSetsOf(object)] = wished[-1]
        elif isinstance(wished, type) and issubclass(wished, Bundle):
            self._raw_bundle_class = wished
        elif isinstance(wished, type):
            self._lookup_with[AllSubSetsOf(object)] = wished
        else:
            raise ValueError("invalid wish %s" % wished)

    def get_bundle_class(self, inpt, bundle_class_map):
        if not isinstance(bundle_class_map, ClassSetDict):
            bundle_class_map = ClassSetDict(bundle_class_map)

        # attrs for customizing the bundle class
        attrs = {}

        if not hasattr(self, '_raw_bundle_class'):
            # Finding a bundle class : first we get the classes to lookup with
            # according to inpt's type, then try to find a bundle class for any
            # of those classes 
            klass = self._lookup_with.subsetget(type(inpt))
            bundle_class = bundle_class_map.subsetget(klass)
            if bundle_class is None:
                raise NoSuitableBundleClass()
            attrs['klass'] = klass
        else:
            bundle_class = self._raw_bundle_class

        if (self._schema is not None): attrs.update({'schema': self._schema})
        return bundle_class.get_subclass(**attrs)

