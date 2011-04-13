from nose.tools import assert_raises, ok_
from any2any.base import *
from any2any.simple import *

class Identity_Test(object):
    """
    Tests for Identity
    """

    def call_test(self):
        """
        Test call
        """
        identity = Identity()
        ok_(identity.call(56) == 56)
        ok_(identity.call('aa') == 'aa')
        a_list = [1, 2]
        other_list = identity.call(a_list)
        ok_(other_list is a_list)

class Container_Test(object):

    def setUp(self):
        class MyCast(Cast):
            defaults = CastSettings(msg='')
            def call(self, inpt):
                return '%s %s' % (self.msg, inpt)
        self.MyCast = MyCast

class SequenceCast_Test(Container_Test):
    """
    Tests for SequenceCast
    """

    def call_test(self):
        """
        Test call
        """
        cast = SequenceCast()
        a_list = [1, 'a']
        other_list = cast.call(a_list)
        ok_(other_list == a_list)
        ok_(not other_list is a_list)

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for the list elements
        """
        cast = SequenceCast(
            mm_to_cast={
                Mm(int, object): self.MyCast(msg='an int'),
                Mm(str, object): self.MyCast(msg='a str'),
            },
            index_to_cast={2: self.MyCast(msg='index 2')}
        )
        ok_(cast.call([1, '3by', 78]) == ['an int 1', 'a str 3by', 'index 2 78'])

class MappingCast_Test(Container_Test):
    """
    Tests for MappingCast
    """

    def call_test(self):
        """
        Test call
        """
        a_dict = {1: 78, 'a': 'testi', 'b': 1.89}
        cast = MappingCast()
        other_dict = cast.call(a_dict)
        ok_(other_dict == a_dict)
        ok_(not other_dict is a_dict)

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for the list elements
        """
        cast = MappingCast(
            mm_to_cast={Mm(int, object): self.MyCast(msg='an int'),},
            index_to_cast={'a': self.MyCast(msg='index a'),},
        )

        ok_(cast.call({1: 78, 'a': 'testi', 'b': 1}) == {1: 'an int 78', 'a': 'index a testi', 'b': 'an int 1'})

