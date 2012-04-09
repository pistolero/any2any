# -*- coding: utf-8 -*-
from nose.tools import assert_raises, ok_
from unittest import TestCase

from any2any.node import *
from any2any.cast import *
from any2any.utils import SmartDict


class NodeImplement(Node):

    def dump(self):
        return iter()

    @classmethod
    def schema_dump(cls):
        return {}

    @classmethod
    def load(cls, items_iter):
        pass

    @classmethod
    def schema_load(cls):
        return {}

class BaseStrNode(NodeImplement): pass
class IntNode(NodeImplement): pass
class MyFloatNode(NodeImplement):
    klass = float


class NodeInfo_test(TestCase):

    def get_node_class_test(self):
        """
        test NodeInfo.get_node_class
        """
        bcm = {
            AllSubSetsOf(basestring): BaseStrNode,
            AllSubSetsOf(list): IdentityNode,
            Singleton(int): IntNode,
        }
        # With a node class
        value_info = NodeInfo(BaseStrNode)
        bc = value_info.get_node_class(1, bcm)
        ok_(issubclass(bc, BaseStrNode))

        # with a normal class
        value_info = NodeInfo(int)
        bc = value_info.get_node_class(1, bcm)
        ok_(issubclass(bc, IntNode))
        ok_(bc.klass is int)
        value_info = NodeInfo(str, schema={'a': str})
        bc = value_info.get_node_class(1, bcm)
        ok_(issubclass(bc, BaseStrNode))
        ok_(bc.klass is str)
        ok_(bc.schema == {'a': str})

        # with a list
        value_info = NodeInfo([float, basestring, list])
        bc = value_info.get_node_class('bla', bcm)
        ok_(issubclass(bc, BaseStrNode))
        ok_(bc.klass is basestring)
        bc = value_info.get_node_class(1, bcm)
        ok_(issubclass(bc, IdentityNode))
        ok_(bc.klass is list)


class Node_Test(TestCase):
    """
    Tests on Node
    """
    
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
        ok_(issubclass(MyNode, Node))
        ok_(not issubclass(Node, MyNode))
        ok_(MyNode.klass == int)
        ok_(MyNode.bla == 8)

    def get_actual_schema_test(self):
        """
        test Node.get_actual_schema
        """
        schema = MappingNode({'a': 1, 'b': 'b'}).get_actual_schema()
        ok_(schema == {'a': int, 'b': str})
        schema = IterableNode([1, 'b', 2.0]).get_actual_schema()
        ok_(schema == {0: int, 1: str, 2: float})
        

class IdentityNode_Test(TestCase):
    """
    Simple tests on IdentityNode
    """

    def dump_test(self):
        """
        Test IdentityNode.dump
        """
        node = IdentityNode(1.89)
        ok_(list(node.dump()) == [(SmartDict.KeyFinal, 1.89)])

    def load_test(self):
        """
        Test IdentityNode.load
        """
        node = IdentityNode.load({'whatever': 'hello'}.iteritems())
        ok_(node.obj == 'hello')
        assert_raises(FactoryError, IdentityNode.load, {}.iteritems())

    def schema_dump_load_test(self):

        class MyNode(IdentityNode):
            klass = int

        ok_(MyNode.schema_dump() == {SmartDict.KeyFinal: int})
        ok_(MyNode.schema_load() == {SmartDict.KeyFinal: int})
        

class IterableNode_Test(TestCase):
    """
    Simple tests on IterableNode
    """

    def dump_test(self):
        """
        Test IterableNode.dump
        """
        node = IterableNode(['a', 'b', 'c'])
        ok_(list(node.dump()) == [(0, 'a'), (1, 'b'), (2, 'c')])
        node = IterableNode(('a',))
        ok_(list(node.dump()) == [(0, 'a')])
        node = IterableNode([])
        ok_(list(node.dump()) == [])

    def load_test(self):
        """
        Test IterableNode.load
        """
        node = IterableNode.load({0: 'aaa', 1: 'bbb', 2: 'ccc'}.iteritems())
        ok_(node.obj == ['aaa', 'bbb', 'ccc'])
        node = IterableNode.load({}.iteritems())
        ok_(node.obj == [])

    def schema_dump_load_test(self):

        class ListOfInt(IterableNode):
            value_type = int

        ok_(ListOfInt.schema_dump() == {SmartDict.KeyAny: int})
        ok_(ListOfInt.schema_load() == {SmartDict.KeyAny: int})


class MappingNode_Test(TestCase):
    """
    Simple tests on MappingNode
    """

    def dump_test(self):
        """
        Test MappingNode.dump
        """
        node = MappingNode({"a": "aaa", "b": 2, "cc": 3})
        ok_(set(node.dump()) == set([("a", "aaa"), ("b", 2), ("cc", 3)]))
        node = MappingNode({})
        ok_(list(node.dump()) == [])

    def load_test(self):
        """
        Test MappingNode.load
        """
        node = MappingNode.load({'a': 'aaa', 1: 'bbb', 'c': 'ccc'}.iteritems())
        ok_(node.obj == {'a': 'aaa', 1: 'bbb', 'c': 'ccc'})
        node = MappingNode.load({}.iteritems())
        ok_(node.obj == {})

    def load_dump_schema_test(self):

        class MappingOfInt(MappingNode):
            value_type = int

        ok_(MappingOfInt.schema_dump() == {SmartDict.KeyAny: int})
        ok_(MappingOfInt.schema_dump() == {SmartDict.KeyAny: int})


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
        ok_(node.getattr('a') == 'blabla')
        ok_(node.getattr('b') == 'bloblo')
                
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
        ok_(obj.a == 'bloblo')
        ok_(obj.b == 'blabla')
