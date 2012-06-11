# -*- coding: utf-8 -*-
import unittest

from any2any.node import *
from any2any.exceptions import NoNodeClassError
from any2any.cast import *
from any2any.utils import *


class MyNode(Node): pass
class BaseStrNode(MyNode): pass
class IntNode(MyNode): pass
class MyFloatNode(MyNode):
    klass = float


class Cast_test(unittest.TestCase):

    def get_fallback_test_fallback_map(self):
        """
        Test _get_fallback, picking from the fallback map.
        """
        cast = Cast({AllSubSetsOf(object): IdentityNode}, {
            AllSubSetsOf(basestring): BaseStrNode,
            AllSubSetsOf(list): IdentityNode,
            ClassSet(int): IntNode,
        })
        class MyIntNode(IntNode):
            klass = int

        inpt = 123
        out_bc = cast._get_fallback(inpt, MyIntNode)
        self.assertTrue(issubclass(out_bc, IntNode))

    def get_fallback_test_default_node_class(self):
        """
        Test Cast._get_fallback, no fallback available, but dumper can be used as loader.
        """
        cast = Cast({AllSubSetsOf(object): IdentityNode}, {
            AllSubSetsOf(basestring): BaseStrNode,
            AllSubSetsOf(list): IdentityNode,
            ClassSet(int): IntNode,
        })
        class MyIntNode(IntNode):
            @classmethod
            def __dschema__(cls, obj):
                return {'haha': int}

        inpt = 123.123
        out_bc = cast._get_fallback(inpt, MyIntNode)
        self.assertTrue(out_bc.__dschema__(inpt) == {'haha': int})

    def resolve_node_class_simple_class_test(self):
        """
        Test _resolve_node_class with NodeInfo that has a simple class
        """
        cast = Cast({
            AllSubSetsOf(basestring): BaseStrNode,
            AllSubSetsOf(list): IdentityNode,
            ClassSet(int): IntNode,
        })
        node_info = NodeInfo(int)

        bc = cast._resolve_node_class(1, node_info, '__dump__')
        self.assertTrue(issubclass(bc, IntNode))
        self.assertTrue(bc.klass is int)
        node_info = NodeInfo(str, schema={'a': str})

        bc = cast._resolve_node_class(1, node_info, '__dump__')
        self.assertTrue(issubclass(bc, BaseStrNode))
        self.assertTrue(bc.klass is str)
        self.assertEqual(bc.schema, {'a': str})

    def resolve_node_class_class_list_test(self):
        """
        Test _resolve_node_class with NodeInfo that has a list of classes
        """
        cast = Cast({
            AllSubSetsOf(basestring): BaseStrNode,
            AllSubSetsOf(list): IdentityNode,
            ClassSet(int): IntNode,
        })
        node_info = NodeInfo(float, basestring, list)

        bc = cast._resolve_node_class('bla', node_info, '__dump__')
        self.assertTrue(issubclass(bc, BaseStrNode))
        self.assertTrue(bc.klass is basestring)

        bc = cast._resolve_node_class(1, node_info, '__dump__')
        self.assertTrue(issubclass(bc, IdentityNode))
        self.assertTrue(bc.klass is list)

        node_info = NodeInfo(float, MyNode)

        bc = cast._resolve_node_class('bla', node_info, '__dump__')
        self.assertTrue(issubclass(bc, MyNode))

    def resolve_node_class_fail_test(self):
        """
        Test _resolve_node_class with corresponding node class
        """
        cast = Cast({ClassSet(int): IntNode})
        node_info = NodeInfo(float)
        self.assertRaises(NoNodeClassError, cast._resolve_node_class, 'bla', node_info, '__dump__')

    def call_test(self):
        """
        test simple calls
        """
        cast = Cast({
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): IdentityNode,
        })
        self.assertEqual(cast({'a': 1, 'b': 2}, dumper=dict, loader=dict), {'a': 1, 'b': 2})
        self.assertEqual(cast({'a': 1, 'b': 2}, loader=list), [1, 2])
        self.assertEqual(cast(['a', 'b', 'c'], loader=dict), {0: 'a', 1: 'b', 2: 'c'})
        self.assertEqual(cast(['a', 'b', 'c'], loader=list), ['a', 'b', 'c'])
        self.assertEqual(cast(1, loader=int), 1)

    def call_inpt_with_dump_test(self):
        """
        Test call with an input that has itself a __dump__ method.
        """
        class MyDumper(object):
                
            @staticmethod
            def __dump__(obj):
                yield AttrDict.KeyFinal, str(obj)

        class MyObject(dict):

            def __dump__(self):
                for k, v in self.iteritems():
                    yield k, v
                yield '__count__', len(self)

            def __dschema__(self):
                return {'__count__': MyDumper, AttrDict.KeyAny: NodeInfo()}

        cast = Cast({
            AllSubSetsOf(object): IdentityNode,
            AllSubSetsOf(dict): MappingNode,
        }, {
            AllSubSetsOf(object): IdentityNode
        })
        inpt = MyObject({'a': 1, 'b': 2})
        self.assertEqual(cast(inpt, loader=dict), {'a': 1, 'b': 2, '__count__': '2'})
        
    def call_inpt_with_load_test(self):
        """
        Test call to a class that has itself a load method.
        """
        class MyDict(dict):
                
            def __load__(self, items_iter):
                for k, v in items_iter:
                    if k.startswith('key'):
                        self[k] = v
                return self

        my_dict = MyDict()
        cast = Cast({
            AllSubSetsOf(object): IdentityNode,
            AllSubSetsOf(dict): MappingNode,
        }, {
            AllSubSetsOf(object): IdentityNode
        })
        inpt = {'a': 1, 'b': 2, 'key_c': 3, 'key_d': 4}
        self.assertEqual(cast(inpt, loader=my_dict), {'key_c': 3, 'key_d': 4})

