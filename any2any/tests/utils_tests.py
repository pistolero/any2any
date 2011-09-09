from any2any.utils import *
from any2any.daccasts import Schema
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
        ok_(issubclass(int, object))
        ok_(not issubclass(object, int))
        ok_(issubclass(object, object))
        # specialization + built-in type
        ok_(issubclass(SpecializedType(str), str))
       # ok_(not issubclass(str, SpecializedType(str)))
        ok_(issubclass(SpecializedType(str), SpecializedType(str)))
        ok_(issubclass(SpecializedType(SpecializedType(str)), SpecializedType(str)))
        # test with different superclass.
        spz_type = SpecializedType(int, superclasses=(str,))
        ok_(issubclass(spz_type, str))
        class Dumb(object): pass
        spz_type = SpecializedType(int, superclasses=(Dumb, str))
        ok_(issubclass(spz_type, str))

    def instantiate_test(self):
        """
        Test instantiate a Specialization
        """
        SpzStr = SpecializedType(str)
        a_spz_str = SpzStr("blabla")
        ok_(type(a_spz_str) == str)
        ok_(a_spz_str == "blabla")

        SpzSpzStr = SpecializedType(SpzStr)
        a_spz_str = SpzSpzStr("bloblo")
        ok_(type(a_spz_str) == str)
        ok_(a_spz_str == "bloblo")

        SpzInt = SpecializedType(int, superclass=str)
        a_spz_int = SpzInt(198)
        ok_(a_spz_int == 198)
        ok_(type(a_spz_int) == int)

ListOfObjects = Schema(list, value_type=object)
ListOfStr = Schema(list, value_type=str)
ListOfInt = Schema(list, value_type=int)

class Schema_Test(object):
    """
    Test object schema
    """

    def setUp(self):
        class AnObject(object): pass
        self.AnObject = AnObject
        class AnObjectSchema(Schema):
            def all_keys(self):
                return ['a', 'b', 'c']
            def get_class(self, key):
                return float
        self.AnObjectSchema = AnObjectSchema

    def base_test(self):
        """
        Base tests
        """
        schema = Schema(self.AnObject, key_to_class={'a': int, 'b': str}, value_type=basestring)
        ok_(set(schema) == set(['a', 'b']))
        ok_(schema['a'] == int)
        ok_(schema['b'] == str)
        assert_raises(KeyError, schema.__getitem__, 'c')
        # value_type as default
        schema = self.AnObjectSchema(self.AnObject, key_to_class={'a': int, 'b': str, 'd': unicode}, value_type=basestring)
        ok_(set(schema) == set(['a', 'b', 'c', 'd']))
        ok_(schema['a'] == int)
        ok_(schema['b'] == str)
        ok_(schema['c'] == basestring)
        # get_class as default
        schema = self.AnObjectSchema(self.AnObject, key_to_class={'a': int})
        ok_(schema['b'] == float)

    def issubclass_test(self):
        """
        Tests for isubclass with Schema
        """
        # Nested specializations
        ok_(issubclass( 
            Schema(list, value_type=Schema(
                list, value_type=ListOfStr
            )),
            Schema(list, value_type=Schema(
                list, value_type=ListOfObjects
            ))
        ))
        ok_(not issubclass(
            Schema(list, value_type=Schema(
                list, value_type=ListOfObjects
            )),
            Schema(list, value_type=Schema(
                list, value_type=ListOfStr
            ))
        ))
        ok_(issubclass(
            Schema(list, value_type=Schema(
                list, value_type=ListOfObjects
            )),
            Schema(list, value_type=Schema(
                list, value_type=list
            ))
        ))
        ok_(issubclass(
            Schema(list, value_type=Schema(
                list, value_type=ListOfObjects
            )),
            list
        ))
        ok_(issubclass(
            Schema(list, value_type=Schema(
                list, value_type=ListOfObjects
            )),
            Schema(list, value_type=ListOfObjects)
        ))
        ok_(not issubclass(
            Schema(list, value_type=Schema(
                list, value_type=ListOfObjects
            )),
            Schema(list, value_type=ListOfInt)
        ))


class Memoization_Test(object):
    """
    Tests for the memoization decorators 
    """

    def setUp(self):
        from any2any.simple import Identity
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
        self.cast.configure(from_=object)
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

