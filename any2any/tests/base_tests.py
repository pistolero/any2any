# -*- coding: utf-8 -*-
from any2any.base import *
from nose.tools import assert_raises, ok_

class BaseCast_subclassing_Test(object):
    """
    Testing subclassing Cast
    """
    def wrappers_test(self):
        """
        Test that metaclass wrappers work as expected
        """
        memory = []
        class Parent(BaseCast):
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

    def settings_inherit_test(self):
        """
        Test that when subclassing settings inherit as expected
        """
        class Parent(BaseCast):
            set1 = Setting(default=1)
            set2 = Setting(default={1: 8})
            set3 = Setting(default=8)
            set4 = Setting(default='coucou')
        class Parent1(Parent):
            set3 = Setting(default=8)
        class Parent2(Parent):
            set1 = Setting(default=5)
            set3 = Setting(default=10)
            set5 = Setting(default='blabla')
        class Child(Parent1, Parent2):
            set2 = ViralDictSetting(default={'a': 9})

        ok_(set(Child._meta.settings_dict.keys()) == set(['set1', 'set2', 'set3', 'set4', 'set5']))
        ok_(Child._meta.settings_dict['set1'].default == 1)
        ok_(Child._meta.settings_dict['set2'].default == {1: 8, 'a': 9})
        ok_(not Child._meta.settings_dict['set2'].default is Parent._meta.settings_dict['set2'].default)
        ok_(Child._meta.settings_dict['set3'].default == 8)
        ok_(Child._meta.settings_dict['set4'].default == 'coucou')
        ok_(Child._meta.settings_dict['set5'].default == 'blabla')

class BaseCast_instantiate_test(object):

    def setUp(self):
        class StrSetting(Setting):
            def get(self, instance):
                return str(super(StrSetting, self).get(instance))
        class DictSetting(Setting):
            def customize(self, instance, value):
                new_value = dict(self.get(instance), **value)
                self.set(instance, new_value)
                
        class MyCast(BaseCast):
            set1 = ViralSetting(default=1)
            set2 = DictSetting(default={1: 8})
            set3 = Setting(default=8)
            set4 = StrSetting(default='coucou')
            def call(self, inpt):
                return inpt
        self.MyCast = MyCast 

    def instantiate_test(self):
        """
        Test that defaults and settings get set right on BaseCast._init__
        """
        my_cast = self.MyCast()
        ok_(my_cast._settings == {'set1': 1, 'set2': {1: 8}, 'set3': 8, 'set4': 'coucou'})
        my_cast = self.MyCast(set1=999, set4=12)
        ok_(my_cast._settings == {'set1': 999, 'set2': {1: 8}, 'set3': 8, 'set4': 12})

    def iter_settings_test(self):
        """
        Test BaseCast.iter_settings
        """
        my_cast = self.MyCast()
        ok_(dict(my_cast.iter_settings()) == {'set1': 1, 'set2': {1: 8}, 'set3': 8, 'set4': 'coucou'})
        my_cast = self.MyCast(set1=999, set4=66)
        ok_(dict(my_cast.iter_settings()) == {'set1': 999, 'set2': {1: 8}, 'set3': 8, 'set4': '66'})

    def customize_cast_test(self):
        """
        Test BaseCast.customize
        """
        cast1 = self.MyCast(set1=1, set2={1: 1, 2: 2}, set3=1)
        cast2 = self.MyCast(set1=2, set2={2: 3, 3: 3}, set3=2)
        cast1.customize(cast2)
        ok_(cast1.set1 == 2) # viral setting
        ok_(cast1.set2 == {1: 1, 2: 3, 3: 3}) # dict setting
        ok_(cast1.set3 == 1) # normal setting

    def copy_cast_test(self):
        """
        Test copying cast
        """
        cast = self.MyCast(set2={1: 1}, set3=123, set4=11)
        copied_cast = copy.copy(cast)
        ok_(copied_cast.set1 == 1)
        ok_(copied_cast.set2 == {1: 1})
        ok_(not copied_cast.set2 is cast.set2)
        ok_(copied_cast.set3 == 123)
        ok_(copied_cast.set4 == '11')
