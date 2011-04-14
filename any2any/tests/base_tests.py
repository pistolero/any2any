"""
..
    >>> import os, sys
    >>> sys.path.append(os.path.abspath('../..'))
    >>> from any2any.base import *
    >>> from any2any.simple import *

.. currentmodule:: any2any.base

Building a serializer
=========================

Constructor
----------------

..
    >>> class MyCustomCast(Cast):
    ...     defaults = CastSettings(
    ...         a_setting='',
    ...         another_setting='',
    ...     )

The constructor of a serializer takes settings as keyword arguments :

    >>> cast = MyCustomCast(mm=Mm(str, int), a_setting='blabla', another_setting={'bla': 'bla'})

Operation context
------------------

During an operation, it is useful to share some information with other methods that are also implied. For this purpose, a context variable is automatically created before each operation, and deleted when the operation is complete:

    >>> class SomeCast(Cast):
    ...     
    ...     def call(self, inpt):
    ...         print 'call', self._context['input']
    ...         self.sub_operation()
    ...     
    ...     def sub_operation(self):
    ...         print 'sub', self._context['input']
    ... 
    >>> cast = SomeCast()
    >>> cast._context == None
    True
    >>> cast.call('bla')
    call bla
    sub bla
    >>> cast._context == None
    True

Delegating operations
=======================

In order to enable delegating operations to other serializers, the following building blocks are provided : 

Getting a serializer for a given class
----------------------------------------

To get a serializer for a class use the method :func:`Cast.cast_for` :

    >>> from any2any.utils import Mm
    >>> cast = Cast()
    >>> class Dumb(object): pass
    >>> dumb_cast = cast.cast_for(Mm(Dumb, object))
    >>> isinstance(dumb_cast, Identity)
    True
    >>> obj_cast = cast.cast_for(Mm(object, object))
    >>> isinstance(obj_cast, Identity)
    True
    >>> list_cast = cast.cast_for(Mm(list, list))
    >>> isinstance(list_cast, ListToList)
    True

You can also pass a second argument in order to override the serializer's settings :

    >>> custom_cast = cast.cast_for(Mm(list, list), {'mm': Mm(set, dict)})
    >>> custom_cast.mm == Mm(set, dict)
    True

.. _configuring-cast_for:

Configuring the behaviour of :meth:`Cast.cast_for`
--------------------------------------------------

Of course, there wouldn't be much fun if you couldn't configure what serializer :meth:`Srz.srz_for` should pick for a given class. There is actually two ways to do this.

You can set a serializer as global default for a class, using the function :func:`register` :

    >>> from any2any.base import register
    >>> class DumbCast(Cast):
    ...     defaults = CastSettings(mm=Mm(Dumb, object))
    >>> dumb_cast = DumbCast()
    >>> register(dumb_cast, [Mm(Dumb, object)])
    >>> cast = Cast()
    >>> other_dumb_cast = cast.cast_for(Mm(Dumb, object))
    >>> isinstance(other_dumb_cast, DumbCast)
    True

..
    Testing that default for 'object' is still the same :
    >>> isinstance(cast.cast_for(Mm(object, object)), Identity)
    True

Note that the serializer returned by :meth:`Cast.cast_for` if not the one you registered :

    >>> dumb_cast == other_dumb_cast
    False

Indeed, :meth:`Srz.srz_for` doesn't return directly ``dumb_srz``, but a copy obtained by calling ``dumb_srz.copy()``. This in in order to allow overriding settings of the returned serializer. For example :

    >>> other_dumb_cast = cast.cast_for(Mm(Dumb, object), settings={'mm': Mm(Dumb, int)})
    >>> dumb_cast.mm
    Mm(<class '__main__.Dumb'>, <type 'object'>)
    >>> other_dumb_cast.mm
    Mm(<class '__main__.Dumb'>, <type 'int'>)

Second solution is to change the setting :attr:`Srz.Settings.class_srz_map`. This won't modify global defaults, but rather override them on the serializer level :
 
    >>> class MyCast(Cast): pass
    >>> cast = Cast()
    >>> mycast = MyCast()
    >>> custom_cast = Cast(mm_to_cast={Mm(int, object): mycast})
    >>> isinstance(custom_cast.cast_for(Mm(int, object)), MyCast)
    True
    >>> isinstance(cast.cast_for(Mm(int, object)), Identity) #Only the map of custom_cast is affected
    True
    >>> isinstance(custom_cast.cast_for(Mm(Dumb, object)), DumbCast) #However the global defaults still work 
    True

Other functionalities
=======================
    
Debugging
-----------

SpitEat logs all the calls to :meth:`spit` or :meth:`eat` to help debugging. By default, the logger's handler is :class:`NullHandler`, so no message is logged. To activate SpitEat's logging, just add any handler to :attr:`logger`, and set the logger's level to :attr:`DEBUG`.

For example, here we create a temporary file, and a :class:`StreamHandler` that will write to this file :

    >>> from tempfile import TemporaryFile
    >>> import logging
    >>> fd = TemporaryFile()
    >>> h = logging.StreamHandler(fd)

Then we set the handler's formatter (optional), add our handler to **SpitEat**'s logger and set the logging level to :attr:`DEBUG`.

    >>> from any2any.base import logger
    >>> logger.addHandler(h)
    >>> logger.setLevel(logging.DEBUG)

Finally, after a few spit/eat operations, we can chack that the logging worked : 

    >>> cast = Identity()
    >>> spitted = cast.call(1)
    >>> fd.seek(0)
    >>> print fd.read()
    any2any.simple.Identity(Mm(<type 'object'>, <type 'object'>)).call <= 1
    any2any.simple.Identity(Mm(<type 'object'>, <type 'object'>)).call => 1
    <BLANKLINE>
    <BLANKLINE>

..
    >>> logger.removeHandler(h)  
"""

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.REPORT_ONLY_FIRST_FAILURE)
