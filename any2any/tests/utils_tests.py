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
    '''
    def subclassing_test(self):
        """
        Test subclassing Specialization
        """
        class MySpecialization()
    '''

    def issubclass_test(self):
        """
        Test Specialization.issubclass
        """
        # built-in types
        ok_(issubclass(int, object))
        ok_(not issubclass(object, int))
        ok_(issubclass(object, object))
        # specialization + built-in type
        ok_(issubclass(SpecializedType(str), str))
        ok_(not issubclass(str, SpecializedType(str)))
        ok_(issubclass(SpecializedType(str), SpecializedType(str)))
        ok_(issubclass(SpecializedType(SpecializedType(str)), SpecializedType(str)))
