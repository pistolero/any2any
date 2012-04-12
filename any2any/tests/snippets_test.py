# -*- coding: utf-8 -*-
import unittest

from any2any.node import *
from any2any.cast import *
from any2any.utils import *


class Validation_Test(unittest.TestCase):
    """
    This test shows how to load a simple validation framework
    on top of any2any
    """

    def validation_system_test(self):
        class ValidationError(Exception):
            
            def __init__(self):
                self.errors = {}
                self.non_field_errors = []

        class MyCast(Cast): pass

        class MyNode(MappingNode):

            @classmethod
            def load(cls, items_iter):
                items_dict = dict()
                error = None
                keys_seen = []
                while(1):
                    try:
                        key, value = items_iter.next()
                        items_dict[key] = value
                    except ValidationError as exc:
                        key = items_iter.last_key
                        error = error or ValidationError()
                        error.errors[key] = (exc.errors, exc.non_field_errors)
                    except StopIteration:
                        break
                    finally:
                        keys_seen.append(key)
                    
                if set(keys_seen) != set(['a', 'b', 'c']):
                    error = error or ValidationError()
                    error.non_field_errors.append('Need more keys')
                if error: raise error
                return super(MyNode, cls).load(items_dict.iteritems())

        cast = MyCast({
            ClassSet(dict): MyNode,
            AllSubSetsOf(object): IdentityNode
        })

        self.assertEqual(cast({'a': 1, 'b': 2, 'c': 3}), {'a': 1, 'b': 2, 'c': 3})
        self.assertRaises(ValidationError, cast, {'a': {'a': {'a': 1}}, 'b': 2, 'c': {'b': 2}})                
        try:
            cast({'a': {'a': {'a': 1}}, 'b': 2, 'c': {'b': 2}})
        except ValidationError as e:
            self.assertEqual(e.errors, {
                'a': (
                    {'a': ({}, ['Need more keys'])},
                    ['Need more keys']
                ),
                'c': ({}, ['Need more keys'])
            })
            self.assertEqual(e.non_field_errors, [])
