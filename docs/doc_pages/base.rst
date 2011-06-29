..
    >>> import os, sys
    >>> sys.path.append(os.path.abspath('../..'))
    >>> from any2any.base import *
    >>> from any2any.simple import *

.. currentmodule:: any2any.base

Basics
++++++++

Implementing a :class:`Cast`
=============================

Virtual methods
------------------

:class:`Cast` is a virtual class, and all subclasses must be provide an implementation of :meth:`Cast.call`. For example :

    >>> from any2any.base import Cast
    >>> class AnyToString(Cast):
    ...     
    ...     def call(self, inpt):
    ...         return '%s' % inpt
    ...
    >>> cast = AnyToString()
    >>> cast(1)
    '1'

Defining/overriding settings
------------------------------

Defining or overriding new settings if very straightforward.

    >>> from any2any.base import Cast, CastSettings
    >>> class AnyToAnyBasestring(Cast):
    ...   
    ...     defaults = CastSettings(
    ...         prefix = '',                # new setting *prefix*
    ...         suffix = '',                # new setting *suffix*
    ...         to = str,                   # override value of Cast's *to* setting
    ...     )
    ...     
    ...     def call(self, inpt):
    ...         output_class = self.to
    ...         return output_class('%s%s%s' % (self.prefix, inpt, self.suffix))
    ... 

The constructor of a cast accepts any defined setting as keyword argument :

    >>> cast = AnyToAnyBasestring(to=unicode, prefix='value:')
    >>> cast(88)
    u'value:88'

Other settings take the class' default value :

    >>> cast.suffix
    ''

Operation context
------------------

When calling a cast, it can be useful for several methods to share data. For this purpose, a *_context* dictionary is automatically created before each call, and deleted when the call returns :

    >>> class SomeCast(Cast):
    ...     
    ...     def call(self, inpt):
    ...         print 'call', self._context['input']
    ...         self._context['bla'] = 'blabla'
    ...         self.sub_operation()
    ...     
    ...     def sub_operation(self):
    ...         print 'sub', self._context['input'], self._context['bla']
    ... 
    >>> cast = SomeCast()
    >>> cast._context == None
    True
    >>> cast.call('bla')
    call bla
    sub bla blabla
    >>> cast._context == None
    True

Looking-up for a suitable cast
===============================

The :meth:`Cast.cast_for` method
-----------------------------------

..
    >>> class MyCast(Cast):
    ...     def call(self): pass

To get a cast suitable for a given metamorphosis use the method :func:`Cast.cast_for` on a cast instance :

    >>> from any2any.utils import Metamorphosis
    >>> list_cast = cast.cast_for(Metamorphosis(list, list))

**any2any** comes with a set of defaults. For example, :class:`ListToList` is the default cast for casting a list to another list :

    >>> isinstance(list_cast, ListToList)
    True

The cast :class:`Identity` is always used as a fallback in case there isn't a better choice :

    >>> from any2any.utils import Mm # Mm is a shorthand for Metamorphosis
    >>> class Dumb(object): pass
    >>> cast = cast.cast_for(Mm(Dumb, object))
    >>> isinstance(cast, Identity)
    True

.. _configuring-cast_for:

Configuring the behaviour of :meth:`Cast.cast_for`
--------------------------------------------------

Of course, there wouldn't be much fun if you couldn't configure what cast :meth:`Cast.cast_for` should pick for a given metamorphosis. There is actually two ways to do this.

**First solution**

You can register a cast as global default for a metamorphosis, using the function :func:`register` :

    >>> from any2any.base import register
    >>> class AnyToAnyBasestring(Cast):
    ...   
    ...     defaults = CastSettings(
    ...         to = str,
    ...     )
    ...     
    ...     def call(self, inpt):
    ...         output_class = self.to
    ...         return output_class('%s' % inpt)
    ...
    >>> default_any2str = AnyToAnyBasestring()
    >>> register(default_any2str, Mm(from_any=object, to_any=basestring))

Then :meth:`Cast.cast_for` will pick it if it is the best match

    >>> cast = MyCast()
    >>> any2str = cast.cast_for(Mm(int, str))
    >>> isinstance(any2str, AnyToAnyBasestring)
    True

Note that the cast returned by :meth:`Cast.cast_for` if not the instance you registered ... it is a copy customized for your needs :

    >>> any2str.from_ == int
    True
    >>> default_any2str.from_ == None
    True

This allows the returned cast to be a little more clever, and output the requested type :

    >>> any2str(1)
    '1'
    >>> any2unicode = cast.cast_for(Mm(int, unicode))
    >>> any2unicode(1)
    u'1'

**Second solution**

You can change the setting :attr:`mm_to_cast`. This won't modify global defaults, but rather override them on a cast instance level :
 
    >>> class AnyToCapitalStr(Cast):
    ...     
    ...     def call(self, inpt):
    ...         return ('%s' % inpt).upper()
    ... 
    >>> cast = MyCast()
    >>> custom_cast = MyCast(mm_to_cast={Mm(from_any=object, to=str): AnyToCapitalStr()})
    >>> any2str = custom_cast.cast_for(Mm(object, str))
    >>> any2str('coucou') # Choice for Mm(object, str) is overriden on instance level 
    'COUCOU'
    >>> any2str = cast.cast_for(Mm(object, str))
    >>> any2str('coucou') # For other casts, global defaults still work 
    'coucou'
    >>> any2unicode = custom_cast.cast_for(Mm(object, unicode))
    >>> any2unicode('coucou') # For other metamorphoses, defaults still work
    u'coucou'

Other functionalities
=======================
    
Debugging
-----------

**any2any** logs all the calls in order to help debugging. By default, the logger's handler is :class:`NullHandler`, so no message is logged. To activate **any2any**'s logging, just add any handler to :attr:`logger`, and set the logger's level to :attr:`DEBUG`.

For example, here we create a temporary file, and a :class:`StreamHandler` that will write to this file :

    >>> from tempfile import TemporaryFile
    >>> import logging
    >>> fd = TemporaryFile()
    >>> h = logging.StreamHandler(fd)

Then we set the handler's formatter (optional), add our handler to **any2any**'s logger and set the logging level to :attr:`DEBUG`.

    >>> from any2any.base import logger
    >>> logger.addHandler(h)
    >>> logger.setLevel(logging.DEBUG)

Finally, after a few calls, we can check that the logging worked : 

    >>> cast = Identity(logs=True)
    >>> spitted = cast.call(1)
    >>> fd.seek(0)
    >>> print fd.read()
    any2any.simple.Identity(<type 'int'>->None).call <= 1
    any2any.simple.Identity(<type 'int'>->None).call => 1
    <BLANKLINE>
    <BLANKLINE>

..
    >>> logger.removeHandler(h)
