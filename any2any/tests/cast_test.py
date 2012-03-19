# -*- coding: utf-8 -*-
from any2any.bundle import *
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


class MyBundle(Bundle):

    @classmethod
    def default_schema(cls):
        return {}

class BaseStrBundle(MyBundle): pass
class IntBundle(MyBundle): pass
class MyFloatBundle(MyBundle):
    klass = float


class Cast_test(object):

    def get_fallback_test(self):
        """
        Test Cast._get_fallback
        """
        cast = Cast({AllSubSetsOf(object): IdentityBundle}, {
            AllSubSetsOf(basestring): BaseStrBundle,
            AllSubSetsOf(list): IdentityBundle,
            Singleton(int): IntBundle,
        })
        # With KeyFinal in schema
        in_bc = IntBundle.get_subclass(schema={SmartDict.KeyFinal: int})
        out_bc = cast._get_fallback(in_bc)
        ok_(issubclass(out_bc, IntBundle))
        # Get from the fallback map
        in_bc = IntBundle.get_subclass(klass=int)
        out_bc = cast._get_fallback(in_bc)
        ok_(issubclass(out_bc, IntBundle))
        # default
        in_bc = IntBundle.get_subclass(schema={'haha': int})
        out_bc = cast._get_fallback(in_bc)
        ok_(out_bc.get_schema() == {'haha': int})

    def call_test(self):
        """
        test simple calls
        """
        cast = Cast({
            AllSubSetsOf(dict): MappingBundle,
            AllSubSetsOf(list): IterableBundle,
            AllSubSetsOf(object): IdentityBundle,
        })
        ok_(cast({'a': 1, 'b': 2}, out_class=dict) == {'a': 1, 'b': 2})
        ok_(cast({'a': 1, 'b': 2}, out_class=list) == [1, 2])
        ok_(cast(['a', 'b', 'c'], out_class=dict) == {0: 'a', 1: 'b', 2: 'c'})
        ok_(cast(['a', 'b', 'c'], out_class=list) == ['a', 'b', 'c'])
        ok_(cast(1, out_class=int) == 1)


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

        class BookBundle(ObjectBundle):
            klass = Book
            @classmethod
            def default_schema(cls):
                return {'title': str,}

        class ListOfBooks(IterableBundle):
            value_type = Book

        class ListOfBookBundle(IterableBundle):
            value_type = BookBundle

        class SimpleAuthorBundle(ObjectBundle):
            klass = Author
            @classmethod
            def default_schema(cls):
                return {
                    'name': str,
                    'books': list,
                }

        class HalfCompleteAuthorBundle(ObjectBundle):
            klass = Author
            @classmethod
            def default_schema(cls):
                return {
                    'name': str,
                    'books': ListOfBooks,
                }

        class CompleteAuthorBundle(ObjectBundle):
            klass = Author
            @classmethod
            def default_schema(cls):
                return {
                    'name': str,
                    'books': ListOfBookBundle,
                }

        self.Book = Book
        self.Author = Author
        self.BookBundle = BookBundle
        self.ListOfBooks = ListOfBooks
        self.CompleteAuthorBundle = CompleteAuthorBundle
        self.HalfCompleteAuthorBundle = HalfCompleteAuthorBundle
        self.SimpleAuthorBundle = SimpleAuthorBundle

        books = [Book('1984'), Book('animal farm')]
        george = Author('George Orwell', books)
        self.george = george

        self.serializer = Cast({
            AllSubSetsOf(dict): MappingBundle,
            AllSubSetsOf(list): IterableBundle,
            AllSubSetsOf(object): IdentityBundle,
        }, {
            AllSubSetsOf(dict): MappingBundle,
            AllSubSetsOf(list): IterableBundle,
            AllSubSetsOf(object): MappingBundle,
        })

        self.deserializer = Cast({
            AllSubSetsOf(dict): MappingBundle,
            AllSubSetsOf(list): IterableBundle,
            AllSubSetsOf(object): IdentityBundle,
        })

    def serialize_given_complete_schema_test(self):
        """
        test serialize object with a bundle class providing complete schema.
        """
        ok_(self.serializer(self.george, in_class=self.CompleteAuthorBundle) == {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })
        self.serializer.bundle_class_map[Singleton(self.Author)] = self.CompleteAuthorBundle
        ok_(self.serializer(self.george) == {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })

    def deserialize_given_complete_schema_test(self):
        """
        test deserialize object with bundle class providing complete schema
        """
        truman = self.deserializer({'name': 'Truman Capote', 'books': [
            {'title': 'In cold blood'},
        ]}, out_class=self.CompleteAuthorBundle)
        ok_(isinstance(truman, self.Author))
        ok_(truman.name == 'Truman Capote')
        ok_(len(truman.books) == 1)
        for book in truman.books:
            ok_(isinstance(book, self.Book))
        ok_(truman.books[0].title == 'In cold blood')

    def serialize_given_halfcomplete_schema_test(self):
        """
        test serialize object with a bundle class providing half complete schema.
        """
        self.serializer.bundle_class_map[Singleton(self.Book)] = self.BookBundle
        ok_(self.serializer(self.george, in_class=self.HalfCompleteAuthorBundle) == {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })
        self.serializer.bundle_class_map[Singleton(self.Author)] = self.HalfCompleteAuthorBundle
        ok_(self.serializer(self.george) == {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })

    def deserialize_given_halfcomplete_schema_test(self):
        """
        test deserialize object with bundle class providing half complete schema
        """
        self.deserializer.bundle_class_map[Singleton(self.Book)] = self.BookBundle
        truman = self.deserializer({'name': 'Truman Capote', 'books': [
            {'title': 'In cold blood'},
        ]}, out_class=self.HalfCompleteAuthorBundle)
        ok_(isinstance(truman, self.Author))
        ok_(truman.name == 'Truman Capote')
        ok_(len(truman.books) == 1)
        for book in truman.books:
            ok_(isinstance(book, self.Book))
        ok_(truman.books[0].title == 'In cold blood')

    def serialize_given_simple_schema_test(self):
        """
        test serialize object with a bundle class providing schema with missing infos.
        """
        self.serializer.bundle_class_map[Singleton(self.Book)] = self.BookBundle
        ok_(self.serializer(self.george, in_class=self.SimpleAuthorBundle) == {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })
        self.serializer.bundle_class_map[Singleton(self.Author)] = self.SimpleAuthorBundle
        ok_(self.serializer(self.george) == {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })

    def deserialize_given_simple_schema_test(self):
        """
        test deserialize object with bundle class providing schema missing infos.
        """
        self.deserializer.fallback_map[Singleton(dict)] = self.BookBundle
        truman = self.deserializer({'name': 'Truman Capote', 'books': [
            {'title': 'In cold blood'},
        ]}, out_class=self.SimpleAuthorBundle)
        ok_(isinstance(truman, self.Author))
        ok_(truman.name == 'Truman Capote')
        ok_(len(truman.books) == 1)
        for book in truman.books:
            ok_(isinstance(book, self.Book))
        ok_(truman.books[0].title == 'In cold blood')


class Cast_ObjectBundle_dict_tests(object):
    """
    Test working with ObjectBundle for dict data.
    """

    def setUp(self):
        class DictObjectBundle(ObjectBundle):
            klass = dict
            schema = {SmartDict.KeyAny: SmartDict.ValueUnknown}
            def iter(self):
                for name in ['aa']:
                    yield name, self.getattr(name)
                for k, v in self.obj.items():
                    yield k, v
            def get_aa(self):
                return 'bloblo'

        self.DictObjectBundle = DictObjectBundle
        self.cast = Cast({
            AllSubSetsOf(dict): MappingBundle,
            AllSubSetsOf(object): IdentityBundle,
        })

    def iter_test(self):
        d = {'a': 1, 'b': 2}
        bundle = self.DictObjectBundle(d)
        ok_(dict(bundle) == {'a': 1, 'b': 2, 'aa': 'bloblo'})

    def cast_test(self):
        d = {'a': 1, 'b': 2}
        bundle = self.DictObjectBundle(d)
        ok_(dict(bundle) == {'a': 1, 'b': 2, 'aa': 'bloblo'})

        data = self.cast(d, in_class=self.DictObjectBundle, out_class=dict)
        ok_(data == {'a': 1, 'b': 2, 'aa': 'bloblo'})

