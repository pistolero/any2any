from any2any.utils import *
from nose.tools import assert_raises, ok_

class Animal(object): pass
class Shark(Animal): pass
class Human(object): pass
class Salesman(Human): pass
class Tecco(Salesman): pass

shark_to_human = Mm(Shark, Human)
animal_to_salesman = Mm(Animal, Salesman)
animal_to_human = Mm(Animal, Human)
shark_to_salesman = Mm(Shark, Salesman)
salesman_to_human = Mm(Salesman, Human)
human_to_salesman = Mm(Human, Salesman)
shark_to_tecco = Mm(Shark, Tecco)

class Metamorphosis_Test(object):
    """
    Tests for the Metamorphosis class
    """    
    # There are 7 cases (excluding symetric cases):
    # A) m1 = m2                                        -> None
    #
    # B) m1 C m2
    #   m1.from_any < m2.from_any, m2.to < m1.to        -> m1
    #   m1.from_any = m2.from_any, m2.to < m1.to        -> m1
    #   m1.from_any < m2.from_any, m2.to = m1.to        -> m1
    #
    # C) m1 & m2 = {}
    #   m1.from_any > m2.from_any, m2.to < m1.to        -> m1
    #   m1.from_any = m2.from_any, m2.to > m1.to        -> m2
    #   m1.from_any > m2.from_any, m2.to = m1.to        -> m2

    def is_included_test(self):
        """
        Test Metamorphosis.is_included
        """
        # A)
        ok_(animal_to_salesman.included_in(animal_to_salesman))
        # B)
        ok_(shark_to_human.included_in(animal_to_salesman))
        ok_(animal_to_human.included_in(animal_to_salesman))
        ok_(shark_to_salesman.included_in(animal_to_salesman))
        # C)
        ok_(not animal_to_human.included_in(shark_to_salesman))
        ok_(not animal_to_salesman.included_in(animal_to_human))
        ok_(not animal_to_human.included_in(shark_to_human))

    def most_precise_test(self):
        """
        Test Metamorphosis.most_precise
        """
        # A)
        ok_(Mm.most_precise(animal_to_salesman, animal_to_salesman) == None)
        # B)
        ok_(Mm.most_precise(shark_to_human, animal_to_salesman) == shark_to_human)
        ok_(Mm.most_precise(animal_to_human, animal_to_salesman) == animal_to_human)
        ok_(Mm.most_precise(shark_to_salesman, animal_to_salesman) == shark_to_salesman)
        # C)
        ok_(Mm.most_precise(animal_to_human, shark_to_salesman) == animal_to_human)
        ok_(Mm.most_precise(animal_to_salesman, animal_to_human) == animal_to_human)
        ok_(Mm.most_precise(animal_to_human, shark_to_human) == shark_to_human)

    def test_pick_closest_in(self):
        """
        Test Metamorphosis.pick_closest_in
        """
        ok_(animal_to_salesman.pick_closest_in(
            [animal_to_salesman, shark_to_human, salesman_to_human]
        ) == animal_to_salesman)
        ok_(animal_to_salesman.pick_closest_in(
            [animal_to_salesman]
        ) == animal_to_salesman)
        assert_raises(ValueError, animal_to_salesman.pick_closest_in, [human_to_salesman])
        ok_(shark_to_salesman.pick_closest_in(
            [animal_to_salesman, shark_to_tecco]
        ) == animal_to_salesman)
        ok_(shark_to_salesman.pick_closest_in(
            [shark_to_tecco, animal_to_salesman]
        ) == animal_to_salesman)
        
class Specialization_Test(object):
    """
    Tests for the Specialization class
    """  

    def issubclass_test(self):
        """
        Test Specialization.issubclass
        """
        # built-in types
        ok_(Spz.issubclass(int, object))
        ok_(not Spz.issubclass(object, int))
        ok_(Spz.issubclass(object, object))
        # specialization + built-in type
        ok_(Spz.issubclass(Spz(list, int), list))
        ok_(not Spz.issubclass(list, Spz(list, int)))
        # specialization only
        ok_(Spz.issubclass(Spz(list, int), Spz(list, int)))
        ok_(Spz.issubclass(Spz(list, int), Spz(list, object)))
        ok_(not Spz.issubclass(Spz(list, object), Spz(list, int)))
        # Nested specializations
        ok_(Spz.issubclass( Spz(list, 
                                Spz(list, 
                                    Spz(list, str))),
                            Spz(list,
                                Spz(list,
                                    Spz(list, object)))
        ))
        ok_(not Spz.issubclass( Spz(list,
                                    Spz(list,
                                        Spz(list, object))),
                                Spz(list,
                                    Spz(list,
                                        Spz(list, str)))
        ))
        ok_(Spz.issubclass( Spz(list,
                                Spz(list,
                                    Spz(list, object))),
                            Spz(list,
                                Spz(list, list))
        ))
        ok_(Spz.issubclass( Spz(list,
                                Spz(list,
                                    Spz(list, object))),
                            list))
        ok_(Spz.issubclass( Spz(list,
                                Spz(list,
                                    Spz(list, object))),
                            Spz(list,
                                Spz(list, object))
        ))
        ok_(not Spz.issubclass( Spz(list,
                                Spz(list,
                                    Spz(list, object))),
                            Spz(list,
                                Spz(list, int))
        ))
