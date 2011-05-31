# -*- coding: utf-8 -*-
from any2any.base import *
from nose.tools import assert_raises, ok_

class Cast_subclassing_Test(object):
    """
    Testing subclassing Cast
    """
    def wrappers_test(self):
        """
        Test that metaclass wrappers work as expected
        """
        memory = []
        class Parent(Cast):
            def call(self, inpt):
                memory.append('Parent %s' % self._context['bla'])
        class Child(Parent):
            def call(self, inpt):
                self._context['bla'] = 'woohoo'
                # When calling like that, the wrapping of Parent.call should be inneficient
                # and therefore, the context should not be reset ...
                super(Child, self).call(inpt)
                #    and not be reset after the parent operation was called
                memory.append('Child %s' % self._context['bla'])
        
        Child().call(1)
        ok_(memory == ['Parent woohoo', 'Child woohoo'])

    def settings_override_test(self):
        """
        Test that when subclassing settings are override as expected
        """
        class Parent(Cast):
            defaults = CastSettings(
                set1 = 1,
                set2 = {1: 8},
                set3 = 8,
                set4 = 'coucou'
            )
        class Parent1(Parent):
            defaults = CastSettings(
                set3 = 9,
            )
        class Parent2(Parent):
            defaults = CastSettings(
                set1 = 5,
                set3 = 10,
                set5 = 'blabla'
            )
        class Child(Parent1, Parent2):
            defaults = CastSettings(
                set2 = {'a': 9},
                _schema = {'set2': {'override': 'update_item'}},
            )
        ok_(Child.defaults['set1'] == 1)
        ok_(Child.defaults['set2'] == {1: 8, 'a': 9})
        ok_(Child.defaults['set3'] == 9)
        ok_(Child.defaults['set4'] == 'coucou')
        ok_(Child.defaults['set5'] == 'blabla')

