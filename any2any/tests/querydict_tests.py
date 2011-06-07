from nose.tools import assert_raises, ok_
from any2any.querydictcast import QueryDictCast

class QueryDictCast_Test(object):
    """
    Tests for QueryDictCast
    """

    def call_test(self):
        cast = QueryDictCast(list_keys=['a_list', 'another_list'])
        ok_(cast({'a_list': [1, 2], 'a_normal_key': [1, 2, 3], 'another_list': []}) == {
            'a_list': [1, 2],
            'a_normal_key': 1,
            'another_list': []
        })
        ok_(cast({'a_list': [1], 'a_normal_key': []}) == {
            'a_list': [1],
            'a_normal_key': None,
        })


