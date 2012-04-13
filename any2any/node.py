# -*- coding: utf-8 -*-
from utils import ClassSetDict, AttrDict, AllSubSetsOf
from exceptions import NoSuitableNodeClass


class Node(object):
    """
    Base for all node classes.
    Subclasses must implement :

        - :meth:`dump`
        - :meth:`schema_dump`
        - :meth:`load`
        - :meth:`schema_load` 
    """

    klass = AttrDict.ValueUnknown
    """The class of the object this node contains."""

    def __init__(self, obj):
        self.obj = obj

    @classmethod
    def new(cls, obj):
        """
        This method is used internally instead of `__init__`, to build
        a new node instance.
        """
        return cls(obj)

    def dump(self):
        """
        Returns an iterator ``key, value`` on the serialized node.
        This iterator is intended to be used by the :meth:`load` method
        of another node class.
        """
        raise NotImplementedError()

    @classmethod
    def load(cls, items_iter):
        """
        Takes an iterator ``key, value`` as returned by the :meth:`dump` method
        of another node ; and returns a deserialized node instance.
        """
        raise NotImplementedError()

    @classmethod
    def schema_dump(cls):
        """
        Returns the schema - a priori - of the node, when serialized with :meth:`dump`.
        """
        raise NotImplementedError()

    @classmethod
    def schema_load(cls):
        """
        Returns the schema - a priori - accepted by the :meth:`load` method 
        of the node class.
        """
        raise NotImplementedError()

    @classmethod
    def get_subclass(cls, **attrs):
        """
        Allows inline subclassing of a node class. Example ::

            ListOfIntNode = IterableNode.get_subclass(klass=list, value_type=int)
        """
        return type(cls.__name__, (cls,), attrs)


class IdentityNode(Node):
    """
    A no-op node class defining :meth:`dump` and :meth:`load` as identity operations.
    """

    def dump(self):
        yield AttrDict.KeyFinal, self.obj

    @classmethod
    def load(cls, items_iter):
        try:
            key, obj = items_iter.next()
        except StopIteration:
            raise TypeError("empty iterator received")
        return cls.new(obj)

    @classmethod
    def schema_dump(cls):
        return {AttrDict.KeyFinal: cls.klass}

    @classmethod
    def schema_load(cls):
        return {AttrDict.KeyFinal: cls.klass}


class ContainerNode(Node):
    """
    Base class for container node classes.
    """

    value_type = AttrDict.ValueUnknown
    """Type of values in the container. This is used to generate schemas."""

    @classmethod
    def schema_dump(cls):
        return {AttrDict.KeyAny: cls.value_type}

    @classmethod
    def schema_load(cls):
        return {AttrDict.KeyAny: cls.value_type}


class IterableNode(ContainerNode):
    """
    Node class for iterables.
    """

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
    """
    Node class for mappings.
    """

    klass = dict

    def dump(self):
        return ((k, self.obj[k]) for k in self.obj)

    @classmethod
    def load(cls, items_iter):
        obj = cls.klass(items_iter)
        return cls.new(obj)


class ObjectNode(Node):
    """
    Node class for any object.
    Provides attribute accessors for the object :meth:`setattr` and :meth:`getattr`.
    """
    
    klass = object

    def dump(self):
        schema = AttrDict(self.schema_dump())
        for name in schema.iter_attrs():
            yield name, self.getattr(name)

    @classmethod
    def load(cls, items_iter):
        obj = cls.klass(**dict(items_iter))
        return cls.new(obj)
    
    @classmethod
    def schema_dump(cls):
        return {}

    @classmethod
    def schema_load(cls):
        return {}

    def setattr(self, name, value):
        """
        Sets the attribute `name` of the node's object, with `value`.
        If the calling node has a method `set_<name>`, this method will be used instead.
        """
        if hasattr(self, 'set_%s' % name):
            getattr(self, 'set_%s' % name)(value)
        else:
            self.default_setattr(name, value)

    def getattr(self, name):
        """
        Gets the attribute `name` from the node's object.
        If the calling node has a method `get_<name>`, this method will be used instead.
        """
        if hasattr(self, 'get_%s' % name):
            return getattr(self, 'get_%s' % name)()
        else:
            return self.default_getattr(name)

    def default_getattr(self, name):
        return getattr(self.obj, name)

    def default_setattr(self, name, value):
        setattr(self.obj, name, value)


class NodeInfo(object):

    def __init__(self, wished, **kwargs):
        # Those will be used for building the final node class        
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
                raise NoSuitableNodeClass(klass)
            attrs['klass'] = klass
        else:
            node_class = self._raw_node_class

        attrs.update(self.kwargs)
        return node_class.get_subclass(**attrs)

