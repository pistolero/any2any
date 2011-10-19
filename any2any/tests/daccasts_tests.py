# -*- coding: utf-8 -*-
from nose.tools import assert_raises, ok_
from any2any.daccasts import *
from any2any.base import Cast, Setting, ToSetting
from any2any.utils import WrappedObject

# Casts for the tests 
class Identity(Cast):

    def call(self, inpt):
        return inpt

class DictToDict(FromMapping, CastItems, ToMapping, DivideAndConquerCast):

    class Meta:
        defaults = {
            'mm_to_cast': {Mm(): Identity()},
            'to': dict
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
        class DictStrippingNoneVal(DictToDict):
            def strip_item(self, key, value):
                if value == None:
                    return True

        cast = DictStrippingNoneVal()
        ok_(cast({1: None, 2: 'bla', 3: None, 4: []}) == {2: 'bla', 4: []})
        
        # Dictionary stripping items whose key is not a string
        class DictStrippingNonStrKeys(DictToDict):
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

        cast = DictToDict(key_cast=ToStr())
        ok_(cast({1: 'bla', 2: 'bla', u'blo': None, 'coucou': [1]}) == {'1': 'bla', '2': 'bla', 'blo': None, 'coucou': [1]})
            

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

        ok_(WrappedObject.issubclass(ListOfListOfListOfStr, ListOfListOfListOfObject))
        ok_(not WrappedObject.issubclass(ListOfListOfListOfObject, ListOfListOfListOfStr))
        ok_(WrappedObject.issubclass(ListOfListOfListOfObject, ListOfListOfList))
        ok_(WrappedObject.issubclass(ListOfListOfListOfObject, list))
        ok_(WrappedObject.issubclass(ListOfListOfListOfObject, ListOfListOfObject))
        ok_(not WrappedObject.issubclass(ListOfListOfListOfObject, ListOfListOfStr))
    
