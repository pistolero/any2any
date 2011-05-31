# -*- coding: utf-8 -*-
from nose.tools import assert_raises, ok_
from any2any.containercast import ToDict, FromDict
from any2any.base import Cast

class FromDictToDict(ToDict, FromDict): pass

class ContainerCast_Test(object):
    """
    Tests for ContainerCast
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
        Test using the keys_cast item to cast all the keys.
        """
        class ToStr(Cast):
            def call(self, inpt):
                return str(inpt)

        to_dict_str_keys = FromDictToDict(value_cast=ToStr())
        cast = FromDictToDict(keys_cast=to_dict_str_keys)
        ok_(cast({1: 'bla', 2: 'bla', u'blo': None, 'coucou': [1]}) == {'1': 'bla', '2': 'bla', 'blo': None, 'coucou': [1]})
            
