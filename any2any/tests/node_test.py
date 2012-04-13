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

    def no_lookup_with_test(self):
        """
        Test creating a NodeInfo with no lookup.
        """
        node_info = NodeInfo()
        self.assertIsNone(node_info.lookup_with)

    def lookup_with_class_test(self):
        """
        Test creating a NodeInfo with a single class for lookup.
        """
        node_info = NodeInfo(int)
        self.assertEqual(node_info.lookup_with, ClassSetDict({
            AllSubSetsOf(object): int,
        }))

    def lookup_with_class_list_test(self):
        """
        Test creating a NodeInfo with a list of classes for lookup.
        """
        node_info = NodeInfo([int, str, unicode])
        self.assertEqual(node_info.lookup_with, ClassSetDict({
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
        self.assertEqual(node_info.lookup_with, node_info_copy.lookup_with)
        self.assertEqual(node_info.kwargs, node_info_copy.kwargs)

        node_info = NodeInfo(blo=0, poi='yuyu')
        node_info_copy = copy.copy(node_info)
        self.assertEqual(node_info.lookup_with, node_info_copy.lookup_with)
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
        node = IdentityNode(1.89)
        self.assertEqual(list(node.dump()), [(AttrDict.KeyFinal, 1.89)])

    def load_test(self):
        """
        Test IdentityNode.load
        """
        node = IdentityNode.load({'whatever': 'hello'}.iteritems())
        self.assertEqual(node.obj, 'hello')
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
        node = IterableNode(['a', 'b', 'c'])
        self.assertEqual(list(node.dump()), [(0, 'a'), (1, 'b'), (2, 'c')])
        node = IterableNode(('a',))
        self.assertEqual(list(node.dump()), [(0, 'a')])
        node = IterableNode([])
        self.assertEqual(list(node.dump()), [])

    def load_test(self):
        """
        Test IterableNode.load
        """
        node = IterableNode.load({0: 'aaa', 1: 'bbb', 2: 'ccc'}.iteritems())
        self.assertEqual(node.obj, ['aaa', 'bbb', 'ccc'])
        node = IterableNode.load({}.iteritems())
        self.assertEqual(node.obj, [])

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
        node = MappingNode({"a": "aaa", "b": 2, "cc": 3})
        self.assertItemsEqual(node.dump(), [("a", "aaa"), ("b", 2), ("cc", 3)])
        node = MappingNode({})
        self.assertEqual(list(node.dump()), [])

    def load_test(self):
        """
        Test MappingNode.load
        """
        node = MappingNode.load({'a': 'aaa', 1: 'bbb', 'c': 'ccc'}.iteritems())
        self.assertEqual(node.obj, {'a': 'aaa', 1: 'bbb', 'c': 'ccc'})
        node = MappingNode.load({}.iteritems())
        self.assertEqual(node.obj, {})

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
        class AnObjectNode(ObjectNode):
            klass = self.AnObject
            def get_a(self):
                return 'blabla'
        obj = self.AnObject()
        obj.b = 'bloblo'
        node = AnObjectNode(obj)
        self.assertEqual(node.getattr('a'), 'blabla')
        self.assertEqual(node.getattr('b'), 'bloblo')
                
    def setattr_test(self):
        """
        Test ObjectNode.setattr
        """
        class AnObjectNode(ObjectNode):
            klass = self.AnObject
            def set_a(self, value):
                self.obj.a = 'bloblo'
        obj = self.AnObject()
        node = AnObjectNode(obj)
        node.setattr('a', 'blibli')
        node.setattr('b', 'blabla')
        self.assertEqual(obj.a, 'bloblo')
        self.assertEqual(obj.b, 'blabla')
