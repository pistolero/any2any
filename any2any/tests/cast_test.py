# -*- coding: utf-8 -*-
from any2any.cast import Cast, CompiledSchema, SchemaNotValid, SchemasDontMatch, NoSuitableBundleClass
from any2any.bundle import Bundle, IdentityBundle, MappingBundle, IterableBundle, ObjectBundle, ValueInfo
from any2any.utils import AllSubSetsOf, Singleton, ClassSet
from nose.tools import assert_raises, ok_


class CompiledSchema_test(object):
    """
    test CompiledSchema
    """

    def valid_schemas_test(self):
        """
        test validate_schema with valid schemas.
        """
        ok_(CompiledSchema.validate_schema({Bundle.KeyAny: str}) is None)
        ok_(CompiledSchema.validate_schema({Bundle.KeyFinal: int}) is None)
        ok_(CompiledSchema.validate_schema({0: int, 1: str, 'a': basestring}) is None)

    def unvalid_schemas_test(self):
        """
        test validate_schema with unvalid schemas.
        """
        assert_raises(SchemaNotValid, CompiledSchema.validate_schema, {
            Bundle.KeyAny: str,
            1: int
        })
        assert_raises(SchemaNotValid, CompiledSchema.validate_schema, {
            Bundle.KeyFinal: str,
            'a': str,
            'bb': float
        })
        assert_raises(SchemaNotValid, CompiledSchema.validate_schema, {
            Bundle.KeyFinal: str,
            Bundle.KeyAny: int
        })

    def validate_schemas_match_test(self):
        """
        test validate_schemas_match with 2 valid schemas
        """
        schema_in = {'a': int, 'c': int}
        schema_out = {'a': int, 'b': str, 'c': float}
        ok_(CompiledSchema.validate_schemas_match(schema_in, schema_out) is None)

        schema_in = {'a': int, 'b': str, 'c': float}
        schema_out = {Bundle.KeyAny: int}
        ok_(CompiledSchema.validate_schemas_match(schema_in, schema_out) is None)

        schema_in = {Bundle.KeyAny: int}
        schema_out = {Bundle.KeyAny: float}
        ok_(CompiledSchema.validate_schemas_match(schema_in, schema_out) is None)

        schema_in = {Bundle.KeyFinal: str}
        schema_out = {Bundle.KeyFinal: unicode}
        ok_(CompiledSchema.validate_schemas_match(schema_in, schema_out) is None)

    def instantiate_error_test(self):
        """
        test validate_schemas_match with 2 unvalid schemas
        """
        schema_in = {0: int, 1: float}
        schema_out = {1: str, 2: int}
        assert_raises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)
        
        schema_in = {Bundle.KeyFinal: int}
        schema_out = {1: str}
        assert_raises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)

        schema_in = {Bundle.KeyAny: int}
        schema_out = {'a': int, 'b': str}
        assert_raises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)

        schema_in = {Bundle.KeyAny: int}
        schema_out = {'a': int, 'b': str}
        assert_raises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)

        schema_in = {Bundle.KeyFinal: int}
        schema_out = {Bundle.KeyAny: int}
        assert_raises(SchemasDontMatch, CompiledSchema.validate_schemas_match, schema_in, schema_out)

    def get_out_class_test(self):
        """
        test CompliedSchema.get_out_class
        """
        schema_in = {'a': float}
        schema_out = {'a': int, 'b': str}
        compiled = CompiledSchema(schema_in, schema_out)
        ok_(compiled.get_out_class('a') is int)
        assert_raises(KeyError, compiled.get_in_class, 'b')
        
        schema_in = {'a': int, 'b': str, 'c': float}
        schema_out = {Bundle.KeyAny: int}
        compiled = CompiledSchema(schema_in, schema_out)
        ok_(compiled.get_out_class('a') is int)
        ok_(compiled.get_out_class('b') is int)
        ok_(compiled.get_out_class('c') is int)
        ok_(compiled.get_out_class(987) is int)

        schema_in = {Bundle.KeyAny: int}
        schema_out = {Bundle.KeyAny: float}
        compiled = CompiledSchema(schema_in, schema_out)
        ok_(compiled.get_out_class('wxd') is float)
        ok_(compiled.get_out_class(7) is float)

        schema_in = {Bundle.KeyFinal: str}
        schema_out = {Bundle.KeyFinal: unicode}
        compiled = CompiledSchema(schema_in, schema_out)
        ok_(compiled.get_out_class(Bundle.KeyFinal) is unicode)
        assert_raises(KeyError, compiled.get_out_class, 'a')


class BaseStrBundle(Bundle): pass
class IntBundle(Bundle): pass


class Cast_test(object):
    """
    test Cast
    """

    def pick_best_test(self):
        """
        test Cast._pick_best
        """
        bundle_class_map = {
            AllSubSetsOf(basestring): BaseStrBundle,
            AllSubSetsOf(object): IdentityBundle,
            Singleton(int): IntBundle,
        }
        bundle_class = Cast._pick_best(object, bundle_class_map)
        ok_(bundle_class is IdentityBundle)

        bundle_class = Cast._pick_best(float, bundle_class_map)
        ok_(bundle_class is IdentityBundle)

        bundle_class = Cast._pick_best(str, bundle_class_map)
        ok_(bundle_class is BaseStrBundle)

        bundle_class = Cast._pick_best(int, bundle_class_map)
        ok_(bundle_class is IntBundle)

    def no_pick_test(self):
        """
        test Cast._pick_best with no suitable bundle class
        """
        assert_raises(NoSuitableBundleClass, Cast._pick_best, str, {Singleton(int): IntBundle})

    def get_bundle_class_test(self):
        """
        test Cast._get_bundle_class
        """
        cast = Cast({
            AllSubSetsOf(basestring): BaseStrBundle,
            AllSubSetsOf(list): IdentityBundle,
            Singleton(int): IntBundle,
        })
        # With a bundle class
        ok_(cast._get_bundle_class(BaseStrBundle) is BaseStrBundle)
        # with a normal class
        bundle_class = cast._get_bundle_class(int)
        ok_(issubclass(bundle_class, IntBundle))
        ok_(bundle_class.klass is int)
        bundle_class = cast._get_bundle_class(str)
        ok_(issubclass(bundle_class, BaseStrBundle))
        ok_(bundle_class.klass is str)
        # with a ValueInfo
        value_info = ValueInfo(klass=int, schema={'a': str})
        bundle_class = cast._get_bundle_class(value_info)
        ok_(issubclass(bundle_class, IntBundle))
        ok_(bundle_class.klass is int)
        ok_(bundle_class.schema == {'a': str})
        value_info = ValueInfo(klass=tuple, lookup_with=(float, basestring, list))
        bundle_class = cast._get_bundle_class(value_info)
        ok_(issubclass(bundle_class, BaseStrBundle))
        ok_(bundle_class.klass is tuple)

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
