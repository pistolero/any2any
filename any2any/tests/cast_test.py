# -*- coding: utf-8 -*-
import unittest

from any2any.node import *
from any2any.cast import *
from any2any.utils import *


class MyNode(Node):

    @classmethod
    def schema_dump(cls):
        return {}

    @classmethod
    def schema_load(cls):
        return {}

class BaseStrNode(MyNode): pass
class IntNode(MyNode): pass
class MyFloatNode(MyNode):
    klass = float


class Cast_test(unittest.TestCase):

    def get_fallback_test_schema_KeyFinal(self):
        """
        Test _get_fallback, frm_node_class's schema containing KeyFinal 
        """
        cast = Cast({AllSubSetsOf(object): IdentityNode}, {
            AllSubSetsOf(basestring): BaseStrNode,
            AllSubSetsOf(list): IdentityNode,
            ClassSet(int): IntNode,
        })
        class MyIntNode(IntNode):
            @classmethod
            def schema_dump(cls):
                return {AttrDict.KeyFinal: int}

        out_bc = cast._get_fallback(MyIntNode)
        self.assertTrue(issubclass(out_bc, IntNode))

    def get_fallback_test_fallback_map(self):
        """
        Test _get_fallback, picking from the fallback map
        """
        cast = Cast({AllSubSetsOf(object): IdentityNode}, {
            AllSubSetsOf(basestring): BaseStrNode,
            AllSubSetsOf(list): IdentityNode,
            ClassSet(int): IntNode,
        })
        class MyIntNode(IntNode):
            klass = int

        out_bc = cast._get_fallback(MyIntNode)
        self.assertTrue(issubclass(out_bc, IntNode))

    def get_fallback_test_default_node_class(self):
        """
        Test Cast._get_fallback, picking the default node class
        """
        cast = Cast({AllSubSetsOf(object): IdentityNode}, {
            AllSubSetsOf(basestring): BaseStrNode,
            AllSubSetsOf(list): IdentityNode,
            ClassSet(int): IntNode,
        })
        class MyIntNode(IntNode):
            @classmethod
            def schema_dump(cls):
                return {'haha': int}

        out_bc = cast._get_fallback(MyIntNode)
        self.assertTrue(out_bc.schema_dump() == {'haha': int})

    def call_test(self):
        """
        test simple calls
        """
        cast = Cast({
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): IdentityNode,
        })
        self.assertEqual(cast({'a': 1, 'b': 2}, to=dict), {'a': 1, 'b': 2})
        self.assertEqual(cast({'a': 1, 'b': 2}, to=list), [1, 2])
        self.assertEqual(cast(['a', 'b', 'c'], to=dict), {0: 'a', 1: 'b', 2: 'c'})
        self.assertEqual(cast(['a', 'b', 'c'], to=list), ['a', 'b', 'c'])
        self.assertEqual(cast(1, to=int), 1)

    def improvise_schema_test(self):
        cast = Cast({})
        schema = cast._improvise_schema({'a': 1, 'b': 'b'}, MappingNode)
        self.assertEqual(schema, {'a': int, 'b': str})
        schema = cast._improvise_schema([1, 'b', 2.0], IterableNode)
        self.assertEqual(schema, {0: int, 1: str, 2: float})

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

        bc = cast._resolve_node_class(node_info, 1)
        self.assertTrue(issubclass(bc, IntNode))
        self.assertTrue(bc.klass is int)
        node_info = NodeInfo(str, schema={'a': str})

        bc = cast._resolve_node_class(node_info, 1)
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
        node_info = NodeInfo([float, basestring, list])

        bc = cast._resolve_node_class(node_info, 'bla')
        self.assertTrue(issubclass(bc, BaseStrNode))
        self.assertTrue(bc.klass is basestring)

        bc = cast._resolve_node_class(node_info, 1)
        self.assertTrue(issubclass(bc, IdentityNode))
        self.assertTrue(bc.klass is list)


class Cast_complex_calls_test(unittest.TestCase):

    def setUp(self):
        class Book(object):
            def __init__(self, title):
                self.title = title

        class Author(object):
            def __init__(self, name, books):
                self.name = name
                self.books = books

        class MyObjectNode(ObjectNode):
            @classmethod
            def schema_dump(cls):
                return cls.schema_common()
            @classmethod
            def schema_load(cls):
                return cls.schema_common()

        class BookNode(MyObjectNode):
            klass = Book
            @classmethod
            def schema_common(cls):
                return {'title': str,}

        class ListOfBooks(IterableNode):
            value_type = Book

        class ListOfBookNode(IterableNode):
            value_type = BookNode

        class SimpleAuthorNode(MyObjectNode):
            klass = Author
            @classmethod
            def schema_common(cls):
                return {
                    'name': str,
                    'books': list,
                }

        class HalfCompleteAuthorNode(MyObjectNode):
            klass = Author
            @classmethod
            def schema_common(cls):
                return {
                    'name': str,
                    'books': ListOfBooks,
                }

        class CompleteAuthorNode(MyObjectNode):
            klass = Author
            @classmethod
            def schema_common(cls):
                return {
                    'name': str,
                    'books': ListOfBookNode,
                }

        self.Book = Book
        self.Author = Author
        self.BookNode = BookNode
        self.ListOfBooks = ListOfBooks
        self.CompleteAuthorNode = CompleteAuthorNode
        self.HalfCompleteAuthorNode = HalfCompleteAuthorNode
        self.SimpleAuthorNode = SimpleAuthorNode

        books = [Book('1984'), Book('animal farm')]
        george = Author('George Orwell', books)
        self.george = george

        self.serializer = Cast({
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): IdentityNode,
        }, {
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): IdentityNode,
            AllSubSetsOf(Author): MappingNode,
            AllSubSetsOf(Book): MappingNode,
        })

        self.deserializer = Cast({
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): IdentityNode,
        })

    def serialize_given_complete_schema_test(self):
        """
        test serialize object with a node class providing complete schema.
        """
        self.assertEqual(self.serializer(self.george, frm=self.CompleteAuthorNode), {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })
        self.serializer.node_class_map[ClassSet(self.Author)] = self.CompleteAuthorNode
        self.assertEqual(self.serializer(self.george), {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })

    def deserialize_given_complete_schema_test(self):
        """
        test deserialize object with node class providing complete schema
        """
        truman = self.deserializer({'name': 'Truman Capote', 'books': [
            {'title': 'In cold blood'},
        ]}, to=self.CompleteAuthorNode)
        self.assertTrue(isinstance(truman, self.Author))
        self.assertEqual(truman.name, 'Truman Capote')
        self.assertEqual(len(truman.books), 1)
        for book in truman.books:
            self.assertTrue(isinstance(book, self.Book))
        self.assertEqual(truman.books[0].title, 'In cold blood')

    def serialize_given_halfcomplete_schema_test(self):
        """
        test serialize object with a node class providing half complete schema.
        """
        self.serializer.node_class_map[ClassSet(self.Book)] = self.BookNode
        self.assertEqual(self.serializer(self.george, frm=self.HalfCompleteAuthorNode), {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })
        self.serializer.node_class_map[ClassSet(self.Author)] = self.HalfCompleteAuthorNode
        self.assertEqual(self.serializer(self.george), {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })

    def deserialize_given_halfcomplete_schema_test(self):
        """
        test deserialize object with node class providing half complete schema
        """
        self.deserializer.node_class_map[ClassSet(self.Book)] = self.BookNode
        truman = self.deserializer({'name': 'Truman Capote', 'books': [
            {'title': 'In cold blood'},
        ]}, to=self.HalfCompleteAuthorNode)
        self.assertTrue(isinstance(truman, self.Author))
        self.assertEqual(truman.name, 'Truman Capote')
        self.assertEqual(len(truman.books), 1)
        for book in truman.books:
            self.assertTrue(isinstance(book, self.Book))
        self.assertEqual(truman.books[0].title, 'In cold blood')

    def serialize_given_simple_schema_test(self):
        """
        test serialize object with a node class providing schema with missing infos.
        """
        self.serializer.node_class_map[ClassSet(self.Book)] = self.BookNode
        self.assertEqual(self.serializer(self.george, frm=self.SimpleAuthorNode), {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })
        self.serializer.node_class_map[ClassSet(self.Author)] = self.SimpleAuthorNode
        self.assertEqual(self.serializer(self.george), {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })

    def deserialize_given_simple_schema_test(self):
        """
        test deserialize object with node class providing schema missing infos.
        """
        self.deserializer.fallback_map[ClassSet(dict)] = self.BookNode
        truman = self.deserializer({'name': 'Truman Capote', 'books': [
            {'title': 'In cold blood'},
        ]}, to=self.SimpleAuthorNode)

        self.assertTrue(isinstance(truman, self.Author))
        self.assertEqual(truman.name, 'Truman Capote')
        self.assertEqual(len(truman.books), 1)
        for book in truman.books:
            self.assertTrue(isinstance(book, self.Book))
        self.assertEqual(truman.books[0].title, 'In cold blood')


class Cast_ObjectNode_dict_tests(unittest.TestCase):
    """
    Test working with ObjectNode for dict data.
    """

    def setUp(self):
        class DictObjectNode(dict, ObjectNode):
            klass = dict
            @classmethod
            def dump(cls, obj):
                for name in ['aa']:
                    yield name, cls.getattr(obj, name)
                for k, v in obj.items():
                    yield k, v
            @classmethod
            def schema_dump(cls):
                return {AttrDict.KeyAny: NodeInfo()}
            def get_aa(self):
                return 'bloblo'

        self.DictObjectNode = DictObjectNode
        self.cast = Cast({
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(object): IdentityNode,
        })

    def dump_test(self):
        node = self.DictObjectNode({'a': 1, 'b': 2})
        self.assertEqual(dict(self.DictObjectNode.dump(node)), {'a': 1, 'b': 2, 'aa': 'bloblo'})

    def cast_test(self):
        node = self.DictObjectNode({'a': 1, 'b': 2})
        self.assertEqual(dict(self.DictObjectNode.dump(node)), {'a': 1, 'b': 2, 'aa': 'bloblo'})

        data = self.cast(node, frm=self.DictObjectNode, to=dict)
        self.assertEqual(data, {'a': 1, 'b': 2, 'aa': 'bloblo'})

