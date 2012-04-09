# -*- coding: utf-8 -*-
from any2any.node import *
from any2any.cast import *
from any2any.utils import *
from nose.tools import assert_raises, ok_


class CompiledSchema_test(object):
    """
    test CompiledSchema
    """

    def valid_schemas_test(self):
        """
        test validate_schema with valid schemas.
        """
        ok_(CompiledSchema.validate_schema({SmartDict.KeyAny: str}) is None)
        ok_(CompiledSchema.validate_schema({SmartDict.KeyAny: str, 1: int}) is None)
        ok_(CompiledSchema.validate_schema({SmartDict.KeyFinal: int}) is None)
        ok_(CompiledSchema.validate_schema({0: int, 1: str, 'a': basestring}) is None)

    def unvalid_schemas_test(self):
        """
        test validate_schema with unvalid schemas.
        """
        assert_raises(SchemaNotValid, CompiledSchema.validate_schema, {
            SmartDict.KeyFinal: str,
            'a': str,
            'bb': float
        })
        assert_raises(SchemaNotValid, CompiledSchema.validate_schema, {
            SmartDict.KeyFinal: str,
            SmartDict.KeyAny: int
        })

    def validate_schemas_match_test(self):
        """
        test validate_schemas_match with 2 valid schemas
        """
        schema_in = {'a': int, 'c': int}
        schema_out = {'a': int, 'b': str, 'c': float}
        ok_(CompiledSchema.validate_schemas_match(schema_in, schema_out) is None)

        schema_in = {'a': int, 'b': str, 'c': float}
        schema_out = {SmartDict.KeyAny: int}
        ok_(CompiledSchema.validate_schemas_match(schema_in, schema_out) is None)

        schema_in = {SmartDict.KeyAny: int}
        schema_out = {SmartDict.KeyAny: float}
        ok_(CompiledSchema.validate_schemas_match(schema_in, schema_out) is None)

        schema_in = {SmartDict.KeyFinal: str}
        schema_out = {SmartDict.KeyFinal: unicode}
        ok_(CompiledSchema.validate_schemas_match(schema_in, schema_out) is None)

    def instantiate_error_test(self):
        """
        test validate_schemas_match with 2 unvalid schemas
        """
        schema_in = {0: int, 1: float}
        schema_out = {1: str, 2: int}
        assert_raises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)
        
        schema_in = {SmartDict.KeyFinal: int}
        schema_out = {1: str}
        assert_raises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)

        schema_in = {SmartDict.KeyAny: int}
        schema_out = {'a': int, 'b': str}
        assert_raises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)

        schema_in = {SmartDict.KeyAny: int}
        schema_out = {'a': int, 'b': str}
        assert_raises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)

        schema_in = {SmartDict.KeyFinal: int}
        schema_out = {SmartDict.KeyAny: int}
        assert_raises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)


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


class Cast_test(object):

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
                return {SmartDict.KeyFinal: int}

        class MyIntNode2(IntNode):
            klass = int

        class MyIntNode3(IntNode):
            @classmethod
            def schema_dump(cls):
                return {'haha': int}

        # With KeyFinal in schema
        out_bc = cast._get_fallback(MyIntNode1)
        ok_(issubclass(out_bc, IntNode))
        # Get from the fallback map
        out_bc = cast._get_fallback(MyIntNode2)
        ok_(issubclass(out_bc, IntNode))
        # default
        out_bc = cast._get_fallback(MyIntNode3)
        ok_(out_bc.schema_dump() == {'haha': int})

    def call_test(self):
        """
        test simple calls
        """
        cast = Cast({
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): IdentityNode,
        })
        ok_(cast({'a': 1, 'b': 2}, out_class=dict) == {'a': 1, 'b': 2})
        ok_(cast({'a': 1, 'b': 2}, out_class=list) == [1, 2])
        ok_(cast(['a', 'b', 'c'], out_class=dict) == {0: 'a', 1: 'b', 2: 'c'})
        ok_(cast(['a', 'b', 'c'], out_class=list) == ['a', 'b', 'c'])
        ok_(cast(1, out_class=int) == 1)

    def improvise_schema_test(self):
        cast = Cast({})
        schema = cast.improvise_schema({'a': 1, 'b': 'b'}, MappingNode)
        ok_(schema == {'a': int, 'b': str})
        schema = cast.improvise_schema([1, 'b', 2.0], IterableNode)
        ok_(schema == {0: int, 1: str, 2: float})


class Cast_complex_calls_test(object):
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
        ok_(self.serializer(self.george, in_class=self.CompleteAuthorNode) == {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })
        self.serializer.node_class_map[ClassSet(self.Author)] = self.CompleteAuthorNode
        ok_(self.serializer(self.george) == {
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
        ok_(isinstance(truman, self.Author))
        ok_(truman.name == 'Truman Capote')
        ok_(len(truman.books) == 1)
        for book in truman.books:
            ok_(isinstance(book, self.Book))
        ok_(truman.books[0].title == 'In cold blood')

    def serialize_given_halfcomplete_schema_test(self):
        """
        test serialize object with a node class providing half complete schema.
        """
        self.serializer.node_class_map[ClassSet(self.Book)] = self.BookNode
        ok_(self.serializer(self.george, in_class=self.HalfCompleteAuthorNode) == {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })
        self.serializer.node_class_map[ClassSet(self.Author)] = self.HalfCompleteAuthorNode
        ok_(self.serializer(self.george) == {
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
        ok_(isinstance(truman, self.Author))
        ok_(truman.name == 'Truman Capote')
        ok_(len(truman.books) == 1)
        for book in truman.books:
            ok_(isinstance(book, self.Book))
        ok_(truman.books[0].title == 'In cold blood')

    def serialize_given_simple_schema_test(self):
        """
        test serialize object with a node class providing schema with missing infos.
        """
        self.serializer.node_class_map[ClassSet(self.Book)] = self.BookNode
        ok_(self.serializer(self.george, in_class=self.SimpleAuthorNode) == {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })
        self.serializer.node_class_map[ClassSet(self.Author)] = self.SimpleAuthorNode
        ok_(self.serializer(self.george) == {
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
        ok_(isinstance(truman, self.Author))
        ok_(truman.name == 'Truman Capote')
        ok_(len(truman.books) == 1)
        for book in truman.books:
            ok_(isinstance(book, self.Book))
        ok_(truman.books[0].title == 'In cold blood')


class Cast_ObjectNode_dict_tests(object):
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
                return {SmartDict.KeyAny: SmartDict.ValueUnknown}
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
        ok_(dict(node.dump()) == {'a': 1, 'b': 2, 'aa': 'bloblo'})

    def cast_test(self):
        d = {'a': 1, 'b': 2}
        node = self.DictObjectNode(d)
        ok_(dict(node.dump()) == {'a': 1, 'b': 2, 'aa': 'bloblo'})

        data = self.cast(d, in_class=self.DictObjectNode, out_class=dict)
        ok_(data == {'a': 1, 'b': 2, 'aa': 'bloblo'})

