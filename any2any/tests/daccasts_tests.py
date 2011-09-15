# -*- coding: utf-8 -*-
from nose.tools import assert_raises, ok_
from any2any.daccasts import *
from any2any.base import Cast
from any2any.utils import Spz

class FromDictToDict(ToMapping, CastItems, FromMapping):

    defaults = dict(to=dict)

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
        
class ObjectType_Test(object):
    """
    Test ObjectType
    """

    def setUp(self):
        class AnObject(object): pass
        self.AnObject = AnObject
        class AnObjectType(ObjectType):
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        self.AnObjectType = AnObjectType

    def get_class_test(self):
        """
        Test ObjectType.get_class and ObjectType.get_schema
        """
        # provided schema
        obj_type = ObjectType(self.AnObject, schema={'a': int, 'b': str})
        ok_(obj_type.get_schema() == {'a': int, 'b': str})
        ok_(obj_type.get_class('a') == int)
        ok_(obj_type.get_class('b') == str)
        assert_raises(KeyError, obj_type.get_class, 'c')
        # default schema
        obj_type = self.AnObjectType(self.AnObject)
        ok_(obj_type.get_schema() == {'a': float, 'b': unicode, 'c': float})
        ok_(obj_type.get_class('a') == float)
        ok_(obj_type.get_class('b') == unicode)
        ok_(obj_type.get_class('c') == float)
        assert_raises(KeyError, obj_type.get_class, 'd')

ListOfObjects = ContainerType(list, value_type=object)
ListOfStr = ContainerType(list, value_type=str)
ListOfInt = ContainerType(list, value_type=int)

class ContainerType_Test(object):
    """
    Test ContainerType
    """

    def issubclass_test(self):
        """
        Tests for isubclass with ContainerType
        """
        # Nested specializations
        ok_(Spz.issubclass(
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfStr
            )),
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            ))
        ))
        ok_(not Spz.issubclass(
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            )),
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfStr
            ))
        ))
        ok_(Spz.issubclass(
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            )),
            ContainerType(list, value_type=ContainerType(
                list, value_type=list
            ))
        ))
        ok_(Spz.issubclass(
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            )),
            list
        ))
        ok_(Spz.issubclass(
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            )),
            ContainerType(list, value_type=ListOfObjects)
        ))
        ok_(not Spz.issubclass(
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            )),
            ContainerType(list, value_type=ListOfInt)
        ))
    
