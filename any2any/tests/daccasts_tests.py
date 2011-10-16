# -*- coding: utf-8 -*-
from nose.tools import assert_raises, ok_
from any2any.daccasts import *
from any2any.base import Cast, Setting, ToSetting
from any2any.utils import Wrapped

# Casts for the tests 
class Identity(Cast):

    def call(self, inpt):
        return inpt

class FromDictToDict(FromMapping, CastItems, ToMapping, DivideAndConquerCast):
    to = ToSetting(default=dict)

    class Meta:
        defaults = {
            'mm_to_cast': {Mm(): Identity()}
        }

class CastItems_Test(object):
    """
    Test mixin CastItems
    """

    def strip_item_test(self):
        """
        Test stripping some items from the output
        """
        # Dictionary stripping the items with value 'None'
        class DictStrippingNoneVal(FromDictToDict):
            def strip_item(self, key, value):
                if value == None:
                    return True

        cast = DictStrippingNoneVal()
        ok_(cast({1: None, 2: 'bla', 3: None, 4: []}) == {2: 'bla', 4: []})
        
        # Dictionary stripping items whose key is not a string
        class DictStrippingNonStrKeys(FromDictToDict):
            def strip_item(self, key, value):
                if not isinstance(key, str):
                    return True

        cast = DictStrippingNonStrKeys()
        ok_(cast({1: 'will be stripped', '2': 'bla', u'will be stripped': None, 'coucou': [1]}) == {'2': 'bla', 'coucou': [1]})

    def cast_keys_test(self):
        """
        Test using the key_cast item to cast all the keys.
        """
        class ToStr(Cast):
            def call(self, inpt):
                return str(inpt)

        cast = FromDictToDict(key_cast=ToStr())
        ok_(cast({1: 'bla', 2: 'bla', u'blo': None, 'coucou': [1]}) == {'1': 'bla', '2': 'bla', 'blo': None, 'coucou': [1]})
        
class WrappedObject_Test(object):
    """
    Test WrappedObject
    """

    def setUp(self):
        class AnObject(object): pass
        self.AnObject = AnObject

    def get_schema_test(self):
        """
        Test WrappedObject.get_schema
        """
        # provided schema
        class ObjectWithSchema(WrappedObject):
            klass = self.AnObject
            extra_schema = {'a': int, 'b': str}
        ok_(ObjectWithSchema.get_schema() == {'a': int, 'b': str})
        # with exclude
        class ObjectWithSchema(WrappedObject):
            klass = self.AnObject
            extra_schema = {'a': int, 'b': str}
            exclude = ['a']
        ok_(ObjectWithSchema.get_schema() == {'b': str})
        # default schema
        class ObjectWithSchema(WrappedObject):
            klass = self.AnObject
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'b': unicode, 'c': float})
        # default schema + exclude
        class ObjectWithSchema(WrappedObject):
            klass = self.AnObject
            exclude = ['b', 'c', 'd']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float})
        # default schema + extra_schema
        class ObjectWithSchema(WrappedObject):
            klass = self.AnObject
            extra_schema = {'a': unicode, 'd': str}
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': unicode, 'b': unicode, 'c': float, 'd': str})
        # default schema + extra_schema + exclude
        class ObjectWithSchema(WrappedObject):
            klass = self.AnObject
            extra_schema = {'a': unicode, 'd': str, 'e': int}
            exclude = ['d', 'a', 'b']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'c': float, 'e': int})
        # default schema + include
        class ObjectWithSchema(WrappedObject):
            klass = self.AnObject
            include = ['a', 'b']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'b': unicode})
        # default schema + extra_schema + include
        class ObjectWithSchema(WrappedObject):
            klass = self.AnObject
            extra_schema = {'d': str}
            include = ['a', 'd']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'd': str})
        # default schema + extra_schema + exclude + include
        class ObjectWithSchema(WrappedObject):
            klass = self.AnObject
            extra_schema = {'d': str, 'e': int}
            include = ['a', 'b', 'e']
            exclude = ['a']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'b': unicode, 'e': int})

    def get_class_test(self):
        """
        Test WrappedObject.get_class
        """
        # provided schema
        class ObjectWithSchema(WrappedObject):
            klass = self.AnObject
            extra_schema = {'a': int, 'b': str}
        ok_(ObjectWithSchema.get_class('a') == int)
        ok_(ObjectWithSchema.get_class('b') == str)
        assert_raises(KeyError, ObjectWithSchema.get_class, 'c')
        # default schema
        class ObjectWithSchema(WrappedObject):
            klass = self.AnObject
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_class('a') == float)
        ok_(ObjectWithSchema.get_class('b') == unicode)
        ok_(ObjectWithSchema.get_class('c') == float)
        assert_raises(KeyError, ObjectWithSchema.get_class, 'd')

    def getattr_test(self):
        """
        Test WrappedObject.getattr
        """
        class WrappedAnObject(WrappedObject):
            klass = self.AnObject
            @classmethod
            def get_a(self, obj):
                return 'blabla'
        obj = self.AnObject()
        obj.b = 'bloblo'
        ok_(WrappedAnObject.getattr(obj, 'a') == 'blabla')
        ok_(WrappedAnObject.getattr(obj, 'b') == 'bloblo')
                
    def setattr_test(self):
        """
        Test WrappedObject.setattr
        """
        class WrappedAnObject(WrappedObject):
            klass=self.AnObject
            @classmethod
            def set_a(self, obj, value):
                obj.a = 'bloblo'
        obj = self.AnObject()
        WrappedAnObject.setattr(obj, 'a', 'blibli')
        WrappedAnObject.setattr(obj, 'b', 'blabla')
        ok_(obj.a == 'bloblo')
        ok_(obj.b == 'blabla')
            

class WrappedContainer_Test(object):
    """
    Test WrappedContainer
    """

    def issubclass_test(self):
        """
        Tests for isubclass with WrappedContainer
        """
        class ListOfObject(WrappedContainer):
            klass = list
            value_type = object

        class ListOfStr(WrappedContainer):
            klass = list
            value_type = str

        class ListOfListOfStr(WrappedContainer): 
            klass = list
            value_type = ListOfStr

        class ListOfListOfObject(WrappedContainer): 
            klass = list
            value_type = ListOfObject

        class ListOfListOfListOfObject(WrappedContainer): 
            klass = list
            value_type = ListOfListOfObject

        class ListOfListOfListOfStr(WrappedContainer): 
            klass = list
            value_type = ListOfListOfStr

        class ListOfList(WrappedContainer): 
            klass = list
            value_type = list

        class ListOfListOfList(WrappedContainer): 
            klass = list
            value_type = ListOfList

        ok_(Wrapped.issubclass(ListOfListOfListOfStr, ListOfListOfListOfObject))
        ok_(not Wrapped.issubclass(ListOfListOfListOfObject, ListOfListOfListOfStr))
        ok_(Wrapped.issubclass(ListOfListOfListOfObject, ListOfListOfList))
        ok_(Wrapped.issubclass(ListOfListOfListOfObject, list))
        ok_(Wrapped.issubclass(ListOfListOfListOfObject, ListOfListOfObject))
        ok_(not Wrapped.issubclass(ListOfListOfListOfObject, ListOfListOfStr))
    
