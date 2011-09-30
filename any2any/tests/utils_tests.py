# -*- coding: utf-8 -*-
from any2any.utils import *
from nose.tools import assert_raises, ok_

class Animal(object): pass
class Shark(Animal): pass
class Human(object): pass
class Salesman(Human): pass

shark_to_human = Mm(Shark, Human)
animal_to_salesman = Mm(Animal, Salesman)
animal_to_human = Mm(Animal, Human)
shark_to_salesman = Mm(Shark, Salesman)
salesman_to_human = Mm(Salesman, Human)
human_to_salesman = Mm(Human, Salesman)
any_animal_to_any_human = Mm(from_any=Animal, to_any=Human)
any_animal_to_salesman = Mm(from_any=Animal, to=Salesman)
animal_to_any_human = Mm(Animal, to_any=Human)
shark_to_any_human = Mm(Shark, to_any=Human)
any_animal_to_human = Mm(from_any=Animal, to=Human)
salesman_to_any_human = Mm(Salesman, to_any=Human)
any_animal_to_shark = Mm(from_any=Animal, to=Shark)
any_human_to_salesman = Mm(from_any=Human, to=Salesman)
any_human_to_shark = Mm(from_any=Human, to=Shark)

class ClassSet_Test(object):
    """
    Tests for the ClassSet class
    """

    def eq_test(self):
        """
        Test ClassSet.__eq__ 
        """
        ok_(ClassSet(object, False) == ClassSet(object, False))
        ok_(ClassSet(int, True) == ClassSet(int, True))
        ok_(not ClassSet(object, False) == ClassSet(object, True))
        ok_(not ClassSet(object, False) == ClassSet(int, False))
        ok_(not ClassSet(object, True) == ClassSet(int, True))

    def lt_test(self):
        """
        Test ClassSet.__lt__
        """
        ok_(ClassSet(object, True) < ClassSet(object, False)) # {object} is included in subclasses of object
        ok_(ClassSet(int, True) < ClassSet(object, False)) # {int} is included in subclasses of object
        ok_(ClassSet(int, False) < ClassSet(object, False)) # subclasses of int are included in subclasses of object

        ok_(not ClassSet(object, False) < ClassSet(object, False)) # because ==
        ok_(not ClassSet(int, True) < ClassSet(object, True)) # because other is singleton
        ok_(not ClassSet(int, False) < ClassSet(object, True)) # ''
        ok_(not ClassSet(int, False) < ClassSet(str, False)) # because no one is other's parent

    def comp_test(self):
        """
        Test ClassSet's rich comparison
        """
        # Revert of lt_tests
        ok_(ClassSet(object, False) > ClassSet(object, True))
        ok_(ClassSet(object, False) > ClassSet(int, True))
        ok_(ClassSet(object, False) > ClassSet(int, False))

        ok_(not ClassSet(object, False) > ClassSet(object, False)) # because ==
        ok_(not ClassSet(int, True) > ClassSet(object, True)) # because other is singleton
        ok_(not ClassSet(int, False) > ClassSet(object, True)) # ''
        ok_(not ClassSet(int, False) > ClassSet(str, False)) # because no one is other's parent
        
        # Other comparison operators
        ok_(ClassSet(object, False) >= ClassSet(object, True))
        ok_(ClassSet(object, False) >= ClassSet(int, True))
        ok_(ClassSet(object, False) >= ClassSet(int, False))
        ok_(ClassSet(object, False) >= ClassSet(object, False))

class Metamorphosis_Test(object):
    """
    Tests for the Metamorphosis class
    """    
    # There are 10 cases (excluding symetric cases):
    # A) m1 = m2                                        -> None
    #
    # B) m1 C m2
    #   m1.from < m2.from, m1.to < m2.to        -> m1
    #   m1.from = m2.from, m1.to < m2.to        -> m1
    #   m1.from < m2.from, m1.to = m2.to        -> m1
    #
    # C) m1 ? m2
    #   a) m1.from > m2.from, m1.to < m2.to        -> m1
    #   b) m1.from ? m2.from, m1.to < m2.to        -> m1
    #   c) m1.from < m2.from, m1.to ? m2.to        -> m1
    #   d) m1.from ? m2.from, m1.to ? m2.to        -> None
    #   e) m1.from ? m2.from, m1.to = m2.to        -> None
    #   f) m1.from = m2.from, m1.to ? m2.to        -> None

    def is_included_test(self):
        """
        Test Metamorphosis.is_included
        """
        # A)
        ok_(animal_to_salesman.included_in(animal_to_salesman))
        # B)
        ok_(shark_to_salesman.included_in(any_animal_to_any_human))
        ok_(animal_to_salesman.included_in(animal_to_any_human))
        ok_(shark_to_salesman.included_in(any_animal_to_salesman))
        # C)
        ok_(not any_animal_to_any_human.included_in(shark_to_salesman))
        ok_(not animal_to_salesman.included_in(animal_to_human))
        ok_(not animal_to_human.included_in(shark_to_human))

    def most_precise_test(self):
        """
        Test Metamorphosis.most_precise
        """
        # A)
        ok_(Mm.most_precise(animal_to_salesman, animal_to_salesman) == None)
        # B)
        ok_(Mm.most_precise(shark_to_human, any_animal_to_any_human) == shark_to_human)
        ok_(Mm.most_precise(animal_to_human, animal_to_any_human) == animal_to_human)
        ok_(Mm.most_precise(shark_to_salesman, any_animal_to_salesman) == shark_to_salesman)
        # C) a), b), c)
        ok_(Mm.most_precise(any_animal_to_human, shark_to_any_human) == any_animal_to_human)
        ok_(Mm.most_precise(shark_to_salesman, salesman_to_any_human) == shark_to_salesman)
        ok_(Mm.most_precise(shark_to_salesman, any_animal_to_shark) == shark_to_salesman)
        #d), e), f)
        ok_(Mm.most_precise(any_animal_to_shark, human_to_salesman) == None)
        ok_(Mm.most_precise(shark_to_salesman, any_human_to_salesman) == None)
        ok_(Mm.most_precise(any_human_to_salesman, any_human_to_shark) == None)

    def test_pick_closest_in(self):
        """
        Test Metamorphosis.pick_closest_in
        """
        ok_(shark_to_salesman.pick_closest_in(
            [any_animal_to_salesman, shark_to_salesman, salesman_to_human]
        ) == shark_to_salesman)
        ok_(shark_to_salesman.pick_closest_in(
            [any_animal_to_salesman, salesman_to_human, shark_to_any_human]
        ) == any_animal_to_salesman)
        ok_(shark_to_salesman.pick_closest_in(
            [shark_to_salesman]
        ) == shark_to_salesman)
        assert_raises(ValueError, animal_to_salesman.pick_closest_in, [human_to_salesman])
        
class Specialization_Test(object):
    """
    Tests for the Specialization class
    """

    def issubclass_test(self):
        """
        Test Specialization.issubclass
        """
        # built-in types
        ok_(Wrap.issubclass(int, object))
        ok_(not Wrap.issubclass(object, int))
        ok_(Wrap.issubclass(object, object))
        # specialization + built-in type
        ok_(Wrap.issubclass(TypeWrap(str), str))
        ok_(not Wrap.issubclass(str, TypeWrap(str)))
        ok_(Wrap.issubclass(TypeWrap(str), TypeWrap(str)))
        ok_(Wrap.issubclass(TypeWrap(TypeWrap(str)), TypeWrap(str)))
        # test with different superclass.
        spz_type = TypeWrap(int, str)
        ok_(Wrap.issubclass(spz_type, str))
        class Dumb(object): pass
        spz_type = TypeWrap(int, Dumb, str)
        ok_(Wrap.issubclass(spz_type, str))
        ok_(Wrap.issubclass(spz_type, Dumb))

    def instantiate_test(self):
        """
        Test instantiate a Specialization
        """
        WrappedStr = TypeWrap(str)
        a_spz_str = WrappedStr("blabla")
        ok_(type(a_spz_str) == str)
        ok_(a_spz_str == "blabla")

        WrappedWrappedStr = TypeWrap(WrappedStr)
        a_spz_str = WrappedWrappedStr("bloblo")
        ok_(type(a_spz_str) == str)
        ok_(a_spz_str == "bloblo")

        WrappedInt = TypeWrap(int, str)
        a_spz_int = WrappedInt(198)
        ok_(a_spz_int == 198)
        ok_(type(a_spz_int) == int)

class Memoization_Test(object):
    """
    Tests for the memoization decorators 
    """

    def setUp(self):
        from any2any import Cast
        class Identity(Cast):
            def call(self, inpt):
                return inpt

        class TestMemCast(Identity):

            @memoize(key=lambda args, kwargs: (args[1], kwargs['kwarg1']))
            def method1(self, arg1, arg2, kwarg1=None):
                return arg1

            @memoize()
            def method2(self, arg1, arg2, kwarg1=None):
                import datetime
                return datetime.datetime.now()

            @memoize(key=lambda args, kwargs: type(args[1]))
            def method3(self, arg1, arg2):
                return arg1

            @memoize()
            def method4(self):
                import datetime
                return datetime.datetime.now()

        self.cast = TestMemCast()

    def memoize_test(self):
        """
        Test memoize decorator
        """
        ok_(self.cast.method1(1, 2, kwarg1=3) == 1)
        ok_(self.cast.method1(55, 2, kwarg1=3) == 1)
        ok_(self.cast.method1(55, 3, kwarg1=3) == 55)
        ok_(self.cast.method1(66, 3, kwarg1=3) == 55)
        self.cast.from_ = object
        ok_(self.cast.method1(88, 2, kwarg1=3) == 88)
        ok_(self.cast.method1(66, 3, kwarg1=3) == 66)

        result = self.cast.method2(1, 2, kwarg1=3)
        import time ; time.sleep(0.1)
        ok_(self.cast.method2(1, 2, kwarg1=3) == result)
        import time ; time.sleep(0.1)
        ok_(not self.cast.method2(2, 2, kwarg1=3) == result)

        ok_(self.cast.method3(1, 2) == 1)
        ok_(self.cast.method3(55, 7) == 1)
        ok_(self.cast.method3(55, 'a') == 55)
        ok_(self.cast.method3(66, 'yyy') == 55)

        result = self.cast.method4()
        import time ; time.sleep(0.1)
        ok_(self.cast.method4() == result)

