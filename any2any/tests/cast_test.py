# -*- coding: utf-8 -*-
import unittest

from any2any.node import *
from any2any.cast import *
from any2any.utils import *


class CompiledSchema_test(unittest.TestCase):
    """
    test CompiledSchema
    """

    def valid_schemas_test(self):
        """
        test validate_schema with valid schemas.
        """
        self.assertIsNone(CompiledSchema.validate_schema({AttrDict.KeyAny: str}))
        self.assertIsNone(CompiledSchema.validate_schema({AttrDict.KeyAny: str, 1: int}))
        self.assertIsNone(CompiledSchema.validate_schema({AttrDict.KeyFinal: int}))
        self.assertIsNone(CompiledSchema.validate_schema({0: int, 1: str, 'a': basestring}))

    def unvalid_schemas_test(self):
        """
        test validate_schema with unvalid schemas.
        """
        self.assertRaises(SchemaNotValid, CompiledSchema.validate_schema, {
            AttrDict.KeyFinal: str,
            'a': str,
            'bb': float
        })
        self.assertRaises(SchemaNotValid, CompiledSchema.validate_schema, {
            AttrDict.KeyFinal: str,
            AttrDict.KeyAny: int
        })

    def validate_schemas_match_test(self):
        """
        test validate_schemas_match with 2 valid schemas
        """
        schema_in = {'a': int, 'c': int}
        schema_out = {'a': int, 'b': str, 'c': float}
        self.assertIsNone(CompiledSchema.validate_schemas_match(schema_in, schema_out))

        schema_in = {'a': int, 'b': str, 'c': float}
        schema_out = {AttrDict.KeyAny: int}
        self.assertIsNone(CompiledSchema.validate_schemas_match(schema_in, schema_out))

        schema_in = {AttrDict.KeyAny: int}
        schema_out = {AttrDict.KeyAny: float}
        self.assertIsNone(CompiledSchema.validate_schemas_match(schema_in, schema_out))

        schema_in = {AttrDict.KeyFinal: str}
        schema_out = {AttrDict.KeyFinal: unicode}
        self.assertIsNone(CompiledSchema.validate_schemas_match(schema_in, schema_out))

    def instantiate_error_test(self):
        """
        test validate_schemas_match with 2 unvalid schemas
        """
        schema_in = {0: int, 1: float}
        schema_out = {1: str, 2: int}
        self.assertRaises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)
        
        schema_in = {AttrDict.KeyFinal: int}
        schema_out = {1: str}
        self.assertRaises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)

        schema_in = {AttrDict.KeyAny: int}
        schema_out = {'a': int, 'b': str}
        self.assertRaises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)

        schema_in = {AttrDict.KeyAny: int}
        schema_out = {'a': int, 'b': str}
        self.assertRaises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)

        schema_in = {AttrDict.KeyFinal: int}
        schema_out = {AttrDict.KeyAny: int}
        self.assertRaises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)


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

    def get_fallback_test(self):
        """
        Test Cast._get_fallback
        """
        cast = Cast({AllSubSetsOf(object): IdentityNode}, {
            AllSubSetsOf(basestring): BaseStrNode,
            AllSubSetsOf(list): IdentityNode,
            ClassSet(int): IntNode,
        })
        class MyIntNode1(IntNode):
            @classmethod
            def schema_dump(cls):
                return {AttrDict.KeyFinal: int}

        class MyIntNode2(IntNode):
            klass = int

        class MyIntNode3(IntNode):
            @classmethod
            def schema_dump(cls):
                return {'haha': int}

        # With KeyFinal in schema
        out_bc = cast._get_fallback(MyIntNode1)
        self.assertTrue(issubclass(out_bc, IntNode))
        # Get from the fallback map
        out_bc = cast._get_fallback(MyIntNode2)
        self.assertTrue(issubclass(out_bc, IntNode))
        # default
        out_bc = cast._get_fallback(MyIntNode3)
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
        self.assertEqual(cast({'a': 1, 'b': 2}, out_class=dict), {'a': 1, 'b': 2})
        self.assertEqual(cast({'a': 1, 'b': 2}, out_class=list), [1, 2])
        self.assertEqual(cast(['a', 'b', 'c'], out_class=dict), {0: 'a', 1: 'b', 2: 'c'})
        self.assertEqual(cast(['a', 'b', 'c'], out_class=list), ['a', 'b', 'c'])
        self.assertEqual(cast(1, out_class=int), 1)

    def improvise_schema_test(self):
        cast = Cast({})
        schema = cast.improvise_schema({'a': 1, 'b': 'b'}, MappingNode)
        self.assertEqual(schema, {'a': int, 'b': str})
        schema = cast.improvise_schema([1, 'b', 2.0], IterableNode)
        self.assertEqual(schema, {0: int, 1: str, 2: float})


class Cast_complex_calls_test(unittest.TestCase):
    """
    Test casting complex objects
    """

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
            AllSubSetsOf(object): MappingNode,
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
        self.assertEqual(self.serializer(self.george, in_class=self.CompleteAuthorNode), {
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
        ]}, out_class=self.CompleteAuthorNode)
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
        self.assertEqual(self.serializer(self.george, in_class=self.HalfCompleteAuthorNode), {
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
        ]}, out_class=self.HalfCompleteAuthorNode)
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
        self.assertEqual(self.serializer(self.george, in_class=self.SimpleAuthorNode), {
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
        ]}, out_class=self.SimpleAuthorNode)
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
        class DictObjectNode(ObjectNode):
            klass = dict
            def dump(self):
                for name in ['aa']:
                    yield name, self.getattr(name)
                for k, v in self.obj.items():
                    yield k, v
            @classmethod
            def schema_dump(cls):
                return {AttrDict.KeyAny: AttrDict.ValueUnknown}
            def get_aa(self):
                return 'bloblo'

        self.DictObjectNode = DictObjectNode
        self.cast = Cast({
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(object): IdentityNode,
        })

    def dump_test(self):
        d = {'a': 1, 'b': 2}
        node = self.DictObjectNode(d)
        self.assertEqual(dict(node.dump()), {'a': 1, 'b': 2, 'aa': 'bloblo'})

    def cast_test(self):
        d = {'a': 1, 'b': 2}
        node = self.DictObjectNode(d)
        self.assertEqual(dict(node.dump()), {'a': 1, 'b': 2, 'aa': 'bloblo'})

        data = self.cast(d, in_class=self.DictObjectNode, out_class=dict)
        self.assertEqual(data, {'a': 1, 'b': 2, 'aa': 'bloblo'})

