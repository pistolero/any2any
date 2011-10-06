# -*- coding: utf-8 -*-
from nose.tools import assert_raises, ok_
from any2any.daccasts import *
from any2any.base import Cast, Setting, ViralDictSetting, ToSetting
from any2any.utils import Wrap

# Casts for the tests 
class Identity(Cast):

    def call(self, inpt):
        return inpt

class FromDictToDict(FromMapping, CastItems, ToMapping, DivideAndConquerCast):
    to = ToSetting(default=dict)
    mm_to_cast = ViralDictSetting(default={Mm(): Identity()})

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
        
class ObjectWrap_Test(object):
    """
    Test ObjectWrap
    """

    def setUp(self):
        class AnObject(object): pass
        self.AnObject = AnObject
        class AnObjectWrap(ObjectWrap):
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
            def guess_class(self, key):
                try:
                    return {'mystery': float}[key]
                except KeyError:
                    return NotImplemented
        self.AnObjectWrap = AnObjectWrap

    def get_schema_test(self):
        """
        Test ObjectWrap.get_schema
        """
        # provided schema
        obj_type = ObjectWrap(self.AnObject, extra_schema={'a': int, 'b': str})
        ok_(obj_type.get_schema() == {'a': int, 'b': str})
        # with exclude
        obj_type = ObjectWrap(self.AnObject, extra_schema={'a': int, 'b': str}, exclude=['a'])
        ok_(obj_type.get_schema() == {'b': str})
        # default schema
        obj_type = self.AnObjectWrap(self.AnObject)
        ok_(obj_type.get_schema() == {'a': float, 'b': unicode, 'c': float})
        # default schema + exclude
        obj_type = self.AnObjectWrap(self.AnObject, exclude=['b', 'c', 'd'])
        ok_(obj_type.get_schema() == {'a': float})
        # default schema + extra_schema
        obj_type = self.AnObjectWrap(self.AnObject, extra_schema={'a': unicode, 'd': str})
        ok_(obj_type.get_schema() == {'a': unicode, 'b': unicode, 'c': float, 'd': str})
        # default schema + extra_schema + exclude
        obj_type = self.AnObjectWrap(self.AnObject, extra_schema={'a': unicode, 'd': str, 'e': int}, exclude=['d', 'a', 'b'])
        ok_(obj_type.get_schema() == {'c': float, 'e': int})
        # default schema + include
        obj_type = self.AnObjectWrap(self.AnObject, include=['a', 'b'])
        ok_(obj_type.get_schema() == {'a': float, 'b': unicode})
        # default schema + extra_schema + include
        obj_type = self.AnObjectWrap(self.AnObject, extra_schema={'d': str}, include=['a', 'd'])
        ok_(obj_type.get_schema() == {'a': float, 'd': str})
        # default schema + extra_schema + exclude + include
        obj_type = self.AnObjectWrap(self.AnObject, extra_schema={'d': str, 'e': int}, include=['a', 'b', 'e'], exclude=['a'])
        ok_(obj_type.get_schema() == {'b': unicode, 'e': int})

    def get_class_test(self):
        """
        Test ObjectWrap.get_class
        """
        # provided schema
        obj_type = ObjectWrap(self.AnObject, extra_schema={'a': int, 'b': str})
        ok_(obj_type.get_class('a') == int)
        ok_(obj_type.get_class('b') == str)
        assert_raises(KeyError, obj_type.get_class, 'c')
        # default schema
        obj_type = self.AnObjectWrap(self.AnObject)
        ok_(obj_type.get_class('a') == float)
        ok_(obj_type.get_class('b') == unicode)
        ok_(obj_type.get_class('c') == float)
        assert_raises(KeyError, obj_type.get_class, 'd')

    def getattr_test(self):
        """
        Test ObjectWrap.getattr
        """
        class AnObjectWrap(ObjectWrap):
            def get_a(self, obj):
                return 'blabla'
        obj_type = AnObjectWrap(self.AnObject)
        obj = self.AnObject()
        obj.b = 'bloblo'
        ok_(obj_type.getattr(obj, 'a') == 'blabla')
        ok_(obj_type.getattr(obj, 'b') == 'bloblo')
                
    def getattr_test(self):
        """
        Test ObjectWrap.setattr
        """
        class AnObjectWrap(ObjectWrap):
            def set_a(self, obj, value):
                obj.a = 'bloblo'
        obj_type = AnObjectWrap(self.AnObject)
        obj = self.AnObject()
        obj_type.setattr(obj, 'a', 'blibli')
        obj_type.setattr(obj, 'b', 'blabla')
        ok_(obj.a == 'bloblo')
        ok_(obj.b == 'blabla')

ListOfObjects = ContainerWrap(list, value_type=object)
ListOfStr = ContainerWrap(list, value_type=str)
ListOfInt = ContainerWrap(list, value_type=int)

class ContainerWrap_Test(object):
    """
    Test ContainerWrap
    """

    def issubclass_test(self):
        """
        Tests for isubclass with ContainerWrap
        """
        # Nested specializations
        ok_(Wrap.issubclass(
            ContainerWrap(list, value_type=ContainerWrap(
                list, value_type=ListOfStr
            )),
            ContainerWrap(list, value_type=ContainerWrap(
                list, value_type=ListOfObjects
            ))
        ))
        ok_(not Wrap.issubclass(
            ContainerWrap(list, value_type=ContainerWrap(
                list, value_type=ListOfObjects
            )),
            ContainerWrap(list, value_type=ContainerWrap(
                list, value_type=ListOfStr
            ))
        ))
        ok_(Wrap.issubclass(
            ContainerWrap(list, value_type=ContainerWrap(
                list, value_type=ListOfObjects
            )),
            ContainerWrap(list, value_type=ContainerWrap(
                list, value_type=list
            ))
        ))
        ok_(Wrap.issubclass(
            ContainerWrap(list, value_type=ContainerWrap(
                list, value_type=ListOfObjects
            )),
            list
        ))
        ok_(Wrap.issubclass(
            ContainerWrap(list, value_type=ContainerWrap(
                list, value_type=ListOfObjects
            )),
            ContainerWrap(list, value_type=ListOfObjects)
        ))
        ok_(not Wrap.issubclass(
            ContainerWrap(list, value_type=ContainerWrap(
                list, value_type=ListOfObjects
            )),
            ContainerWrap(list, value_type=ListOfInt)
        ))
    
