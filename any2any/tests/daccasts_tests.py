# -*- coding: utf-8 -*-
from nose.tools import assert_raises, ok_
from any2any.daccasts import ToMapping, FromMapping, CastItems, ContainerType
from any2any.base import Cast

class FromDictToDict(ToMapping, CastItems, FromMapping):

    defaults = dict(to=dict)

ListOfObjects = ContainerType(list, value_type=object)
ListOfStr = ContainerType(list, value_type=str)
ListOfInt = ContainerType(list, value_type=int)

class ContainerType_Test(object):
    """
    Tests for ContainerType
    """

    def issubclass_test(self):
        """
        Tests for ContainerSpecialization
        """
        # Nested specializations
        ok_(issubclass( 
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfStr
            )),
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            ))
        ))
        ok_(not issubclass(
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            )),
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfStr
            ))
        ))
        ok_(issubclass(
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            )),
            ContainerType(list, value_type=ContainerType(
                list, value_type=list
            ))
        ))
        ok_(issubclass(
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            )),
            list
        ))
        ok_(issubclass(
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            )),
            ContainerType(list, value_type=ListOfObjects)
        ))
        ok_(not issubclass(
            ContainerType(list, value_type=ContainerType(
                list, value_type=ListOfObjects
            )),
            ContainerType(list, value_type=ListOfInt)
        ))

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
            
