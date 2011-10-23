# -*- coding: utf-8 -*-
from utils import AllSubSetsOf, Singleton, ClassSet


class FactoryError(TypeError): pass


class Bundle(object):

    use_for = None

    class Final(object): pass

    def __init__(self, obj):
        self.obj = obj

    def __iter__(self):
        return self.iter()

    def iter(self):
        raise NotImplementedError()

    @classmethod
    def factory(cls, item_iter):
        raise NotImplementedError()

    @classmethod
    def get_class(self, key):
        raise NotImplementedError()


class IdentityBundle(Bundle):

    use_for = AllSubSetsOf(object)

    def iter(self):
        yield self.Final, self.obj

    @classmethod
    def factory(cls, item_iter):
        try:
            key, obj = item_iter.next()
        except StopIteration:
            raise FactoryError("empty iterator received")
        return cls(obj)

    @classmethod
    def get_class(self, key):
        return NotImplemented


class ContainerBundle(Bundle):

    value_type = object

    @classmethod
    def get_class(cls, key):
        return cls.value_type


class IterableBundle(ContainerBundle):

    klass = list
    use_for = AllSubSetsOf(list)

    def iter(self):
        return enumerate(self.obj)

    @classmethod
    def factory(cls, item_iter):
        obj = cls.klass((v for k, v in item_iter))
        return cls(obj)


class MappingBundle(ContainerBundle):
    
    klass = dict
    use_for = AllSubSetsOf(dict)

    def iter(self):
        return ((k, self.obj[k]) for k in self.obj)

    @classmethod
    def factory(cls, item_iter):
        obj = cls.klass(item_iter)
        return cls(obj)


class ObjectBundle(Bundle):
    """
    Subclass `WrappedObject` to create a placeholder containing extra-information on a type. e.g. :

        >>> class WrappedInt(WrappedObject):
        ...
        ...     klass = int
        ...     greater_than = 0
        ...

    A subclass of `WrappedObject` can also provide informations on the wrapped type's instances' :

        - attribute schema - :meth:`default_schema`
        - attribute access - :meth:`setattr` and :meth:`getattr`
        - creation of new instances - :meth:`new`
    """
    
    klass = object
    """type. The wrapped type."""

    extra_schema = {}
    """dict. ``{<attribute_name>: <attribute_type>}``. Allows to update the default schema, see :meth:`get_schema`."""

    include = []
    """list. The list of attributes to include in the schema see, :meth:`get_schema`."""

    exclude = []
    """list. The list of attributes to exclude from the schema see, :meth:`get_schema`."""

    def iter(self):
        for name in self.get_schema():
            yield name, self.getattr(name)

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
    def factory(cls, items_iter):
        """
        Creates and returns a new instance of the wrapped type.
        """
        return cls.klass(**items_iter)

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
