"""
..
    >>> import os, sys
    >>> sys.path.append(os.path.abspath('../..'))
    >>> from any2any.base import *
    >>> from any2any.simple import *

Identity
---------

    >>> identity = Identity()
    >>> identity.call(56)
    56
    >>> identity.call('aa')
    'aa'
    >>> a_list = [1, 2]
    >>> other_list = identity.call(a_list)
    >>> other_list is a_list
    True

SequenceCast
---------------------

    >>> cast = SequenceCast(mm=Mm(Spz(list, object), Spz(list, object)))
    >>> a_list = [1, 'a']
    >>> other_list = cast.call(a_list)
    >>> other_list == a_list, other_list is a_list
    (True, False)

    >>> class MyCast(Cast):
    ...     def call(self, inpt):
    ...         return 'bla %s' % inpt
    ...
    >>> cast.settings['element_cast'] = MyCast()
    >>> cast.call([1, '3by', 78])
    ['bla 1', 'bla 3by', 'bla 78']

MappingCast
--------------------

    >>> a_dict = {1: 78, 'a': 'testi', 'b': 1.89}
    >>> cast = MappingCast(mm=Mm(Spz(dict, object), Spz(dict, object)))
    >>> other_dict = cast.call(a_dict)
    >>> other_dict == a_dict, other_dict is a_dict
    (True, False)
"""

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.REPORT_ONLY_FIRST_FAILURE)
