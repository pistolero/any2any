import datetime

from nose.tools import assert_raises, ok_
from any2any.base import *
from any2any.utils import *
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


class ListToList_Test(Container_Test):
    """
    Tests for ListToList
    """

    def call_test(self):
        """
        Test call
        """
        cast = ListToList()
        a_list = [1, 'a']
        other_list = cast.call(a_list)
        ok_(other_list == a_list)
        ok_(not other_list is a_list)

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for the list elements
        """
        cast = ListToList(
            mm_to_cast={
                Mm(int, object): self.MyCast(msg='an int'),
                Mm(str, object): self.MyCast(msg='a str'),
            },
            key_to_cast={2: self.MyCast(msg='index 2')}
        )
        ok_(cast.call([1, '3by', 78]) == ['an int 1', 'a str 3by', 'index 2 78'])


class DictToDict_Test(Container_Test):
    """
    Tests for DictToDict
    """

    def call_test(self):
        """
        Test call
        """
        a_dict = {1: 78, 'a': 'testi', 'b': 1.89}
        cast = DictToDict()
        other_dict = cast.call(a_dict)
        ok_(other_dict == a_dict)
        ok_(not other_dict is a_dict)

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for the dict elements
        """
        cast = DictToDict(
            mm_to_cast={Mm(int, object): self.MyCast(msg='an int'),},
            key_to_cast={'a': self.MyCast(msg='index a'),},
        )
        ok_(cast.call({1: 78, 'a': 'testi', 'b': 1}) == {1: 'an int 78', 'a': 'index a testi', 'b': 'an int 1'})


class ObjectToDict_Test(Container_Test):
    """
    Tests for ObjectToDict
    """

    def setUp(self):
        super(ObjectToDict_Test, self).setUp()
        class Object(object): pass
        self.Object = Object

    def call_test(self):
        """
        Test call
        """
        obj = self.Object() ; obj.a1 = 90 ; obj.blabla = 'coucou'
        cast = ObjectToDict()
        ok_(cast.call(obj) == {'a1': 90, 'blabla': 'coucou'})

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for attributes
        """
        obj = self.Object() ; obj.a1 = 90 ; obj.blabla = 'coucou' ; obj.bb = 'bibi'
        cast = ObjectToDict(
            mm_to_cast={Mm(int, object): self.MyCast(msg='an int'),},
            key_to_cast={'bb': self.MyCast(msg='index bb'),},
        )
        ok_(cast.call(obj) == {'a1': 'an int 90', 'blabla': 'coucou', 'bb': 'index bb bibi'})

    def virtual_attr_test(self):
        """
        Test serialize virtual attribute from object
        """
        obj = self.Object() ; obj.a = 90
        def get_my_virtual_attr(obj, name):
            return 'virtual %s' % obj.a
        cast = ObjectToDict(
            attrname_to_getter={'virtual_a': get_my_virtual_attr},
            include=['a', 'virtual_a'],
        )
        ok_(cast.call(obj) == {'a': 90, 'virtual_a': 'virtual 90'})


class DictToObject_Test(Container_Test):
    """
    Tests for DictToObject
    """

    def setUp(self):
        super(DictToObject_Test, self).setUp()
        class Object(object): pass
        self.Object = Object

    def call_test(self):
        """
        Test call
        """
        cast = DictToObject(to=self.Object)
        obj = cast.call({'a1': 90, 'blabla': 'coucou'})
        ok_(isinstance(obj, self.Object))
        ok_(obj.a1 == 90)
        ok_(obj.blabla == 'coucou')

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for attributes
        """
        cast = DictToObject(
            to=self.Object,
            mm_to_cast={Mm(int, object): self.MyCast(msg='an int'),},
            key_to_cast={'bb': self.MyCast(msg='index bb'),},
        )
        obj = cast.call({'a1': 90, 'blabla': 'coucou', 'bb': 'bibi'})
        ok_(isinstance(obj, self.Object))
        ok_(obj.a1 == 'an int 90')
        ok_(obj.blabla == 'coucou')
        ok_(obj.bb == 'index bb bibi')

    def virtual_attr_test(self):
        """
        Test set attribute to object
        """
        def set_my_virtual_attr(obj, name, value):
            obj.virt1 = value
            obj.virt2 = value
        cast = DictToObject(
            to=self.Object,
            attrname_to_setter={'a': set_my_virtual_attr},
        )
        obj = cast.call({'a': 90})
        ok_(isinstance(obj, self.Object))
        ok_(obj.virt1 == 90)
        ok_(obj.virt2 == 90)


class DateTimeToDict_Test(object):
    """
    Tests for DateTimeToDict
    """

    def call_test(self):
        """
        Test call for DateTimeToDict.
        """
        cast = DateTimeToDict()
        ok_(cast(datetime.datetime(year=1986, month=12, day=8)) == {
            'year': 1986,
            'month': 12,
            'day': 8,
            'hour': 0,
            'minute': 0,
            'second': 0,
            'microsecond': 0,
        })
        ok_(cast(datetime.datetime(year=10, month=11, day=1, microsecond=8)) == {
            'year': 10,
            'month': 11,
            'day': 1,
            'hour': 0,
            'minute': 0,
            'second': 0,
            'microsecond': 8,
        })


class DateToDict_Test(object):
    """
    Tests for DateToDict
    """

    def call_test(self):
        """
        Test call for DateToDict.
        """
        cast = DateToDict()
        ok_(cast(datetime.date(year=19, month=11, day=28)) == {
            'year': 19,
            'month': 11,
            'day': 28,
        })


class DictToDateTime_Test(object):
    """
    Tests for DictToDateTime
    """

    def call_test(self):
        """
        Test call for DictToDateTime.
        """
        cast = DictToDateTime()
        ok_(cast({
            'year': 1986,
            'month': 12,
            'day': 8,
            'hour': 0,
            'minute': 0,
            'second': 0,
            'microsecond': 0,
        }) == datetime.datetime(year=1986, month=12, day=8))
        ok_(cast({
            'year': 10,
            'month': 11,
            'day': 1,
            'hour': 0,
            'minute': 0,
            'second': 0,
            'microsecond': 8,
        }) == datetime.datetime(year=10, month=11, day=1, microsecond=8))


class DictToDate_Test(object):
    """
    Tests for DictToDate
    """

    def call_test(self):
        """
        Test call for DictToDate.
        """
        cast = DictToDate()
        ok_(cast({
            'year': 19,
            'month': 11,
            'day': 28,
        }) == datetime.date(year=19, month=11, day=28))


class ConcatDict_Test(object):
    """
    Tests for ConcatDict
    """

    def call_test(self):
        """
        Test call for ConcatDict
        """
        DictOfStr = ContainerType(dict, value_type=str)
        cast0 = DictToDict()
        cast1 = DictToDict(to=DictOfStr, value_cast=ToType())
        cast = ConcatDict(key_to_route={'a': 1, 'b': 0, 'c': 1}, operands=[cast0, cast1])
        print cast({
            'a': 987, 'b': 88, 'c': 34
        }), cast0.value_cast
        ok_(cast({
            'a': 987, 'b': 88, 'c': 34
        }) == {'a': '987', 'b': 88, 'c': '34'})
