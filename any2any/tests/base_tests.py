# -*- coding: utf-8 -*-
from any2any.base import *
from nose.tools import assert_raises, ok_

class BaseCast_subclassing_test(object):
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

    def mixin_test(self):
        """
        Test that when subclassing mixing settings with non-Casts works
        """
        class Parent(BaseCast):
            set1 = Setting(default=1)
            set2 = Setting(default=1)
        class Mixin1(CastMixin):
            set2 = Setting(default=2)
            set3 = Setting(default=2)
        class Mixin2(CastMixin):
            set4 = Setting(default=2)
        class Mixin3(Mixin1): pass
        class Child1(Parent, Mixin1, Mixin2): pass
        class Child2(Mixin1, Parent, Mixin2): pass
        class Child3(Parent, Mixin3): pass

        ok_(set(Child1._meta.settings_dict.keys()) == set(['set1', 'set2', 'set3', 'set4']))
        ok_(Child1._meta.settings_dict['set1'].default == 1)
        ok_(Child1._meta.settings_dict['set2'].default == 1)
        ok_(set(Child2._meta.settings_dict.keys()) == set(['set1', 'set2', 'set3', 'set4']))
        ok_(Child2._meta.settings_dict['set1'].default == 1)
        ok_(Child2._meta.settings_dict['set2'].default == 2)
        ok_(set(Child3._meta.settings_dict.keys()) == set(['set1', 'set2', 'set3']))
        ok_(Child3._meta.settings_dict['set1'].default == 1)
        ok_(Child3._meta.settings_dict['set2'].default == 1)

    def settings_inherit_test(self):
        """
        Test that when subclassing settings inherit as expected
        """
        class DictSetting(Setting):
            def inherits(self, setting):
                self.default = dict(setting.default, **self.default)
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
            set2 = DictSetting(default={'a': 9})

        ok_(set(Child._meta.settings_dict.keys()) == set(['set1', 'set2', 'set3', 'set4', 'set5']))
        ok_(Child._meta.settings_dict['set1'].default == 1)
        ok_(Child._meta.settings_dict['set2'].default == {1: 8, 'a': 9})
        ok_(Child._meta.settings_dict['set3'].default == 8)
        ok_(Child._meta.settings_dict['set4'].default == 'coucou')
        ok_(Child._meta.settings_dict['set5'].default == 'blabla')

    def Meta_defaults_test(self):
        """
        Test Meta.defaults
        """
        class DictSetting(Setting):
            def inherits(self, setting):
                self.default = dict(setting.default, **self.default)
        class Parent(BaseCast):
            set1 = Setting(default=1)
            set2 = DictSetting(default={1: 1, 2: 2})
        class Child(Parent):
            class Meta:
                defaults = {
                    'set2': {1: 2, 3: 3}
                }
        ok_(Child._meta.settings_dict['set1'].default == 1)
        ok_(Child._meta.settings_dict['set2'].default == {1: 2, 2: 2, 3: 3})
        ok_(type(Child._meta.settings_dict['set2']) == DictSetting)

class BaseCast_instantiate_test(object):

    def setUp(self):
        class StrSetting(Setting):
            def get(self, instance):
                return str(super(StrSetting, self).get(instance))
        class DictSetting(Setting):
            def customize(self, instance, value):
                new_value = dict(self.get(instance), **value)
                self.set(instance, new_value)
        class IntSetting(Setting):
            def init(self, instance, value):
                try:
                    self.set(instance, int(value))
                except TypeError:
                    self.set(instance, value)
        class MyCast(BaseCast):
            set1 = ViralSetting(default=1)
            set2 = DictSetting(default={1: 8})
            set3 = Setting(default=8)
            set4 = StrSetting(default='coucou')
            set5 = IntSetting()
            def call(self, inpt):
                return inpt
        self.MyCast = MyCast 

    def instantiate_test(self):
        """
        Test that defaults and settings get set right on BaseCast._init__
        """
        my_cast = self.MyCast()
        ok_(my_cast._settings == {'set1': 1, 'set2': {1: 8}, 'set3': 8, 'set4': 'coucou', 'set5': None})
        my_cast = self.MyCast(set1=999, set4=12, set5='5')
        ok_(my_cast._settings == {'set1': 999, 'set2': {1: 8}, 'set3': 8, 'set4': 12, 'set5': 5})

    def iter_settings_test(self):
        """
        Test BaseCast.iter_settings
        """
        my_cast = self.MyCast()
        ok_(dict(my_cast.iter_settings()) == {'set1': 1, 'set2': {1: 8}, 'set3': 8, 'set4': 'coucou', 'set5': None})
        my_cast = self.MyCast(set1=999, set4=66)
        ok_(dict(my_cast.iter_settings()) == {'set1': 999, 'set2': {1: 8}, 'set3': 8, 'set4': '66', 'set5': None})

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
        ok_(copied_cast.set2 is cast.set2)
        ok_(copied_cast.set3 == 123)
        ok_(copied_cast.set4 == '11')

class Cast_test(object):
    """
    Test Cast
    """

    def setUp(self):
        class Identity(Cast):
            def call(self, inpt):
                return inpt
        class ToStr(Cast):
            def call(self, inpt):
                return str(inpt)
        self.Identity = Identity
        self.ToStr = ToStr

    def cast_for_test(self):
        """
        Test Cast.cast_for
        """
        cast = self.Identity(mm_to_cast={
            Mm(int): self.ToStr()
        })
        ok_(isinstance(cast.cast_for(Mm(int)), self.ToStr))
        ok_(isinstance(cast.cast_for(Mm(int, str)), self.ToStr))
        assert_raises(ValueError, cast.cast_for, Mm(str))
        cast = self.Identity(mm_to_cast={
            Mm(int): self.ToStr(),
            Mm(): self.Identity()
        })
        ok_(isinstance(cast.cast_for(Mm(int)), self.ToStr))
        ok_(isinstance(cast.cast_for(Mm(int, str)), self.ToStr))
        ok_(isinstance(cast.cast_for(Mm(str)), self.Identity))
        ok_(isinstance(cast.cast_for(Mm(str, int)), self.Identity))
        ok_(isinstance(cast.cast_for(Mm()), self.Identity))
