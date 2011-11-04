# -*- coding: utf-8 -*-
from nose.tools import assert_raises, ok_
from any2any.bundle import *
from any2any.cast import *


class BaseStrBundle(Bundle): pass
class IntBundle(Bundle): pass
class MyFloatBundle(Bundle):
    klass = float


class ValueInfo_test(object):

    def klass_test(self):
        """
        test ValueInfo.klass
        """
        value_info = ValueInfo(MyFloatBundle)
        ok_(value_info.klass == float)
        value_info = ValueInfo(str)
        ok_(value_info.klass == str)

    def lookup_with_test(self):
        """
        test ValueInfo.lookup_with
        """
        value_info = ValueInfo(int)
        ok_(value_info.lookup_with == (int,))
        value_info = ValueInfo(str, lookup_with=(float, int))
        ok_(value_info.lookup_with == (float, int))

    def new_test(self):
        """
        Test constructor
        """
        ok_(ValueInfo(Bundle.ValueUnknown) is Bundle.ValueUnknown)
        value_info = ValueInfo(int)
        ok_(ValueInfo(value_info) is value_info)
        ok_(not ValueInfo(int) is ValueInfo(int))
        ok_(not ValueInfo(MyFloatBundle) is ValueInfo(MyFloatBundle))

    def bundle_class_test(self):
        """
        test ValueInfo.bundle_class
        """
        bcm = {
            AllSubSetsOf(basestring): BaseStrBundle,
            AllSubSetsOf(list): IdentityBundle,
            Singleton(int): IntBundle,
        }
        # With a bundle class
        value_info = ValueInfo(BaseStrBundle)
        value_info.bundle_class_map = bcm
        ok_(issubclass(value_info.bundle_class, BaseStrBundle))
        # with a normal class
        value_info = ValueInfo(int)
        value_info.bundle_class_map = bcm
        ok_(issubclass(value_info.bundle_class, IntBundle))
        ok_(value_info.bundle_class.klass is int)
        value_info = ValueInfo(str, schema={'a': str})
        value_info.bundle_class_map = bcm
        ok_(issubclass(value_info.bundle_class, BaseStrBundle))
        ok_(value_info.bundle_class.klass is str)
        ok_(value_info.bundle_class.schema == {'a': str})
        # with provided lookup
        value_info = ValueInfo(tuple, lookup_with=(float, basestring, list))
        value_info.bundle_class_map = bcm
        ok_(issubclass(value_info.bundle_class, BaseStrBundle))
        ok_(value_info.bundle_class.klass is tuple)

    def schema_test(self):
        """
        test ValueInfo.schema
        """
        pass


class Bundle_Test(object):
    """
    Tests on Bundle
    """
    
    def setUp(self):
        class AnObject(object): pass
        self.AnObject = AnObject
        class SimpleBundle(Bundle):
            @classmethod
            def default_schema(cls):
                return {}
        self.SimpleBundle = SimpleBundle

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

    def get_schema_test(self):
        """
        Test Bundle.get_schema
        """
        # provided schema
        class ObjectWithSchema(self.SimpleBundle):
            klass = self.AnObject
            schema = {'a': int, 'b': str}
        ok_(ObjectWithSchema.get_schema() == {'a': int, 'b': str})
        # with exclude
        class ObjectWithSchema(self.SimpleBundle):
            klass = self.AnObject
            schema = {'a': int, 'b': str}
            exclude = ['a']
        ok_(ObjectWithSchema.get_schema() == {'b': str})
        # default schema
        class ObjectWithSchema(self.SimpleBundle):
            klass = self.AnObject
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'b': unicode, 'c': float})
        # default schema + exclude
        class ObjectWithSchema(self.SimpleBundle):
            klass = self.AnObject
            exclude = ['b', 'c', 'd']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float})
        # default schema + schema
        class ObjectWithSchema(self.SimpleBundle):
            klass = self.AnObject
            schema = {'a': unicode, 'd': str}
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': unicode, 'b': unicode, 'c': float, 'd': str})
        # default schema + schema + exclude
        class ObjectWithSchema(self.SimpleBundle):
            klass = self.AnObject
            schema = {'a': unicode, 'd': str, 'e': int}
            exclude = ['d', 'a', 'b']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'c': float, 'e': int})
        # default schema + include
        class ObjectWithSchema(self.SimpleBundle):
            klass = self.AnObject
            include = ['a', 'b']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'b': unicode})
        # default schema + schema + include
        class ObjectWithSchema(self.SimpleBundle):
            klass = self.AnObject
            schema = {'d': str}
            include = ['a', 'd']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'd': str})
        # default schema + schema + exclude + include
        class ObjectWithSchema(self.SimpleBundle):
            klass = self.AnObject
            schema = {'d': str, 'e': int}
            include = ['a', 'b', 'e']
            exclude = ['a']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'b': unicode, 'e': int})


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
