# -*- coding: utf-8 -*-
from utils import ClassSetDict, SmartDict, AllSubSetsOf


class FactoryError(TypeError): pass


class Node(object):
    """
    Base class for all node classes. 
    """

    klass = SmartDict.ValueUnknown

    def __init__(self, obj):
        self.obj = obj

    @classmethod
    def new(cls, obj):
        return cls(obj)

    def dump(self):
        raise NotImplementedError()

    @classmethod
    def schema_dump(cls):
        raise NotImplementedError()

    @classmethod
    def load(cls, items_iter):
        raise NotImplementedError()

    @classmethod
    def schema_load(cls):
        raise NotImplementedError()

    @classmethod
    def get_subclass(cls, **attrs):
        return type(cls.__name__, (cls,), attrs)

    def get_actual_schema(self):
        schema = {}
        for k, v in self.dump():
            schema[k] = type(v)
        return schema


class IdentityNode(Node):

    def dump(self):
        yield SmartDict.KeyFinal, self.obj

    @classmethod
    def schema_dump(cls):
        return {SmartDict.KeyFinal: cls.klass}

    @classmethod
    def load(cls, items_iter):
        try:
            key, obj = items_iter.next()
        except StopIteration:
            raise FactoryError("empty iterator received")
        return cls.new(obj)

    @classmethod
    def schema_load(cls):
        return {SmartDict.KeyFinal: cls.klass}


class ContainerNode(Node):

    value_type = SmartDict.ValueUnknown

    @classmethod
    def schema_dump(cls):
        return {SmartDict.KeyAny: cls.value_type}

    @classmethod
    def schema_load(cls):
        return {SmartDict.KeyAny: cls.value_type}


class IterableNode(ContainerNode):

    klass = list

    def dump(self):
        return enumerate(self.obj)

    @classmethod
    def load(cls, items_iter):
        # TODO: needs ordered dict to pass data between nodes
        items_iter = sorted(items_iter, key=lambda i: i[0])
        obj = cls.klass((v for k, v in items_iter))
        return cls.new(obj)


class MappingNode(ContainerNode):
    
    klass = dict

    def dump(self):
        return ((k, self.obj[k]) for k in self.obj)

    @classmethod
    def load(cls, items_iter):
        obj = cls.klass(items_iter)
        return cls.new(obj)


class ObjectNode(Node):
    """
    A subclass of `WrappedObject` can also provide informations on the wrapped type's instances' :

        - attribute access - :meth:`setattr` and :meth:`getattr`
        - creation of new instances - :meth:`new`
    """
    
    klass = object

    def dump(self):
        for name in self.schema_dump():
            yield name, self.getattr(name)
    
    @classmethod
    def schema_dump(cls):
        return {}

    @classmethod
    def load(cls, items_iter):
        """
        Creates and returns a new instance of the wrapped type.
        """
        obj = cls.klass(**dict(items_iter))
        return cls.new(obj)

    @classmethod
    def schema_load(cls):
        return {}

    def setattr(self, name, value):
        """
        Sets the attribute `name` on `instance`, with value `value`. If the calling :class:`WrappedObject` has a method `set_<name>`, this method will be used to set the attribute.
        """
        if hasattr(self, 'set_%s' % name):
            getattr(self, 'set_%s' % name)(value)
        else:
            self.default_setattr(name, value)

    def getattr(self, name):
        """
        Gets the attribute `name` from `instance`. If the calling :class:`WrappedObject` has a method `get_<name>`, this method will be used to get the attribute.
        """
        if hasattr(self, 'get_%s' % name):
            return getattr(self, 'get_%s' % name)()
        else:
            return self.default_getattr(name)

    def default_getattr(self, name):
        return getattr(self.obj, name)

    def default_setattr(self, name, value):
        setattr(self.obj, name, value)


class NoSuitableNodeClass(Exception): pass


class NodeInfo(object):

    def __init__(self, wished, **kwargs):
        # Those will be used for building the node class        
        self.kwargs = kwargs

        # Dealing with `wished`, which can be of many different types
        self._lookup_with = ClassSetDict()
        if isinstance(wished, (list, tuple)):
            for klass in wished:
                self._lookup_with[AllSubSetsOf(klass)] = klass
            # We use the last class of the list as a fallback
            if not AllSubSetsOf(object) in self._lookup_with:
                self._lookup_with[AllSubSetsOf(object)] = wished[-1]
        elif isinstance(wished, type) and issubclass(wished, Node):
            self._raw_node_class = wished
        elif isinstance(wished, type):
            self._lookup_with[AllSubSetsOf(object)] = wished
        else:
            raise ValueError("invalid wish %s" % wished)

    def get_node_class(self, inpt, node_class_map):
        if not isinstance(node_class_map, ClassSetDict):
            node_class_map = ClassSetDict(node_class_map)

        # attrs for customizing the node class
        attrs = {}

        if not hasattr(self, '_raw_node_class'):
            # Finding a node class : first we get the classes to lookup with
            # according to inpt's type, then try to find a node class for any
            # of those classes 
            klass = self._lookup_with.subsetget(type(inpt))
            node_class = node_class_map.subsetget(klass)
            if node_class is None:
                raise NoSuitableNodeClass()
            attrs['klass'] = klass
        else:
            node_class = self._raw_node_class

        attrs.update(self.kwargs)
        return node_class.get_subclass(**attrs)

