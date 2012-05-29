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

        >>> NodeInfo(list, tuple, value_type=str)

    Tells the cast to pick a node class for `list` or `tuple`, depending
    on the input to be casted, and customize it as before.

    If the input doesn't match any of the class provided, the last class
    of the list is taken as default.
    """

    def __init__(self, *class_info, **kwargs):
        if len(class_info) == 0:
            self._raw_class_info = None
        else:
            self.class_info = class_info

        # Those will be used for building the final node class        
        self.kwargs = kwargs

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self._raw_class_info or '')

    def __copy__(self):
        if self._raw_class_info is None:
            return NodeInfo(**self.kwargs)
        else:
            return NodeInfo(*self._raw_class_info, **self.kwargs)

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
    def class_info(self, class_list):
        self._raw_class_info = class_list
        # Dealing with `class_info`, which can be of different types
        self._class_info = ClassSetDict()
        for klass in class_list:
            self._class_info[AllSubSetsOf(klass)] = klass
        # We use the last class of the list as a fallback
        if not AllSubSetsOf(object) in self._class_info:
            self._class_info[AllSubSetsOf(object)] = class_list[-1]


class Node(object):
    """
    Base for all node classes.
    Subclasses must implement :

        - :meth:`dump`
        - :meth:`load`
        - :meth:`schema_dump`
        - :meth:`schema_load` 
    """

    klass = NodeInfo()
    """Informs on what class the node actually contains."""

    @classmethod
    def dump(cls, obj):
        """
        Returns an iterator ``key, value``, serialized version of `obj`.
        This iterator is intended to be used by the :meth:`load` method
        of another node class.
        """
        raise NotImplementedError()

    @classmethod
    def load(cls, items_iter):
        """
        Takes an iterator ``key, value`` as returned by the :meth:`dump` method
        of another node class ; and returns a deserialized object.
        """
        raise NotImplementedError()

    @classmethod
    def schema_dump(cls, obj):
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

    @classmethod
    def dump(cls, obj):
        yield AttrDict.KeyFinal, obj

    @classmethod
    def load(cls, items_iter):
        try:
            key, obj = items_iter.next()
        except StopIteration:
            raise TypeError("empty iterator received")
        return obj

    @classmethod
    def schema_dump(cls, obj):
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
    def schema_dump(cls, obj):
        return {AttrDict.KeyAny: cls.value_type}

    @classmethod
    def schema_load(cls):
        return {AttrDict.KeyAny: cls.value_type}


class IterableNode(ContainerNode):
    """
    Node class for iterables.
    """

    klass = list

    @classmethod
    def dump(cls, obj):
        return enumerate(obj)

    @classmethod
    def load(cls, items_iter):
        # TODO: needs ordered dict to pass data between nodes
        items_iter = sorted(items_iter, key=lambda i: i[0])
        return cls.klass((v for k, v in items_iter))


class MappingNode(ContainerNode):
    """
    Node class for mappings.
    """

    klass = dict

    @classmethod
    def dump(cls, obj):
        return ((k, obj[k]) for k in obj)

    @classmethod
    def load(cls, items_iter):
        return cls.klass(items_iter)

