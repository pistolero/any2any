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

class Metamorphosis_Test(object):
    """
    Tests for the Metamorphosis class
    """    
    # There are 10 cases (excluding symetric cases):
    # A) m1 = m2                                        -> None
    #
    # B) m1 C m2
    #   m1.from < m2.from, m1.to < m2.to        -> m1 < m2
    #   m1.from = m2.from, m1.to < m2.to        -> m1 < m2
    #   m1.from < m2.from, m1.to = m2.to        -> m1 < m2
    #
    # C) m1 ? m2
    #   a) m1.from > m2.from, m1.to < m2.to        -> None
    #   b) m1.from ? m2.from, m1.to < m2.to        -> None
    #   c) m1.from < m2.from, m1.to ? m2.to        -> None
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

    def test_super_mms(self):
        """
        Test Metamorphosis.super_mms
        """
        # Both `any_animal_to_salesman` and `shark_to_any_human` are supersets of `shark_to_salesman`
        ok_(set(shark_to_salesman.super_mms(
            [any_animal_to_salesman, salesman_to_human, shark_to_any_human]
        )) == set([any_animal_to_salesman, shark_to_any_human]))
        # Both `any_animal_to_salesman` and `shark_to_salesman` are supersets of `shark_to_salesman`,
        # but `any_animal_to_salesman` is superset of `shark_to_salesman`, therefore not needed.
        ok_(shark_to_salesman.super_mms(
            [any_animal_to_salesman, shark_to_salesman, salesman_to_human]
        ) == [shark_to_salesman])
        # No match
        ok_(animal_to_salesman.super_mms([human_to_salesman]) == [])
        
class Wrap_Test(object):
    """
    Tests for the Wrap class
    """

    def wrapmeta_test(self):
        """
        Test subclassing a wrap and defaults inheritance
        """
        class MyWrap(Wrap):
            defaults = {'feat1': 123}

        ok_(MyWrap.defaults == {'factory': None, 'feat1': 123, 'superclasses': ()})

    def issubclass_test(self):
        """
        Test Wrap.issubclass
        """
        # built-in types
        ok_(Wrap.issubclass(int, object))
        ok_(not Wrap.issubclass(object, int))
        ok_(Wrap.issubclass(object, object))
        # Wrap + built-in type
        ok_(Wrap.issubclass(Wrap(str), str))
        ok_(not Wrap.issubclass(str, Wrap(str)))
        ok_(Wrap.issubclass(Wrap(str), Wrap(str)))
        ok_(Wrap.issubclass(Wrap(Wrap(str)), Wrap(str)))
        # test with different superclass.
        WrappedTypes = Wrap(int, superclasses=(str,))
        ok_(Wrap.issubclass(WrappedTypes, str))
        class Dumb(object): pass
        WrappedTypes = Wrap(int, superclasses=(Dumb, str,))
        ok_(Wrap.issubclass(WrappedTypes, str))
        ok_(Wrap.issubclass(WrappedTypes, int))
        ok_(Wrap.issubclass(WrappedTypes, Dumb))

    def instantiate_test(self):
        """
        Test instantiate a Wrap
        """
        WrappedStr = Wrap(str)
        a_str = WrappedStr("blabla")
        ok_(type(a_str) == str)
        ok_(a_str == "blabla")

        WrappedWrappedStr = Wrap(WrappedStr)
        a_str = WrappedWrappedStr("bloblo")
        ok_(type(a_str) == str)
        ok_(a_str == "bloblo")

        WrappedInt = Wrap(int, superclasses=(str,))
        an_int = WrappedInt(198)
        ok_(an_int == 198)
        ok_(type(an_int) == int)

    def declarative_instantiate_test(self):
        """
        Test instantiate a wrap with the declarative syntax
        """
        class WrappedInt(Wrapped):
            class Meta:
                klass = int
        # Test features and other basics
        ok_(isinstance(WrappedInt, Wrap))
        ok_(WrappedInt.superclasses == (int,))
        ok_(WrappedInt.factory == int)
        an_int = WrappedInt(198)
        ok_(an_int == 198)
        ok_(type(an_int) == int)
        # Test declaring instance methods
        try:
            class UnvalidWrapped(Wrapped):
                def non_sense(self): pass
                class Meta:
                    klass = int
        except TypeError:
            pass
        else:
            raise Exception("test failed, because cannot declare instance methods there")
        # Test declaring class methods
        class MyWrapped(Wrapped):
            @classmethod
            def makes_sense(self): return 11
            class Meta:
                klass = int
        ok_(MyWrapped.makes_sense() == 11)
        # Check that inheritance works as well
        class MyOhMyWrapped(MyWrapped):
            class Meta:
                klass = int
        ok_(MyOhMyWrapped.makes_sense() == 11)

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

