import datetime

from nose.tools import assert_raises, ok_
from any2any import *
from any2any.stacks.basicstack import *

class MyCast(Cast):
    msg = Setting(default='')
    def call(self, inpt):
        return '%s %s' % (self.msg, inpt)

class Object(object): pass

class Identity_Test(object):
    """
    Tests for Identity
    """

    def call_test(self):
        """
        Test call
        """
        identity = Identity()
        ok_(identity(56) == 56)
        ok_(identity('aa') == 'aa')
        a_list = [1, 2]
        other_list = identity(a_list)
        ok_(other_list is a_list)


class IterableToIterable_Test(object):
    """
    Tests for IterableToIterable
    """

    def call_test(self):
        """
        Test call
        """
        cast = IterableToIterable(to=list, mm_to_cast={Mm(): Identity()})
        a_list = [1, 'a']
        other_list = cast(a_list)
        ok_(other_list == a_list)
        ok_(not other_list is a_list)

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for the list elements
        """
        cast = IterableToIterable(
            to=list,
            mm_to_cast={
                Mm(from_=int): MyCast(msg='an int'),
                Mm(from_=str): MyCast(msg='a str'),
            },
            key_to_cast={2: MyCast(msg='index 2')}
        )
        ok_(cast([1, '3by', 78]) == ['an int 1', 'a str 3by', 'index 2 78'])

class MappingToMapping_Test(object):
    """
    Tests for MappingToMapping
    """

    def call_test(self):
        """
        Test call
        """
        a_dict = {1: 78, 'a': 'testi', 'b': 1.89}
        cast = MappingToMapping(to=dict, mm_to_cast={Mm(): Identity()})
        other_dict = cast(a_dict)
        ok_(other_dict == a_dict)
        ok_(not other_dict is a_dict)

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for the dict elements
        """
        cast = MappingToMapping(
            to=dict,
            mm_to_cast={Mm(from_=int): MyCast(msg='an int'),},
            key_to_cast={'a': MyCast(msg='index a'),},
        )
        ok_(cast({1: 78, 'a': 'testi', 'b': 1}) == {1: 'an int 78', 'a': 'index a testi', 'b': 'an int 1'})

class ObjectToMapping_Test(object):
    """
    Tests for ObjectToMapping
    """

    def call_test(self):
        """
        Test call
        """
        class MyWrappedObject(WrappedObject):
            klass = Object
            extra_schema={'a1': int, 'blabla': str}

        obj = Object() ; obj.a1 = 90 ; obj.blabla = 'coucou'
        cast = ObjectToMapping(from_=MyWrappedObject, mm_to_cast={Mm(): Identity()}, to=dict)
        ok_(cast(obj) == {'a1': 90, 'blabla': 'coucou'})

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for attributes
        """
        class MyWrappedObject(WrappedObject):
            klass = Object
            extra_schema = {'a1': int, 'blabla': str, 'bb': str}

        obj = Object() ; obj.a1 = 90 ; obj.blabla = 'coucou' ; obj.bb = 'bibi'
        cast = ObjectToMapping(
            from_=MyWrappedObject,
            to=dict,
            mm_to_cast={Mm(): Identity(), Mm(from_=int): MyCast(msg='an int'),},
            key_to_cast={'bb': MyCast(msg='index bb'),},
        )
        ok_(cast(obj) == {'a1': 'an int 90', 'blabla': 'coucou', 'bb': 'index bb bibi'})

class MappingToObject_Test(object):
    """
    Tests for MappingToObject
    """

    def call_test(self):
        """
        Test call
        """
        class MyWrappedObject(WrappedObject):
            klass = Object
            extra_schema = extra_schema={'a1': int, 'blabla': str, 'bb': str, 'a': object}
            @classmethod
            def new(cls, *args, **kwargs):
                obj = super(MyWrappedObject, cls).new()
                for name, value in kwargs.items():
                    setattr(obj, name, value)
                return obj

        cast = MappingToObject(to=MyWrappedObject, mm_to_cast={Mm(): Identity()})
        obj = cast({'a1': 90, 'blabla': 'coucou'})
        ok_(isinstance(obj, Object))
        ok_(obj.a1 == 90)
        ok_(obj.blabla == 'coucou')

    def custom_cast_for_elems_test(self):
        """
        Test call, with a custom cast for attributes
        """
        class MyWrappedObject(WrappedObject):
            klass = Object
            extra_schema = extra_schema={'a1': int, 'blabla': str, 'bb': str, 'a': object}
            @classmethod
            def new(cls, *args, **kwargs):
                obj = super(MyWrappedObject, cls).new()
                for name, value in kwargs.items():
                    setattr(obj, name, value)
                return obj

        cast = MappingToObject(
            to=MyWrappedObject,
            mm_to_cast={Mm(): Identity(), Mm(from_=int): MyCast(msg='an int'),},
            key_to_cast={'bb': MyCast(msg='index bb'),},
        )
        obj = cast({'a1': 90, 'blabla': 'coucou', 'bb': 'bibi'})
        ok_(isinstance(obj, Object))
        ok_(obj.a1 == 'an int 90')
        ok_(obj.blabla == 'coucou')
        ok_(obj.bb == 'index bb bibi')

class BasicStack_Test(object):

    def call_test(self):
        """
        Test basic calls
        """
        stack = BasicStack()
        ok_(stack(1) == 1)
        ok_(stack('2') == '2')
        ok_(stack([1, 2, '3']) == [1, 2, '3'])
        stack = BasicStack(extra_mm_to_cast={Mm(from_any=int): ToType(to=str)})
        ok_(stack(1) == '1')
        ok_(stack('2') == '2')
        ok_(stack(2.0) == 2.0)
        ok_(stack([1, 5.01, '3']) == ['1', 5.01, '3'])
