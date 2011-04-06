"""
..
    >>> import os, sys
    >>> sys.path.append(os.path.abspath('../..'))
    >>> from any2any.base import *

init
---------

Valid settings

    >>> settings = CastSettings(
    ...     my_setting={1: 2},
    ...     my_other_setting=1,
    ...     _schema={'my_setting': {'update': 'update'}}
    ... )
    >>> settings._values == {
    ...     'my_setting': {1: 2},
    ...     'my_other_setting': 1,
    ... }
    True
    >>> settings._schema == {
    ...     'my_setting': {'update': 'update'},
    ...     'my_other_setting': {}
    ... }
    True

items
-------

    >>> dict(settings.items()) == settings._values
    True

iter
-----

    >>> list(settings) == settings._values.keys()
    True

contains
---------

    >>> 'my_setting' in settings
    True
    >>> 'my_other_setting' in settings
    True
    >>> 'unvalid_another' in settings
    False

update
--------

fixture

    >>> settings = CastSettings(
    ...     _schema={'a_setting': {'update': 'update'}},
    ...     a_setting={'a': 1, 'b': 2},
    ...     another=1,
    ...     more={'c': 'C'},
    ... )

Test

    >>> settings.update(CastSettings(
    ...     a_setting={'a': 2, 'c': 3},
    ...     moremore={'D': 'd'},
    ...     _schema={'a_setting': {}, 'moremore': {1: 2}},
    ... ))
    >>> settings._values['a_setting'] == {'a': 2, 'b': 2, 'c': 3}
    True
    >>> settings._values['moremore'] == {'D': 'd'}
    True
    >>> settings._values['more'] == {'c': 'C'}
    True
    >>> settings._schema == {
    ...     'a_setting': {'update': 'update'},
    ...     'moremore': {1: 2},
    ...     'more': {},
    ...     'another': {},
    ... }
    True

copy
------

fixture

    >>> settings = CastSettings(
    ...     _schema={'a_setting': {'update': 'update'}},
    ...     a_setting={'a': 1, 'b': 2},
    ...     another=1,
    ...     more={'c': 'C'},
    ... )

Test

    >>> settings_copy = copy.copy(settings)
    >>> settings_copy._values == settings._values
    True
    >>> settings_copy._values is settings._values
    False
    >>> settings_copy._schema == settings._schema
    True
    >>> settings_copy._schema is settings._schema
    False
    >>> settings_copy._values['more'] is settings._values['more']
    True
    >>> settings_copy._values['another'] is settings._values['another']
    True
    >>> settings_copy._values['a_setting'] is settings._values['a_setting']
    True

configure
-----------

fixture

    >>> settings = CastSettings(
    ...     _schema={'a_setting': {'update': 'update'}},
    ...     a_setting={'a': 1, 'b': 2},
    ...     another=1,
    ...     more={'c': 'C'},
    ... )

Valid settings

    >>> settings.configure(a_setting=1, another=[1, 3, 5])
    >>> settings._values == {
    ...     'a_setting': 1,
    ...     'another': [1, 3, 5],
    ...     'more': {'c': 'C'},
    ... }
    True

Invalid setting

    >>> settings.configure(b_setting=1)#doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    TypeError: message

get
----

fixture

    >>> settings = CastSettings(
    ...     a_setting=2,
    ...     more='c',
    ... )

Valid setting

    >>> settings.get('a_setting')
    2
    >>> settings.get('more')
    'c'

Invalid setting

    >>> settings.get('b_setting')#doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    TypeError: message

"""
if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.REPORT_ONLY_FIRST_FAILURE)

