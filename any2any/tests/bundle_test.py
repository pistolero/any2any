# -*- coding: utf-8 -*-
from nose.tools import assert_raises, ok_
from any2any.bundle import *


class Bundle_Test(object):
    """
    Tests on Bundle
    """
    
    def get_subclass_test(self):
        MyBundle = Bundle.get_subclass(klass=int, bla=8)
        ok_(issubclass(MyBundle, Bundle))
        ok_(not issubclass(Bundle, MyBundle))
        ok_(MyBundle.klass == int)
        ok_(MyBundle.bla == 8)

    def get_actual_schema_test(self):
        """
        test Bundle.get_actual_schema
        """
        schema = MappingBundle({'a': 1, 'b': 'b'}).get_actual_schema()
        ok_(schema == {'a': int, 'b': str})
        schema = IterableBundle([1, 'b', 2.0]).get_actual_schema()
        ok_(schema == {0: int, 1: str, 2: float})


class IdentityBundle_Test(object):
    """
    Simple tests on IdentityBundle
    """

    def iter_test(self):
        """
        Test IdentityBundle.iter
        """
        bundle = IdentityBundle(1.89)
        ok_(list(bundle) == [(Bundle.KeyFinal, 1.89)])

    def factory_test(self):
        """
        Test IdentityBundle.factory
        """
        bundle = IdentityBundle.factory({'whatever': 'hello'}.iteritems())
        ok_(bundle.obj == 'hello')
        assert_raises(FactoryError, IdentityBundle.factory, {}.iteritems())

    def get_schema_test(self):
        """
        Test IdentityBundle.get_schema
        """
        class MyBundle(IdentityBundle):
            klass = int
        ok_(MyBundle.get_schema() == {Bundle.KeyFinal: int})
        

class IterableBundle_Test(object):
    """
    Simple tests on IterableBundle
    """

    def iter_test(self):
        """
        Test IterableBundle.iter
        """
        bundle = IterableBundle(['a', 'b', 'c'])
        ok_(list(bundle) == [(0, 'a'), (1, 'b'), (2, 'c')])
        bundle = IterableBundle(('a',))
        ok_(list(bundle) == [(0, 'a')])
        bundle = IterableBundle([])
        ok_(list(bundle) == [])

    def factory_test(self):
        """
        Test IterableBundle.factory
        """
        bundle = IterableBundle.factory({0: 'aaa', 1: 'bbb', 2: 'ccc'}.iteritems())
        ok_(bundle.obj == ['aaa', 'bbb', 'ccc'])
        bundle = IterableBundle.factory({}.iteritems())
        ok_(bundle.obj == [])

    def get_schema_test(self):
        """
        Test IterableBundle.get_schema
        """
        class ListOfInt(IterableBundle):
            value_type = int
        ok_(ListOfInt.get_schema() == {Bundle.KeyAny: int})


class MappingBundle_Test(object):
    """
    Simple tests on MappingBundle
    """

    def iter_test(self):
        """
        Test MappingBundle.iter
        """
        bundle = MappingBundle({"a": "aaa", "b": 2, "cc": 3})
        ok_(set(bundle) == set([("a", "aaa"), ("b", 2), ("cc", 3)]))
        bundle = MappingBundle({})
        ok_(list(bundle) == [])

    def factory_test(self):
        """
        Test MappingBundle.factory
        """
        bundle = MappingBundle.factory({'a': 'aaa', 1: 'bbb', 'c': 'ccc'}.iteritems())
        ok_(bundle.obj == {'a': 'aaa', 1: 'bbb', 'c': 'ccc'})
        bundle = MappingBundle.factory({}.iteritems())
        ok_(bundle.obj == {})

    def get_schema_test(self):
        """
        Test MappingBundle.get_schema
        """
        class MappingOfInt(MappingBundle):
            value_type = int
        ok_(MappingOfInt.get_schema() == {Bundle.KeyAny: int})


class ObjectBundle_Test(object):
    """
    Tests for the ObjectBundle class
    """

    def setUp(self):
        class AnObject(object): pass
        self.AnObject = AnObject

    def get_schema_test(self):
        """
        Test ObjectBundle.get_schema
        """
        # provided schema
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'a': int, 'b': str}
        ok_(ObjectWithSchema.get_schema() == {'a': int, 'b': str})
        # with exclude
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'a': int, 'b': str}
            exclude = ['a']
        ok_(ObjectWithSchema.get_schema() == {'b': str})
        # default schema
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'b': unicode, 'c': float})
        # default schema + exclude
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            exclude = ['b', 'c', 'd']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float})
        # default schema + extra_schema
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'a': unicode, 'd': str}
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': unicode, 'b': unicode, 'c': float, 'd': str})
        # default schema + extra_schema + exclude
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'a': unicode, 'd': str, 'e': int}
            exclude = ['d', 'a', 'b']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'c': float, 'e': int})
        # default schema + include
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            include = ['a', 'b']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'b': unicode})
        # default schema + extra_schema + include
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'d': str}
            include = ['a', 'd']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'd': str})
        # default schema + extra_schema + exclude + include
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'d': str, 'e': int}
            include = ['a', 'b', 'e']
            exclude = ['a']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'b': unicode, 'e': int})

    def getattr_test(self):
        """
        Test ObjectBundle.getattr
        """
        class AnObjectBundle(ObjectBundle):
            klass = self.AnObject
            def get_a(self):
                return 'blabla'
        obj = self.AnObject()
        obj.b = 'bloblo'
        bundle = AnObjectBundle(obj)
        ok_(bundle.getattr('a') == 'blabla')
        ok_(bundle.getattr('b') == 'bloblo')
                
    def setattr_test(self):
        """
        Test ObjectBundle.setattr
        """
        class AnObjectBundle(ObjectBundle):
            klass=self.AnObject
            def set_a(self, value):
                self.obj.a = 'bloblo'
        obj = self.AnObject()
        bundle = AnObjectBundle(obj)
        bundle.setattr('a', 'blibli')
        bundle.setattr('b', 'blabla')
        ok_(obj.a == 'bloblo')
        ok_(obj.b == 'blabla')
