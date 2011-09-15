import datetime

from nose.tools import assert_raises, ok_
from any2any.base import *
from any2any.utils import *
from any2any.simple import *
from any2any.daccasts import ObjectType

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


class IterableToIterable_Test(Container_Test):
    """
    Tests for IterableToIterable
    """

    def call_test(self):
        """
        Test call
        """
        cast = IterableToIterable(to=list)
        a_list = [1, 'a']
        other_list = cast.call(a_list)
        ok_(other_list == a_list)
        ok_(not other_list is a_list)

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for the list elements
        """
        cast = IterableToIterable(
            to=list,
            mm_to_cast={
                Mm(from_=int): self.MyCast(msg='an int'),
                Mm(from_=str): self.MyCast(msg='a str'),
            },
            key_to_cast={2: self.MyCast(msg='index 2')}
        )
        ok_(cast.call([1, '3by', 78]) == ['an int 1', 'a str 3by', 'index 2 78'])


class MappingToMapping_Test(Container_Test):
    """
    Tests for MappingToMapping
    """

    def call_test(self):
        """
        Test call
        """
        a_dict = {1: 78, 'a': 'testi', 'b': 1.89}
        cast = MappingToMapping(to=dict)
        other_dict = cast.call(a_dict)
        ok_(other_dict == a_dict)
        ok_(not other_dict is a_dict)

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for the dict elements
        """
        cast = MappingToMapping(
            to=dict,
            mm_to_cast={Mm(from_=int): self.MyCast(msg='an int'),},
            key_to_cast={'a': self.MyCast(msg='index a'),},
        )
        ok_(cast.call({1: 78, 'a': 'testi', 'b': 1}) == {1: 'an int 78', 'a': 'index a testi', 'b': 'an int 1'})


class ObjectToMapping_Test(Container_Test):
    """
    Tests for ObjectToMapping
    """

    def setUp(self):
        super(ObjectToMapping_Test, self).setUp()
        class Object(object): pass
        self.Object = Object

    def call_test(self):
        """
        Test call
        """
        obj_type = ObjectType(self.Object, schema={'a1': int, 'blabla': str})
        obj = self.Object() ; obj.a1 = 90 ; obj.blabla = 'coucou'
        cast = ObjectToMapping(from_=obj_type, to=dict)
        ok_(cast.call(obj) == {'a1': 90, 'blabla': 'coucou'})

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for attributes
        """
        obj_type = ObjectType(self.Object, schema={'a1': int, 'blabla': str, 'bb': str})
        obj = self.Object() ; obj.a1 = 90 ; obj.blabla = 'coucou' ; obj.bb = 'bibi'
        cast = ObjectToMapping(
            from_=obj_type,
            to=dict,
            mm_to_cast={Mm(from_=int): self.MyCast(msg='an int'),},
            key_to_cast={'bb': self.MyCast(msg='index bb'),},
        )
        ok_(cast.call(obj) == {'a1': 'an int 90', 'blabla': 'coucou', 'bb': 'index bb bibi'})

    def virtual_attr_test(self):
        """
        Test serialize virtual attribute from object
        """
        obj_type = ObjectType(self.Object, schema={'a': int, 'virtual_a': str})
        obj = self.Object() ; obj.a = 90
        def get_my_virtual_attr(obj, name):
            return 'virtual %s' % obj.a
        cast = ObjectToMapping(
            from_=obj_type,
            to=dict,
            attrname_to_getter={'virtual_a': get_my_virtual_attr},
        )
        ok_(cast.call(obj) == {'a': 90, 'virtual_a': 'virtual 90'})


class MappingToObject_Test(Container_Test):
    """
    Tests for MappingToObject
    """

    def setUp(self):
        super(MappingToObject_Test, self).setUp()
        class Object(object): pass
        self.Object = Object
        self.ObjectSchema = ObjectType(Object, schema={'a1': int, 'blabla': str, 'bb': str, 'a': object})

    def call_test(self):
        """
        Test call
        """
        cast = MappingToObject(to=self.ObjectSchema)
        obj = cast.call({'a1': 90, 'blabla': 'coucou'})
        ok_(isinstance(obj, self.Object))
        ok_(obj.a1 == 90)
        ok_(obj.blabla == 'coucou')

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for attributes
        """
        cast = MappingToObject(
            to=self.ObjectSchema,
            mm_to_cast={Mm(from_=int): self.MyCast(msg='an int'),},
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
        cast = MappingToObject(
            to=self.ObjectSchema,
            attrname_to_setter={'a': set_my_virtual_attr},
        )
        obj = cast.call({'a': 90})
        ok_(isinstance(obj, self.Object))
        ok_(obj.virt1 == 90)
        ok_(obj.virt2 == 90)

class ConcatMapping_Test(object):
    """
    Tests for ConcatMapping
    """

    def call_test(self):
        """
        Test call for ConcatMapping
        """
        DictOfStr = ContainerType(dict, value_type=str)
        cast0 = MappingToMapping(to=dict)
        cast1 = MappingToMapping(to=DictOfStr, value_cast=ToType())
        cast = ConcatMapping(key_to_route={'a': 1, 'b': 0, 'c': 1}, operands=[cast0, cast1], to=dict)
        ok_(cast({
            'a': 987, 'b': 88, 'c': 34
        }) == {'a': '987', 'b': 88, 'c': '34'})
