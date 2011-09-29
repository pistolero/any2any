# -*- coding: utf-8 -*-
from any2any.base import *
from nose.tools import assert_raises, ok_

class CastSettings_Test(object):
    """
    Tests for CastSettings
    """

    def setUp(self):
        _meta = {'override': update_setting_cb, 'customize': update_setting_cb}
        self._meta = _meta
        self.settings = CastSettings(
            _meta={'a_setting': _meta},
            a_setting={'a': 1, 'b': 2},
            another=1,
            more={'c': 'C'},
        )

    def create_test(self):
        """
        Test CastSettings.__init__
        """
        #Valid settings
        ok_(self.settings._values == {
            'a_setting': {'a': 1, 'b': 2},
            'another': 1,
            'more': {'c': 'C'},
        })
        ok_(self.settings._meta == {
            'a_setting': self._meta,
            'another': {},
            'more': {},
        })

    def setitem_test(self):
        """
        Test CastSettings.__setitem__
        """
        # simple case
        self.settings['more'] = 'blabla'
        ok_(self.settings['more'] == 'blabla')
        # with type check
        self.settings['another'] = 590
        ok_(self.settings['another'] == 590)
        # unknown setting
        assert_raises(TypeError, self.settings.__setitem__, 'unknown_setting', 'bla')

    def override_test(self):
        """
        Test CastSettings.override
        """
        self.settings.override(CastSettings(
            a_setting={'a': 2, 'c': 3},
            moremore={'D': 'd'},
            _meta={'a_setting': {'bla': 'blo', 'customize': 'do_nothing'}, 'moremore': {1: 2}},
        ))
        ok_(self.settings._values['a_setting'] == {'a': 2, 'b': 2, 'c': 3})
        ok_(self.settings._values['moremore'] == {'D': 'd'})
        ok_(self.settings._values['more'] == {'c': 'C'})
        ok_(self.settings._meta == {
            'a_setting': {'override': update_setting_cb, 'customize': 'do_nothing', 'bla': 'blo'},
            'moremore': {1: 2},
            'more': {},
            'another': {},
        })

    def customize_test(self):
        """
        Test CastSettings.customize
        """
        self.settings.customize(CastSettings(
            a_setting={'a': 2, 'c': 3},
            moremore={'D': 'd'},
            _meta={'a_setting': {}, 'moremore': {1: 2}},
        ))
        ok_(self.settings._values['a_setting'] == {'a': 2, 'b': 2, 'c': 3})
        ok_(not 'moremore' in self.settings._values)
        ok_(self.settings._values['more'] == {'c': 'C'})
        ok_(self.settings._meta == {
            'a_setting': self._meta,
            'another': {},
            'more': {},
            'moremore': {1: 2}
        })

    def copy_test(self):
        """
        Test CastSettings.copy
        """
        settings_copy = copy.copy(self.settings)
        ok_(settings_copy._values == self.settings._values)
        ok_(not settings_copy._values is self.settings._values)
        ok_(settings_copy._meta == self.settings._meta)
        ok_(not settings_copy._meta is self.settings._meta)
        ok_(settings_copy._values['more'] is self.settings._values['more'])
        ok_(settings_copy._values['another'] is self.settings._values['another'])
        ok_(settings_copy._values['a_setting'] is self.settings._values['a_setting'])

