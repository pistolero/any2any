# -*- coding: utf-8 -*-
from any2any.utils import *
from nose.tools import assert_raises, ok_


class ClassSet_Test(object):
    """
    Tests for the ClassSet class
    """

    def eq_test(self):
        """
        Test ClassSet.__eq__ 
        """
        ok_(AllSubSetsOf(object) == AllSubSetsOf(object))
        ok_(ClassSet(int) == ClassSet(int))
        ok_(not AllSubSetsOf(object) == ClassSet(object))
        ok_(not AllSubSetsOf(object) == AllSubSetsOf(int))
        ok_(not ClassSet(object) == ClassSet(int))

        ok_(ClassSet(object) == object)
        ok_(not AllSubSetsOf(object) == object)

        ok_(not ClassSet(int) == ClassSet(str, int))

    def lt_test(self):
        """
        Test ClassSet.__lt__
        """
        ok_(ClassSet(object) < AllSubSetsOf(object)) # {object} is included in subclasses of object
        ok_(ClassSet(int, str) < AllSubSetsOf(object)) # {int, str} is included in subclasses of object
        ok_(AllSubSetsOf(int) < AllSubSetsOf(object)) # subclasses of int are included in subclasses of object

        ok_(not AllSubSetsOf(object) < AllSubSetsOf(object)) # because ==
        ok_(not ClassSet(int) < ClassSet(object))
        ok_(not AllSubSetsOf(int) < ClassSet(object))
        ok_(not AllSubSetsOf(int) < AllSubSetsOf(str)) # because no one is other's parent

        ok_(not ClassSet(str) < object)
        ok_(not ClassSet(object) < object)
        ok_(not AllSubSetsOf(object) < object)

    def comp_test(self):
        """
        Test ClassSet's rich comparison
        """
        # Revert of lt_tests
        ok_(AllSubSetsOf(object) > ClassSet(object))
        ok_(AllSubSetsOf(object) > ClassSet(int, str, dict))
        ok_(AllSubSetsOf(object) > AllSubSetsOf(int))

        ok_(not AllSubSetsOf(object) > AllSubSetsOf(object)) # because ==
        ok_(not ClassSet(int) > ClassSet(object))
        ok_(not AllSubSetsOf(int) > ClassSet(object))
        ok_(not AllSubSetsOf(int) > AllSubSetsOf(str)) # because no one is other's parent
        
        ok_(AllSubSetsOf(object) > object)
        ok_(AllSubSetsOf(object) > str)
        ok_(not ClassSet(object) > str)

        # Other comparison operators
        ok_(AllSubSetsOf(object) >= ClassSet(object, dict))
        ok_(AllSubSetsOf(object) >= ClassSet(int))
        ok_(AllSubSetsOf(object) >= AllSubSetsOf(int))
        ok_(AllSubSetsOf(object) >= AllSubSetsOf(object))


class ClassSetDict_Test(object):
    """
    Tests for the ClassSetDict class
    """

    def subsetget_test(self):
        """
        test ClassSetDict.subsetget
        """
        choice_map = {
            AllSubSetsOf(basestring): 1,
            AllSubSetsOf(object): 2,
            ClassSet(int): 3,
        }
        csd = ClassSetDict(choice_map)
        ok_(csd.subsetget(object) is 2)
        ok_(csd.subsetget(float) is 2)
        ok_(csd.subsetget(str) is 1)
        ok_(csd.subsetget(int) is 3)

    def no_pick_test(self):
        """
        test ClassSetDict.subsetget with no suitable subset
        """
        choice_map = {ClassSet(int): 1}
        csd = ClassSetDict(choice_map)
        ok_(csd.subsetget(str) is None)
        ok_(csd.subsetget(str, 'blabla') is 'blabla')


class SmartDict_test(object):
    """
    Tests for the SmartDict class
    """

    def getitem_test(self):
        """
        Test SmartDict.__getitem__
        """
        d = SmartDict({SmartDict.KeyAny: 1, 'a': 2, 'b': 3})
        ok_(d['a'] == 2)
        ok_(d['b'] == 3)
        ok_(d['c'] == 1)
        ok_(d['d'] == 1)

    def getitem_keyerror_test(self):
        """
        Test SmartDict.__getitem__
        """
        d = SmartDict({'a': 1})
        assert_raises(KeyError, d.__getitem__, 'b')
        d = SmartDict({SmartDict.KeyAny: 1})
        assert_raises(KeyError, d.__getitem__, SmartDict.KeyFinal)

    def get_test(self):
        """
        Test SmartDict.get
        """
        d = SmartDict({SmartDict.KeyAny: 1, 'a': 2, 'b': 3})
        ok_(d.get('a') == 2)
        ok_(d.get('b') == 3)
        ok_(d.get('c') == 1)
        ok_(d.get('d') == 1)
        d = SmartDict({'a': 1})
        ok_(d.get('a') == 1)
        ok_(d.get('b', 2) == 2)

    def contains_test(self):
        """
        Test SmartDict.contains
        """
        d = SmartDict({SmartDict.KeyAny: 1, 'a': 2, 'b': 3})
        ok_('a' in d)
        ok_('b' in d)
        ok_('c' in d)
        ok_(not SmartDict.KeyFinal in d)
