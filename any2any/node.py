# -*- coding: utf-8 -*-
from utils import ClassSetDict, AttrDict, AllSubSetsOf


class NodeInfo(object):
    """
    NodeInfo allows to specify a node class, without chosing it.

    Examples :

        >>> NodeInfo()

    Tells the cast that the node class is completely unknown.

        >>> NodeInfo(list, value_type=int)

    Tells the cast to pick a node class for type `list`, 
    set its ``value_type`` class attributes to ``value_type = int``.

        >>> NodeInfo([list, tuple], value_type=str)

    Tells the cast to pick a node class for `list` or `tuple`, depending
    on the input to be casted, and customize it as before.
    """

    def __init__(self, *class_info, **kwargs):
        if not len(class_info) <= 1:
            raise TypeError('%s() takes 0 or 1 argument (%s given)' % 
                (self.__class__.__name__, len(class_info)))
        elif len(class_info) == 1:
            self.class_info = class_info[0]
        else:
            self._raw_class_info = None

        # Those will be used for building the final node class        
        self.kwargs = kwargs

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self._raw_class_info or '')

    def __copy__(self):
        if self._raw_class_info is None:
            return NodeInfo(**self.kwargs)
        else:
            return NodeInfo(self._raw_class_info, **self.kwargs)

    def get_class(self, klass):
        """
        Chose a single class, given the input class of the casting.
        """
        return self._class_info.subsetget(klass)

    @property
    def class_info(self):
        """
        A :class:`ClassSetDict` if the NodeInfo contains class information, `None` otherwise.
        """
        return getattr(self, '_class_info', None)

    @class_info.setter
    def class_info(self, value):
        self._raw_class_info = value

        # Dealing with `class_info`, which can be of different types
        self._class_info = ClassSetDict()
        if isinstance(value, (list, tuple)):
            for klass in value:
                self._class_info[AllSubSetsOf(klass)] = klass
            # We use the last class of the list as a fallback
            if not AllSubSetsOf(object) in self._class_info:
                self._class_info[AllSubSetsOf(object)] = value[-1]
        else:
            self._class_info[AllSubSetsOf(object)] = value


class Node(object):
    """
    Base for all node classes.
    Subclasses must implement :

        - :meth:`dump`
        - :meth:`schema_dump`
        - :meth:`load`
        - :meth:`schema_load` 
    """

    klass = NodeInfo()
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

    value_type = NodeInfo()
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

