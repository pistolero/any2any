# -*- coding: utf-8 -*-
from any2any.cast import Cast, CompiledSchema, SchemaNotValid, SchemasDontMatch
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

    def instantiate_test(self):
        """
        Test instantiating with 2 matching schemas.
        """
        schema_in = {'a': int, 'b': str, 'c': float}
        schema_out = {'a': int, 'c': int}
        ok_(CompiledSchema(schema_in, schema_out))

        schema_in = {'a': int, 'b': str, 'c': float}
        schema_out = {Bundle.KeyAny: int}
        ok_(CompiledSchema(schema_in, schema_out))

        schema_in = {Bundle.KeyAny: int}
        schema_out = {Bundle.KeyAny: float}
        ok_(CompiledSchema(schema_in, schema_out))

        schema_in = {Bundle.KeyFinal: str}
        schema_out = {Bundle.KeyFinal: unicode}
        ok_(CompiledSchema(schema_in, schema_out))

    def instantiate_error_test(self):
        """
        Test instantiating with not matching schemas.
        """
        schema_in = {0: int, 1: float}
        schema_out = {1: str, 2: int}
        assert_raises(SchemasDontMatch, CompiledSchema, schema_in, schema_out)
        
        schema_in = {Bundle.KeyFinal: int}
        schema_out = {1: str}
        assert_raises(SchemasDontMatch, CompiledSchema, schema_in, schema_out)

        schema_in = {Bundle.KeyAny: int}
        schema_out = {'a': int, 'b': str}
        assert_raises(SchemasDontMatch, CompiledSchema, schema_in, schema_out)

        schema_in = {Bundle.KeyAny: int}
        schema_out = {'a': int, 'b': str}
        assert_raises(SchemasDontMatch, CompiledSchema, schema_in, schema_out)

        schema_in = {Bundle.KeyFinal: int}
        schema_out = {Bundle.KeyAny: int}
        assert_raises(SchemasDontMatch, CompiledSchema, schema_in, schema_out)

    def query_schema_test(self):
        """
        Test CompliedSchema.get
        """
        schema_in = {'a': int, 'b': str}
        schema_out = {'a': float}
        compiled = CompiledSchema(schema_in, schema_out)
        ok_(compiled.get('a') is float)
        assert_raises(KeyError, compiled.get, 'b')
        
        schema_in = {'a': int, 'b': str, 'c': float}
        schema_out = {Bundle.KeyAny: int}
        compiled = CompiledSchema(schema_in, schema_out)
        ok_(compiled.get('a') is int)
        ok_(compiled.get('b') is int)
        ok_(compiled.get('c') is int)
        ok_(compiled.get(987) is int)

        schema_in = {Bundle.KeyAny: int}
        schema_out = {Bundle.KeyAny: float}
        compiled = CompiledSchema(schema_in, schema_out)
        ok_(compiled.get('wxd') is float)
        ok_(compiled.get(7) is float)

        schema_in = {Bundle.KeyFinal: str}
        schema_out = {Bundle.KeyFinal: unicode}
        compiled = CompiledSchema(schema_in, schema_out)
        ok_(compiled.get(Bundle.KeyFinal) is unicode)
        assert_raises(KeyError, compiled.get, 'a')


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
        cast = Cast({
            AllSubSetsOf(basestring): BaseStrBundle,
            AllSubSetsOf(object): IdentityBundle,
            Singleton(int): IntBundle,
        })
        bundle_class = cast.get_bundle_class(object)
        ok_(issubclass(bundle_class, IdentityBundle))
        ok_(bundle_class.klass is object)

        bundle_class = cast.get_bundle_class(float)
        ok_(issubclass(bundle_class, IdentityBundle))
        ok_(bundle_class.klass is float)

        bundle_class = cast.get_bundle_class(str)
        ok_(issubclass(bundle_class, BaseStrBundle))
        ok_(bundle_class.klass is str)

        bundle_class = cast.get_bundle_class(int)
        ok_(issubclass(bundle_class, IntBundle))
        ok_(bundle_class.klass is int)

    def call_test(self):
        """
        Test Cast.__call__
        """
        cast = Cast({
            AllSubSetsOf(dict): MappingBundle,
            AllSubSetsOf(list): IterableBundle,
            AllSubSetsOf(object): IdentityBundle,
        })
        ok_(cast({'a': 1, 'b': 2}, to=dict) == {'a': 1, 'b': 2})
        ok_(cast({'a': 1, 'b': 2}, to=list) == [1, 2])
        ok_(cast(['a', 'b', 'c'], to=dict) == {0: 'a', 1: 'b', 2: 'c'})
        ok_(cast(['a', 'b', 'c'], to=list) == ['a', 'b', 'c'])
        ok_(cast(1, to=int) == 1)


