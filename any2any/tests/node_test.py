# -*- coding: utf-8 -*-
from unittest import TestCase
import copy

from any2any.node import *
from any2any.cast import *
from any2any.utils import AttrDict, ClassSet


class NodeImplement(Node):

    def __dump__(self):
        return iter()

    @classmethod
    def __load__(cls, items_iter):
        pass

    @classmethod
    def __dschema__(cls, obj):
        return {}

    @classmethod
    def __lschema__(cls):
        return {}

class BaseStrNode(NodeImplement): pass
class IntNode(NodeImplement): pass
class MyFloatNode(NodeImplement):
    klass = float


class NodeInfo_test(TestCase):

    def no_class_info_test(self):
        """
        Test creating a NodeInfo with no class info.
        """
        node_info = NodeInfo()
        self.assertIsNone(node_info.class_info)

    def class_info_class_test(self):
        """
        Test creating a NodeInfo with a single class as info.
        """
        node_info = NodeInfo(int)
        self.assertEqual(node_info.class_info, ClassSetDict({
            AllSubSetsOf(object): int,
        }))

    def class_info_class_list_test(self):
        """
        Test creating a NodeInfo with a list of classes as info.
        """
        node_info = NodeInfo(int, str, unicode)
        self.assertEqual(node_info.class_info, ClassSetDict({
            AllSubSetsOf(int): int,
            AllSubSetsOf(str): str,
            AllSubSetsOf(object): unicode,
        }))

    def copy_test(self):
        """
        test copying NodeInfo
        """
        node_info = NodeInfo(bla=90)
        node_info_copy = copy.copy(node_info)
        self.assertEqual(node_info.class_info, node_info_copy.class_info)
        self.assertEqual(node_info.kwargs, node_info_copy.kwargs)

        node_info = NodeInfo(blo=0, poi='yuyu')
        node_info_copy = copy.copy(node_info)
        self.assertEqual(node_info.class_info, node_info_copy.class_info)
        self.assertEqual(node_info.kwargs, node_info_copy.kwargs)

        node_info = NodeInfo(int, str)
        node_info_copy = copy.copy(node_info)
        self.assertEqual(node_info.class_info, node_info_copy.class_info)
        self.assertEqual(node_info.kwargs, node_info_copy.kwargs)


class Node_Test(TestCase):
    
    def setUp(self):
        class AnObject(object): pass
        self.AnObject = AnObject
        class SimpleNode(Node):
            @classmethod
            def __dschema__(cls, obj):
                return {}
            @classmethod
            def __lschema__(cls):
                return {}
        self.SimpleNode = SimpleNode

    def get_subclass_test(self):
        MyNode = Node.get_subclass(klass=int, bla=8)
        self.assertTrue(issubclass(MyNode, Node))
        self.assertFalse(issubclass(Node, MyNode))
        self.assertEqual(MyNode.klass, int)
        self.assertEqual(MyNode.bla, 8)
        

class IdentityNode_Test(TestCase):
    """
    Simple tests on IdentityNode
    """

    def dump_test(self):
        """
        Test IdentityNode.__dump__
        """
        self.assertEqual(list(IdentityNode.__dump__(1.89)), [(AttrDict.KeyFinal, 1.89)])

    def load_test(self):
        """
        Test IdentityNode.__load__
        """
        loaded_dict = IdentityNode.__load__({'whatever': 'hello'}.iteritems())
        self.assertEqual(loaded_dict, 'hello')
        self.assertRaises(TypeError, IdentityNode.__load__, {}.iteritems())

    def dschema_lschema_test(self):

        class MyNode(IdentityNode):
            klass = int

        self.assertEqual(MyNode.__dschema__(None), {AttrDict.KeyFinal: int})
        self.assertEqual(MyNode.__lschema__(), {AttrDict.KeyFinal: int})
        

class IterableNode_Test(TestCase):
    """
    Simple tests on IterableNode
    """

    def dump_test(self):
        """
        Test IterableNode.__dump__
        """
        self.assertEqual(
            list(IterableNode.__dump__(['a', 'b', 'c'])),
            [(0, 'a'), (1, 'b'), (2, 'c')]
        )
        self.assertEqual(list(IterableNode.__dump__(('a',))), [(0, 'a')])
        self.assertEqual(list(IterableNode.__dump__([])), [])

    def load_test(self):
        """
        Test IterableNode.__load__
        """
        loaded_list = IterableNode.__load__({0: 'aaa', 1: 'bbb', 2: 'ccc'}.iteritems())
        self.assertEqual(loaded_list, ['aaa', 'bbb', 'ccc'])
        loaded_list = IterableNode.__load__({}.iteritems())
        self.assertEqual(loaded_list, [])

    def dschema_lschema_test(self):

        class ListOfInt(IterableNode):
            value_type = int

        self.assertEqual(ListOfInt.__dschema__(None), {AttrDict.KeyAny: int})
        self.assertEqual(ListOfInt.__lschema__(), {AttrDict.KeyAny: int})


class MappingNode_Test(TestCase):
    """
    Simple tests on MappingNode
    """

    def dump_test(self):
        """
        Test MappingNode.__dump__
        """
        self.assertItemsEqual(
            MappingNode.__dump__({"a": "aaa", "b": 2, "cc": 3}),
            [("a", "aaa"), ("b", 2), ("cc", 3)]
        )
        self.assertEqual(list(MappingNode.__dump__({})), [])

    def load_test(self):
        """
        Test MappingNode.__load__
        """
        loaded_dict = MappingNode.__load__({'a': 'aaa', 1: 'bbb', 'c': 'ccc'}.iteritems())
        self.assertEqual(loaded_dict, {'a': 'aaa', 1: 'bbb', 'c': 'ccc'})
        loaded_dict = MappingNode.__load__({}.iteritems())
        self.assertEqual(loaded_dict, {})

    def load_dump_schema_test(self):

        class MappingOfInt(MappingNode):
            value_type = int

        self.assertEqual(MappingOfInt.__dschema__(None), {AttrDict.KeyAny: int})
        self.assertEqual(MappingOfInt.__dschema__(None), {AttrDict.KeyAny: int})

