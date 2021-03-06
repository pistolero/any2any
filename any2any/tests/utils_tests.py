# -*- coding: utf-8 -*-
import unittest

from any2any.utils import *


class ClassSet_Test(unittest.TestCase):
    """
    Tests for the ClassSet class
    """

    def eq_test(self):
        """
        Test ClassSet.__eq__ 
        """
        self.assertEqual(AllSubSetsOf(object), AllSubSetsOf(object))
        self.assertEqual(ClassSet(int), ClassSet(int))
        self.assertNotEqual(AllSubSetsOf(object), ClassSet(object))
        self.assertNotEqual(AllSubSetsOf(object), AllSubSetsOf(int))
        self.assertNotEqual(ClassSet(object), ClassSet(int))

        self.assertEqual(ClassSet(object), object)
        self.assertNotEqual(AllSubSetsOf(object), object)

        self.assertNotEqual(ClassSet(int), ClassSet(str, int))

        self.assertNotEqual(ClassSet(object), 1)

    def lt_test(self):
        """
        Test ClassSet.__lt__
        """
        self.assertTrue(ClassSet(object) < AllSubSetsOf(object)) # {object} is included in subclasses of object
        self.assertTrue(ClassSet(int, str) < AllSubSetsOf(object)) # {int, str} is included in subclasses of object
        self.assertTrue(AllSubSetsOf(int) < AllSubSetsOf(object)) # subclasses of int are included in subclasses of object

        self.assertFalse(AllSubSetsOf(object) < AllSubSetsOf(object)) # because ==
        self.assertFalse(ClassSet(int) < ClassSet(object))
        self.assertFalse(AllSubSetsOf(int) < ClassSet(object))
        self.assertFalse(AllSubSetsOf(int) < AllSubSetsOf(str)) # because no one is other's parent

        self.assertFalse(ClassSet(str) < object)
        self.assertFalse(ClassSet(object) < object)
        self.assertFalse(AllSubSetsOf(object) < object)

    def comp_test(self):
        """
        Test ClassSet's rich comparison
        """
        # Revert of lt_tests
        self.assertTrue(AllSubSetsOf(object) > ClassSet(object))
        self.assertTrue(AllSubSetsOf(object) > ClassSet(int, str, dict))
        self.assertTrue(AllSubSetsOf(object) > AllSubSetsOf(int))

        self.assertFalse(AllSubSetsOf(object) > AllSubSetsOf(object)) # because ==
        self.assertFalse(ClassSet(int) > ClassSet(object))
        self.assertFalse(AllSubSetsOf(int) > ClassSet(object))
        self.assertFalse(AllSubSetsOf(int) > AllSubSetsOf(str)) # because no one is other's parent
        
        self.assertTrue(AllSubSetsOf(object) > object)
        self.assertTrue(AllSubSetsOf(object) > str)
        self.assertFalse(ClassSet(object) > str)

        # Other comparison operators
        self.assertTrue(AllSubSetsOf(object) >= ClassSet(object, dict))
        self.assertTrue(AllSubSetsOf(object) >= ClassSet(int))
        self.assertTrue(AllSubSetsOf(object) >= AllSubSetsOf(int))
        self.assertTrue(AllSubSetsOf(object) >= AllSubSetsOf(object))


class ClassSetDict_Test(unittest.TestCase):
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
        self.assertTrue(csd.subsetget(object) is 2)
        self.assertTrue(csd.subsetget(float) is 2)
        self.assertTrue(csd.subsetget(str) is 1)
        self.assertTrue(csd.subsetget(int) is 3)

    def no_pick_test(self):
        """
        test ClassSetDict.subsetget with no suitable subset
        """
        choice_map = {ClassSet(int): 1}
        csd = ClassSetDict(choice_map)
        self.assertIsNone(csd.subsetget(str))
        self.assertEqual(csd.subsetget(str, 'blabla'), 'blabla')


class AttrDict_test(unittest.TestCase):
    """
    Tests for the AttrDict class
    """

    def getitem_test(self):
        """
        Test AttrDict.__getitem__
        """
        d = AttrDict({AttrDict.KeyAny: 1, 'a': 2, 'b': 3})
        self.assertEqual(d['a'], 2)
        self.assertEqual(d['b'], 3)
        self.assertEqual(d['c'], 1)
        self.assertEqual(d['d'], 1)

    def getitem_keyerror_test(self):
        """
        Test AttrDict.__getitem__ with a key that is not in the dict, or when the dict doesn't contain
        `KeyAny`.
        """
        d = AttrDict({'a': 1})
        self.assertRaises(KeyError, d.__getitem__, 'b')
        d = AttrDict({AttrDict.KeyAny: 1})
        self.assertRaises(KeyError, d.__getitem__, AttrDict.KeyFinal)

    def iter_attrs_test(self):
        """
        Test iterating attributes.
        """
        d = AttrDict({'a': 1, 'b': 2, AttrDict.KeyAny: 3})
        self.assertItemsEqual(['a', 'b'], list(d.iter_attrs()))
        d = AttrDict({'a': 1, 'b': 2})
        self.assertItemsEqual(['a', 'b'], list(d.iter_attrs()))
        d = AttrDict({AttrDict.KeyAny: 1})
        self.assertItemsEqual([], list(d.iter_attrs()))

    def get_test(self):
        """
        Test AttrDict.get
        """
        d = AttrDict({AttrDict.KeyAny: 1, 'a': 2, 'b': 3})
        self.assertEqual(d.get('a'), 2)
        self.assertEqual(d.get('b'), 3)
        self.assertEqual(d.get('c'), 1)
        self.assertEqual(d.get('d'), 1)
        d = AttrDict({'a': 1})
        self.assertEqual(d.get('a'), 1)
        self.assertEqual(d.get('b', 2), 2)

    def del_test(self):
        """
        Test AttrDict.__delitem__
        """
        d = AttrDict({AttrDict.KeyAny: 1, 'a': 2, 'b': 3})
        del d['a']
        self.assertItemsEqual(d.keys(), ['b', AttrDict.KeyAny])
        del d[AttrDict.KeyAny]
        self.assertItemsEqual(d.keys(), ['b'])

    def len_test(self):
        """
        Test AttrDict.__len__
        """
        d = AttrDict({AttrDict.KeyAny: 1, 'a': 2, 'b': 3})
        self.assertEqual(len(d), 3)

    def contains_test(self):
        """
        Test AttrDict.contains
        """
        d = AttrDict({AttrDict.KeyAny: 1, 'a': 2, 'b': 3})
        self.assertTrue('a' in d)
        self.assertTrue('b' in d)
        self.assertTrue('c' in d)
        self.assertFalse(AttrDict.KeyFinal in d)

    def constructor_unvalid_data_test(self):
        """
        Test constuctor raises ValueError with unvalid schemas.
        """
        self.assertRaises(ValueError, AttrDict, {
            AttrDict.KeyFinal: str,
            'a': str,
            'bb': float
        })
        self.assertRaises(ValueError, AttrDict, {
            AttrDict.KeyFinal: str,
            AttrDict.KeyAny: int
        })

    def setitem_unvalid_data_test(self):
        """
        Test setitem with unvalid data
        """
        d = AttrDict({
            AttrDict.KeyAny: str,
            'a': str,
        })
        self.assertRaises(ValueError, d.__setitem__, AttrDict.KeyFinal, int)

        d = AttrDict({
            1: int,
            'a': str,
        })
        self.assertRaises(ValueError, d.__setitem__, AttrDict.KeyFinal, int)

        d = AttrDict({
            AttrDict.KeyFinal: str,
        })
        self.assertRaises(ValueError, d.__setitem__, 2, str)

    def validate_inclusion_valid_test(self):
        """
        test validate_inclusion with calling dict included in other
        """
        attr_dict = AttrDict({'a': int, 'c': int})
        other = AttrDict({'a': int, 'b': str, 'c': float})
        self.assertIsNone(attr_dict.validate_inclusion(other))

        attr_dict = AttrDict({'a': int, 'b': str, 'c': float})
        other = AttrDict({AttrDict.KeyAny: int})
        self.assertIsNone(attr_dict.validate_inclusion(other))

        attr_dict = AttrDict({AttrDict.KeyAny: int})
        other = AttrDict({AttrDict.KeyAny: float})
        self.assertIsNone(attr_dict.validate_inclusion(other))

        attr_dict = AttrDict({AttrDict.KeyFinal: str})
        other = AttrDict({AttrDict.KeyFinal: unicode})
        self.assertIsNone(attr_dict.validate_inclusion(other))

    def validate_inclusion_error_test(self):
        """
        test validate_inclusion with calling dict NOT included in other
        """
        attr_dict = AttrDict({0: int, 1: float})
        other = AttrDict({1: str, 2: int})
        self.assertRaises(NotIncludedError, attr_dict.validate_inclusion, other)
        
        attr_dict = AttrDict({AttrDict.KeyFinal: int})
        other = AttrDict({1: str})
        self.assertRaises(NotIncludedError, attr_dict.validate_inclusion, other)

        attr_dict = AttrDict({AttrDict.KeyAny: int})
        other = AttrDict({'a': int, 'b': str})
        self.assertRaises(NotIncludedError, attr_dict.validate_inclusion, other)

        attr_dict = AttrDict({AttrDict.KeyAny: int})
        other = AttrDict({'a': int, 'b': str})
        self.assertRaises(NotIncludedError, attr_dict.validate_inclusion, other)

        attr_dict = AttrDict({AttrDict.KeyFinal: int})
        other = AttrDict({AttrDict.KeyAny: int})
        self.assertRaises(NotIncludedError, attr_dict.validate_inclusion, other)
