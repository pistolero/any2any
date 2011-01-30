"""
..
    >>> import os, sys
    >>> sys.path.append(os.path.abspath('../..'))
    >>> from spiteat.objectcast import *
    >>> from spiteat.base import *
    >>> import re

.. currentmodule:: spiteat.objectcast

:class:`ObjectCast` implements serializations with the following steps :

    #. **Decomposing**. Serialization of the object requires serialization of all its attributes.
    #. **Delegating**, which implies for each attribute :
    
        #. :ref:`Getting the attribute's value<accessors>`
        #. :ref:`Getting a serializer for the attribute<attr-serializers>`
        #. And finally using this serializer

    #. **Combining** in a dictionary **{<attr_name>: <serialized_value>}**

And deserializations :

    #. **Decomposing**. Deserialization of the object requires deserialization of all its attributes.
    #. **Delegating**. :ref:`Getting a serializer for each attribute<attr-serializers>` and using it.
    #. **Combining**, which implies :
    
        #. If not provided, creating a new object
        #. :ref:`Setting each of its attributes with the deserialized value<accessors>`

.. note:: For a fully working serializer you should at least subclass :meth:`ObjectCast.new_object`. Otherwise, the serializer wont be able to create new objects.

.. seealso:: :class:`ObjectCast.Settings` : settings available for instances of :class:`ObjectCast<>`.

How to customize an :class:`ObjectCast`
========================================

Selecting which attributes to handle
-------------------------------------

With the settings :attr:`ObjectCast.Settings.include` and :attr:`ObjectCast.Settings.exclude`, it is easy to specify which attributes should be handled by the cast.

    >>> # Creating some object
    >>> class SomeObject(object):
    ...     def __init__(self, a=0, b=1, c='C'):
    ...         self.a = a
    ...         self.b = b
    ...         self.c = c
    ...
    ...     def __repr__(self):
    ...         return 'SomeObject(%s, %s, %s)' % (self.a, self.b, self.c)
    ...
    >>> # Cast object to dictionary
    >>> someobj_to_dict = ObjectToDict(include=['a', 'b'])
    >>> someobj_to_dict(SomeObject(1, 2, 3)) == {'a': 1, 'b': 2}
    True
    >>> # Cast dictionary to object
    >>> dict_to_someobj = DictToObject(conversion=(dict, SomeObject), include=['a', 'b'])
    >>> dict_to_someobj({'a': 5, 'b': 'zouzou'})
    SomeObject(5, zouzou, C)

Notice that :attr:`exclude` takes precedence over :attr:`include` :

    >>> someobj_to_dict = ObjectToDict(conversion=(SomeObject, dict), include=['a', 'b', 'c'], exclude=['b', 'a'])
    >>> someobj_to_dict(SomeObject(1, 2, 3)) == {'c': 3}
    True

.. _attr-serializers:

Specifying the cast for a given attribute
-------------------------------------------------

With the setting :attr:`ObjectCast.Settings.attr_cast_map`, you can easily chose which cast should be used for a given atttribute.

    >>> class BoringCast(Cast):
    ...     def __call__(self, obj):
    ...         return 'BoringCast'
    ...
    >>> class TheOneIWant(Cast):
    ...     def __call__(self, obj):
    ...         return 'TheOneIWant'
    ...
    >>> someobj_to_dict = ObjectToDict(
    ...     include=['a'], 
    ...     cast_map={(object, object): BoringCast()},
    ...     attr_cast_map={'a': TheOneIWant()}
    ... )
    >>> someobj_to_dict(SomeObject()) == {'a': 'TheOneIWant'}
    True
    
.. note:: As you can see, :attr:`ObjectCast.attr_cast_map` takes precedence over :attr:`Cast.cast_map` 


.. _accessors:

Customizing attribute access
--------------------------------

The way :class:`ObjectCast` access an object's attribute is fully customizable thanks to :class:`Accessor`. An accessor defines two methods :meth:`Accessor.get_attr` and :meth:`Accessor.set_attr`. They are specified exactly like Python built-in :func:`getattr<>` and :func:`setattr<>`

Once you have declared a new accessor, you can use the settings :attr:`ObjectCast.Settings.class_accessor_map` or :attr:`ObjectCast.Settings.attr_accessor_map` to plug it into your cast :

    >>> class Son(object):
    ...     def __init__(self, firstname):
    ...         self.age = 1
    ...         self.firstname = firstname
    ...
    >>> class Father(object):
    ...     def __init__(self, son=None, fortunate_son=None, son_of_a_gun=None):
    ...         self.son = son
    ...         self.son_of_a_gun = son_of_a_gun
    ...         self.fortunate_son = fortunate_son
    ...
    >>> class SonAccessor(Accessor):
    ...     def get_attr(self, instance, name):
    ...         print 'SonAccessor, attr : %s' % name
    ...         return getattr(instance, name)
    ...
    >>> class SonOfAGunAccessor(Accessor):
    ...     def get_attr(self, instance, name):
    ...         print 'SonOfAGunAccessor, attr : %s' % name
    ...         return getattr(instance, name)
    ...
    >>> junior = Son('Jack') ; john = Son('John') ; pete = Son('Pete')
    >>> daddy = Father(junior, john, pete)
    >>> father_to_dict = ObjectToDict(
    ...     include=['son', 'fortunate_son', 'son_of_a_gun'],
    ...     class_accessor_map={object: SonAccessor()},
    ...     attr_accessor_map={'son_of_a_gun': SonOfAGunAccessor()},
    ... )
    >>> father_to_dict(daddy) == {'son': junior, 'fortunate_son': john, 'son_of_a_gun': pete}
    SonAccessor, attr : fortunate_son
    SonOfAGunAccessor, attr : son_of_a_gun
    SonAccessor, attr : son
    True

.. note:: Notice that :attr:`attr_accessor_map` takes precedence over :attr:`class_accessor_map`.

..
    ----- Testing log for ObjectCast
    >>> for h in logger.handlers:
    ...     logger.removeHandler(h)
    
    Adding a handler
    >>> from tempfile import TemporaryFile
    >>> fd = TemporaryFile()
    >>> import logging
    >>> h = logging.StreamHandler(fd)
    >>> logger.addHandler(h)
    >>> logger.setLevel(logging.DEBUG)
    
    Defining some casts
    >>> some_obj = SomeObject(1, SomeObject(2), 3)
    >>> anothercast = ObjectToDict(include=['a', 'c'])
    >>> somecast = ObjectToDict(include=['a', 'b', 'c'], attr_cast_map={'b': anothercast})
    
    Checking out the log of a cast
    >>> r = somecast(some_obj)
    >>> fd.seek(0)
    >>> print fd.read()
    spiteat.objectcast.ObjectToDict((<type 'object'>, <type 'dict'>)) <= SomeObject(1, SomeObject(2, 1, C), 3)
    Attribute a
        spiteat.base.Identity((<type 'object'>, <type 'object'>)) <= 1
        spiteat.base.Identity((<type 'object'>, <type 'object'>)) => 1
    Attribute c
        spiteat.base.Identity((<type 'object'>, <type 'object'>)) <= 3
        spiteat.base.Identity((<type 'object'>, <type 'object'>)) => 3
    Attribute b
        spiteat.objectcast.ObjectToDict((<type 'object'>, <type 'dict'>)) <= SomeObject(2, 1, C)
        Attribute a
            spiteat.base.Identity((<type 'object'>, <type 'object'>)) <= 2
            spiteat.base.Identity((<type 'object'>, <type 'object'>)) => 2
        Attribute c
            spiteat.base.Identity((<type 'object'>, <type 'object'>)) <= 'C'
            spiteat.base.Identity((<type 'object'>, <type 'object'>)) => 'C'
        spiteat.objectcast.ObjectToDict((<type 'object'>, <type 'dict'>)) => {'a': 2, 'c': 'C'}
    spiteat.objectcast.ObjectToDict((<type 'object'>, <type 'dict'>)) => {'a': 1, 'c': 3, 'b': {'a': 2, 'c': 'C'}}
    <BLANKLINE>
    <BLANKLINE>




"""

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.REPORT_ONLY_FIRST_FAILURE)
