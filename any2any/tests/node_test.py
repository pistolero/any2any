# -*- coding: utf-8 -*-
from unittest import TestCase
import copy

from any2any.node import *
from any2any.cast import *
from any2any.utils import AttrDict, ClassSet


class NodeImplement(Node):

    def dump(self):
        return iter()

    @classmethod
    def load(cls, items_iter):
        pass

    @classmethod
    def schema_dump(cls):
        return {}

    @classmethod
    def schema_load(cls):
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
            AllSubSetsOf(int): int,
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
            AllSubSetsOf(unicode): unicode,
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
            def schema_dump(cls):
                return {}
            @classmethod
            def schema_load(cls):
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
        Test IdentityNode.dump
        """
        self.assertEqual(list(IdentityNode.dump(1.89)), [(AttrDict.KeyFinal, 1.89)])

    def load_test(self):
        """
        Test IdentityNode.load
        """
        loaded_dict = IdentityNode.load({'whatever': 'hello'}.iteritems())
        self.assertEqual(loaded_dict, 'hello')
        self.assertRaises(TypeError, IdentityNode.load, {}.iteritems())

    def schema_dump_load_test(self):

        class MyNode(IdentityNode):
            klass = int

        self.assertEqual(MyNode.schema_dump(), {AttrDict.KeyFinal: int})
        self.assertEqual(MyNode.schema_load(), {AttrDict.KeyFinal: int})
        

class IterableNode_Test(TestCase):
    """
    Simple tests on IterableNode
    """

    def dump_test(self):
        """
        Test IterableNode.dump
        """
        self.assertEqual(
            list(IterableNode.dump(['a', 'b', 'c'])),
            [(0, 'a'), (1, 'b'), (2, 'c')]
        )
        self.assertEqual(list(IterableNode.dump(('a',))), [(0, 'a')])
        self.assertEqual(list(IterableNode.dump([])), [])

    def load_test(self):
        """
        Test IterableNode.load
        """
        loaded_list = IterableNode.load({0: 'aaa', 1: 'bbb', 2: 'ccc'}.iteritems())
        self.assertEqual(loaded_list, ['aaa', 'bbb', 'ccc'])
        loaded_list = IterableNode.load({}.iteritems())
        self.assertEqual(loaded_list, [])

    def schema_dump_load_test(self):

        class ListOfInt(IterableNode):
            value_type = int

        self.assertEqual(ListOfInt.schema_dump(), {AttrDict.KeyAny: int})
        self.assertEqual(ListOfInt.schema_load(), {AttrDict.KeyAny: int})


class MappingNode_Test(TestCase):
    """
    Simple tests on MappingNode
    """

    def dump_test(self):
        """
        Test MappingNode.dump
        """
        self.assertItemsEqual(
            MappingNode.dump({"a": "aaa", "b": 2, "cc": 3}),
            [("a", "aaa"), ("b", 2), ("cc", 3)]
        )
        self.assertEqual(list(MappingNode.dump({})), [])

    def load_test(self):
        """
        Test MappingNode.load
        """
        loaded_dict = MappingNode.load({'a': 'aaa', 1: 'bbb', 'c': 'ccc'}.iteritems())
        self.assertEqual(loaded_dict, {'a': 'aaa', 1: 'bbb', 'c': 'ccc'})
        loaded_dict = MappingNode.load({}.iteritems())
        self.assertEqual(loaded_dict, {})

    def load_dump_schema_test(self):

        class MappingOfInt(MappingNode):
            value_type = int

        self.assertEqual(MappingOfInt.schema_dump(), {AttrDict.KeyAny: int})
        self.assertEqual(MappingOfInt.schema_dump(), {AttrDict.KeyAny: int})


class ObjectNode_Test(TestCase):
    """
    Tests for the ObjectNode class
    """

    def setUp(self):
        class AnObject(object): pass
        self.AnObject = AnObject

    def getattr_test(self):
        """
        Test ObjectNode.getattr
        """
        class AnObjectNode(self.AnObject, ObjectNode):
            klass = self.AnObject
            def get_a(self):
                return 'blabla'

        obj = AnObjectNode()
        obj.b = 'bloblo'
        self.assertEqual(AnObjectNode.getattr(obj, 'a'), 'blabla')
        self.assertEqual(AnObjectNode.getattr(obj, 'b'), 'bloblo')
                
    def setattr_test(self):
        """
        Test ObjectNode.setattr
        """
        class AnObjectNode(self.AnObject, ObjectNode):
            klass = self.AnObject
            def set_a(self, value):
                self.a = 'bloblo'

        obj = AnObjectNode()
        AnObjectNode.setattr(obj, 'a', 'blibli')
        AnObjectNode.setattr(obj, 'b', 'blabla')
        self.assertEqual(obj.a, 'bloblo')
        self.assertEqual(obj.b, 'blabla')
