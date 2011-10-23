# -*- coding: utf-8 -*-
from nose.tools import assert_raises, ok_
from any2any.bundle import ObjectBundle


class ObjectBundle_Test(object):
    """
    Tests for the ObjectBundle class
    """

    def setUp(self):
        class AnObject(object): pass
        self.AnObject = AnObject

    def get_schema_test(self):
        """
        Test ObjectBundle.get_schema
        """
        # provided schema
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'a': int, 'b': str}
        ok_(ObjectWithSchema.get_schema() == {'a': int, 'b': str})
        # with exclude
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'a': int, 'b': str}
            exclude = ['a']
        ok_(ObjectWithSchema.get_schema() == {'b': str})
        # default schema
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'b': unicode, 'c': float})
        # default schema + exclude
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            exclude = ['b', 'c', 'd']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float})
        # default schema + extra_schema
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'a': unicode, 'd': str}
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': unicode, 'b': unicode, 'c': float, 'd': str})
        # default schema + extra_schema + exclude
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'a': unicode, 'd': str, 'e': int}
            exclude = ['d', 'a', 'b']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'c': float, 'e': int})
        # default schema + include
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            include = ['a', 'b']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'b': unicode})
        # default schema + extra_schema + include
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'d': str}
            include = ['a', 'd']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'a': float, 'd': str})
        # default schema + extra_schema + exclude + include
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'d': str, 'e': int}
            include = ['a', 'b', 'e']
            exclude = ['a']
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_schema() == {'b': unicode, 'e': int})

    def get_class_test(self):
        """
        Test ObjectBundle.get_class
        """
        # provided schema
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            extra_schema = {'a': int, 'b': str}
        ok_(ObjectWithSchema.get_class('a') == int)
        ok_(ObjectWithSchema.get_class('b') == str)
        assert_raises(KeyError, ObjectWithSchema.get_class, 'c')
        # default schema
        class ObjectWithSchema(ObjectBundle):
            klass = self.AnObject
            @classmethod
            def default_schema(self):
                return {'a': float, 'b': unicode, 'c': float}
        ok_(ObjectWithSchema.get_class('a') == float)
        ok_(ObjectWithSchema.get_class('b') == unicode)
        ok_(ObjectWithSchema.get_class('c') == float)
        assert_raises(KeyError, ObjectWithSchema.get_class, 'd')

    def getattr_test(self):
        """
        Test ObjectBundle.getattr
        """
        class AnObjectBundle(ObjectBundle):
            klass = self.AnObject
            def get_a(self):
                return 'blabla'
        obj = self.AnObject()
        obj.b = 'bloblo'
        bundle = AnObjectBundle(obj)
        ok_(bundle.getattr('a') == 'blabla')
        ok_(bundle.getattr('b') == 'bloblo')
                
    def setattr_test(self):
        """
        Test ObjectBundle.setattr
        """
        class AnObjectBundle(ObjectBundle):
            klass=self.AnObject
            def set_a(self, value):
                self.obj.a = 'bloblo'
        obj = self.AnObject()
        bundle = AnObjectBundle(obj)
        bundle.setattr('a', 'blibli')
        bundle.setattr('b', 'blabla')
        ok_(obj.a == 'bloblo')
        ok_(obj.b == 'blabla')
