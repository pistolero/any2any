# -*- coding: utf-8 -*-
from any2any.cast import Cast, CompiledSchema, SchemaNotValid, SchemasDontMatch, NoSuitableBundleClass
from any2any.bundle import Bundle, IdentityBundle, MappingBundle, IterableBundle, ObjectBundle
from any2any.utils import AllSubSetsOf, Singleton, ClassSet
from nose.tools import assert_raises, ok_


class CompiledSchema_Test(object):
    """
    Test CompiledSchema
    """

    def valid_schemas_test(self):
        """
        Test validate_schema with valid schemas.
        """
        ok_(CompiledSchema.validate_schema({Bundle.KeyAny: str}) is None)
        ok_(CompiledSchema.validate_schema({Bundle.KeyFinal: int}) is None)
        ok_(CompiledSchema.validate_schema({0: int, 1: str, 'a': basestring}) is None)

    def unvalid_schemas_test(self):
        """
        Test validate_schema with unvalid schemas.
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
        Test validate_schemas_match with 2 valid schemas
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
        Test validate_schemas_match with 2 unvalid schemas
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
        Test CompliedSchema.get_out_class
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


class Cast_Test(object):
    """
    Test Cast
    """

    def get_bundle_class_test(self):
        """
        Test Cast.get_bundle_class
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
        Test Cast.get_bundle_class with no suitable bundle class
        """
        assert_raises(NoSuitableBundleClass, Cast.get_bundle_class, str, {Singleton(int): IntBundle})

    def call_test(self):
        """
        Test Cast.__call__
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

    def complex_call_test(self):
        """
        Test Cast.__call__ with complex object
        """
        class Book(object):
            def __init__(self, title):
                self.title = title
        class Author(object):
            def __init__(self, name, books):
                self.name = name
                self.books = books
        class ListOfBooks(IterableBundle):
            value_type = Book
        class AuthorBundle(ObjectBundle):
            @classmethod
            def default_schema(cls):
                return {
                    'name': str,
                    'books': ListOfBooks,
                }
        class BookBundle(ObjectBundle):
            @classmethod
            def default_schema(cls):
                return {'title': str,}

        cast = Cast({
            Singleton(Book): BookBundle,
            Singleton(Author): AuthorBundle,
            #Singleton(Bundle.ValueUnknown): MappingBundle,
            AllSubSetsOf(dict): MappingBundle,
            AllSubSetsOf(list): IterableBundle,
            AllSubSetsOf(object): IdentityBundle,
        }, {
            Singleton(Book): MappingBundle,
        })
        books = [Book('1984'), Book('animal farm')]
        george = Author('George Orwell', books)
        ok_(cast(george, out_class=dict) == {'name': 'George Orwell', 'books': [
            {'title': '1984'},
            {'title': 'animal farm'},
        ]})
                

