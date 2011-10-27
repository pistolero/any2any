# -*- coding: utf-8 -*-


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

    def __init__(self, obj):
        self.obj = obj

    def __iter__(self):
        return self.iter()

    def get_actual_schema(self):
        schema = {}
        for k, v in iter(self):
            schema[k] = type(v)
        return schema

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
    def get_subclass(cls, **attrs):
        return type(cls.__name__, (cls,), attrs)

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


class ValueInfo(object):

    def __init__(self, klass, lookup_with=(), schema=None):
        self.klass = klass
        self.lookup_with = lookup_with
        self.schema = schema

    @property
    def bundle_class_dict(self):
        return {'klass': self.klass, 'schema': self.schema}

    def get_lookup_classes(self):
        return self.lookup_with or (self.klass,)
