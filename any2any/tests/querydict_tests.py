from nose.tools import assert_raises, ok_
from any2any.querydictcast import DictFlatener

class DictFlatener_Test(object):
    """
    Tests for DictFlatener
    """

    def call_test(self):
        cast = DictFlatener(list_keys=['a_list', 'another_list'])
        ok_(cast({'a_list': [1, 2], 'a_normal_key': [1, 2, 3], 'another_list': []}) == {
            'a_list': [1, 2],
            'a_normal_key': 1,
            'another_list': []
        })
        ok_(cast({'a_list': [1], 'a_normal_key': []}) == {
            'a_list': [1],
            'a_normal_key': None,
        })


