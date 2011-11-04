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
        ok_(Singleton(int) == Singleton(int))
        ok_(not AllSubSetsOf(object) == Singleton(object))
        ok_(not AllSubSetsOf(object) == AllSubSetsOf(int))
        ok_(not Singleton(object) == Singleton(int))

        ok_(Singleton(object) == object)
        ok_(not AllSubSetsOf(object) == object)

    def lt_test(self):
        """
        Test ClassSet.__lt__
        """
        ok_(Singleton(object) < AllSubSetsOf(object)) # {object} is included in subclasses of object
        ok_(Singleton(int) < AllSubSetsOf(object)) # {int} is included in subclasses of object
        ok_(AllSubSetsOf(int) < AllSubSetsOf(object)) # subclasses of int are included in subclasses of object

        ok_(not AllSubSetsOf(object) < AllSubSetsOf(object)) # because ==
        ok_(not Singleton(int) < Singleton(object)) # because other is singleton
        ok_(not AllSubSetsOf(int) < Singleton(object)) # ''
        ok_(not AllSubSetsOf(int) < AllSubSetsOf(str)) # because no one is other's parent

        ok_(not Singleton(str) < object)
        ok_(not Singleton(object) < object)
        ok_(not AllSubSetsOf(object) < object)

    def comp_test(self):
        """
        Test ClassSet's rich comparison
        """
        # Revert of lt_tests
        ok_(AllSubSetsOf(object) > Singleton(object))
        ok_(AllSubSetsOf(object) > Singleton(int))
        ok_(AllSubSetsOf(object) > AllSubSetsOf(int))

        ok_(not AllSubSetsOf(object) > AllSubSetsOf(object)) # because ==
        ok_(not Singleton(int) > Singleton(object)) # because other is singleton
        ok_(not AllSubSetsOf(int) > Singleton(object)) # ''
        ok_(not AllSubSetsOf(int) > AllSubSetsOf(str)) # because no one is other's parent
        
        ok_(AllSubSetsOf(object) > object)
        ok_(AllSubSetsOf(object) > str)
        ok_(not Singleton(object) > str)

        # Other comparison operators
        ok_(AllSubSetsOf(object) >= Singleton(object))
        ok_(AllSubSetsOf(object) >= Singleton(int))
        ok_(AllSubSetsOf(object) >= AllSubSetsOf(int))
        ok_(AllSubSetsOf(object) >= AllSubSetsOf(object))

    def pick_best_test(self):
        """
        test ValueInfo._pick_best
        """
        choice_map = {
            AllSubSetsOf(basestring): 1,
            AllSubSetsOf(object): 2,
            Singleton(int): 3,
        }
        ok_(ClassSet.pick_best(object, choice_map) is 2)
        ok_(ClassSet.pick_best(float, choice_map) is 2)
        ok_(ClassSet.pick_best(str, choice_map) is 1)
        ok_(ClassSet.pick_best(int, choice_map) is 3)

    def no_pick_test(self):
        """
        test ValueInfo._pick_best with no suitable bundle class
        """
        choice_map = {Singleton(int): 1}
        class Bla(Exception): pass
        assert_raises(Bla, ClassSet.pick_best, str, choice_map, exc_type=Bla)

