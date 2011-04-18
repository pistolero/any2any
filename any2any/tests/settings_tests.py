from any2any.base import *
from nose.tools import assert_raises, ok_


class CastSettings_Test(object):
    """
    Tests for CastSettings
    """

    def setUp(self):
        self.settings = CastSettings(
            _schema={
                'a_setting': {'override': 'update_item'},
                'another': {'type': int},
            },
            a_setting={'a': 1, 'b': 2},
            another=1,
            more={'c': 'C'},
        )

    def init_test(self):
        """
        Test CastSettings.__init__
        """
        #Valid settings
        ok_(self.settings._values == {
            'a_setting': {'a': 1, 'b': 2},
            'another': 1,
            'more': {'c': 'C'},
        })
        ok_(self.settings._schema == {
            'a_setting': {'override': 'update_item'},
            'another': {'type': int},
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
        assert_raises(TypeError, self.settings.__setitem__, ('another', 'bla'))
        # unknown setting
        assert_raises(TypeError, self.settings.__setitem__, ('unknown_setting', 'bla'))

    def override_test(self):
        """
        Test CastSettings.override
        """
        self.settings.override(CastSettings(
            a_setting={'a': 2, 'c': 3},
            moremore={'D': 'd'},
            _schema={'a_setting': {}, 'moremore': {1: 2}},
        ))
        ok_(self.settings._values['a_setting'] == {'a': 2, 'b': 2, 'c': 3})
        ok_(self.settings._values['moremore'] == {'D': 'd'})
        ok_(self.settings._values['more'] == {'c': 'C'})
        ok_(self.settings._schema == {
            'a_setting': {'override': 'update_item'},
            'moremore': {1: 2},
            'more': {},
            'another': {'type': int},
        })

    def copy_test(self):
        """
        Test CastSettings.copy
        """
        settings_copy = copy.copy(self.settings)
        ok_(settings_copy._values == self.settings._values)
        ok_(not settings_copy._values is self.settings._values)
        ok_(settings_copy._schema == self.settings._schema)
        ok_(not settings_copy._schema is self.settings._schema)
        ok_(settings_copy._values['more'] is self.settings._values['more'])
        ok_(settings_copy._values['another'] is self.settings._values['another'])
        ok_(settings_copy._values['a_setting'] is self.settings._values['a_setting'])


"""
:class:`Settings` is a placeholder to declare the settings available for a serializer class, and to give them default values. For example :

    >>> seq_srz = SequenceSrz()
    >>> class MySrz(Srz):
    ...
    ...     class Settings:
    ...         class_srz_map = {str: seq_srz}
    ...         your_default_attr = 123
    ...
    >>> dict(MySrz.settings) == {
    ...     'custom_for': object,
    ...     'class_srz_map': {str: seq_srz}, # Overwrite Srz's default value
    ...     'your_default_attr': 123,
    ...     'propagate': ['class_srz_map', 'propagate'], # Inherited from Srz
    ... }
    True
    >>> dict(Srz.settings) == {
    ...     'custom_for': object,
    ...     'class_srz_map': {},
    ...     'propagate': ['class_srz_map', 'propagate']
    ... }
    True

Notice that settings are inherited from parent classes if not overriden.

.. seealso:: :class:`Srz.Settings` : settings available for instances of :class:`Srz<>`.

..
    Test that it also works for classes not directly child of Srz :
    >>> id_srz = IdentitySrz() 
    >>> class ChildSrz(MySrz):
    ...
    ...     class Settings:
    ...         class_srz_map = {int: id_srz} #override
    ...
    >>> dict(ChildSrz.settings) == {
    ...     'custom_for': object,
    ...     'class_srz_map': {int: id_srz},
    ...     'your_default_attr': 123,
    ...     'propagate': ['class_srz_map', 'propagate'],
    ... }
    True

Default value for each setting is copied and set on every instance created : 

    >>> mysrz = MySrz() ; mysrz2 = MySrz()
    >>> mysrz.class_srz_map == {str: seq_srz}
    True
    >>> mysrz2.class_srz_map == mysrz.class_srz_map
    True
    >>> mysrz2.class_srz_map is mysrz.class_srz_map # The setting is an instance attribute,
    ... # so you can modify it at will.
    True

In order to set the value (different that the default one) of a setting you can pass a `settings` keyword to the serializer's constructor :

    >>> another_seq_srz = SequenceSrz()
    >>> mysrz = MySrz(class_srz_map={int: another_seq_srz})
    >>> mysrz.class_srz_map == {int: another_seq_srz}
    True

.. 
    Test that it fails for an undefined setting
    >>> MySrz(blabla=1)#doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ValueError: message


:attr:`Srz.Settings.propagate` plays a particular role, in that when using :meth:`Srz.srz_for`, only settings in :attr:`Srz.Settings.propagate` are transmitted from the calling serializer to the returned serializer :

    >>> amysrz = MySrz()
    >>> mysrz = MySrz(class_srz_map={bool: amysrz}, propagate=['class_srz_map', 'your_default_attr'])
    >>> int_srz = mysrz.srz_for(int)
    >>> int_srz.class_srz_map == {bool: amysrz} # Transmitted by 'mysrz'
    True
    >>> int_srz.propagate == ['class_srz_map', 'your_default_attr'] # Not transmitted by 'mysrz'
    False

On the other hand, settings not defined on the returned serializer's class are not set :

    >>> getattr(int_srz, 'your_default_attr', 'UNDEFINED') # Setting 'your_default_attr' is not defined for IdentitySrz
    'UNDEFINED'
"""
