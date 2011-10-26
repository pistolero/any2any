# -*- coding: utf-8 -*-
from any2any.cast import Cast, CompiledSchema, SchemaNotValid, SchemasDontMatch, NoSuitableBundleClass
from any2any.bundle import Bundle, IdentityBundle, MappingBundle, IterableBundle, ObjectBundle
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
        schema_in = {'a': int, 'b': str, 'c': float}
        schema_out = {'a': int, 'c': int}
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
        schema_in = {'a': int, 'b': str}
        schema_out = {'a': float}
        compiled = CompiledSchema(schema_in, schema_out)
        ok_(compiled.get_out_class('a') is float)
        assert_raises(KeyError, compiled.get_out_class, 'b')
        
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


class BaseStrBundle(IdentityBundle): pass
class IntBundle(IdentityBundle): pass


class Cast_test(object):
    """
    test Cast
    """

    def get_bundle_class_test(self):
        """
        test Cast.get_bundle_class
        """
        bundle_class_map = {
            AllSubSetsOf(basestring): BaseStrBundle,
            AllSubSetsOf(object): IdentityBundle,
            Singleton(int): IntBundle,
        }
        bundle_class = Cast.get_bundle_class(object, bundle_class_map)
        ok_(bundle_class is IdentityBundle)

        bundle_class = Cast.get_bundle_class(float, bundle_class_map)
        ok_(bundle_class is IdentityBundle)

        bundle_class = Cast.get_bundle_class(str, bundle_class_map)
        ok_(bundle_class is BaseStrBundle)

        bundle_class = Cast.get_bundle_class(int, bundle_class_map)
        ok_(bundle_class is IntBundle)

    def no_bundle_class_test(self):
        """
        test Cast.get_bundle_class with no suitable bundle class
        """
        assert_raises(NoSuitableBundleClass, Cast.get_bundle_class, str, {Singleton(int): IntBundle})

    def get_actual_schema_test(self):
        """
        test Cast.get_actual_schema
        """        
        schema = Cast.get_actual_schema({'a': 1, 'b': 'b'}, MappingBundle)
        ok_(schema == {'a': int, 'b': str})
        schema = Cast.get_actual_schema([1, 'b', 2.0], IterableBundle)
        ok_(schema == {0: int, 1: str, 2: float})

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

    def serialize_given_complete_schema_test(self):
        """
        test serialize object with a bundle class providing complete schema.
        """
        # specifying a 
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

    '''
def deserialize_given_complete_schema_test(self):
        """
        test deserialize object with bundle class providing complete schema
        """
        truman = cast({'name': 'Truman Capote', 'books': [
            {'title': 'In cold blood'},
        ]}, out_class=Author)
        ok_(truman.name == 'Truman Capote')
        ok_(len(truman.books) == 1)
        ok_(truman.books[0].title == 'In cold blood')
                
    '''
