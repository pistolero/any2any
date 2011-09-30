..
    >>> import os, sys
    >>> sys.path.append(os.path.abspath('../..'))
    >>> from any2any import *

.. currentmodule:: any2any.base

Basics
++++++++

Implementing a :class:`Cast`
=============================

Virtual methods
------------------

:class:`Cast` is a virtual class, and all subclasses must provide an implementation of :meth:`Cast.call`. For example :

    >>> from any2any import Cast
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

Defining or overriding new settings is very straightforward.

    >>> from any2any import Cast, CastSettings
    >>> class AnyToAnyBasestring(Cast):
    ...   
    ...     prefix = Setting(default='')    # new setting *prefix*
    ...     suffix = Setting(default='')    # new setting *suffix*
    ...     
    ...     class Meta:
    ...         defaults = {'to': str}
    ...
    ...     def call(self, inpt):
    ...         return self.to('%s%s%s' % (self.prefix, inpt, self.suffix))
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
    >>> cast._context == {}
    True
    >>> cast.call('bla')
    call bla
    sub bla blabla
    >>> cast._context == {}
    True

Other functionalities
=======================
    
Debugging
-----------

**any2any** logs all the calls in order to help debugging. By default, the logger's handler is :class:`NullHandler`, so no message is logged. To activate **any2any**'s logging, just add any handler to :attr:`logger`, and set the logger's level to :attr:`DEBUG`.

Finally, after a few calls, we can check that the logging worked : 

    >>> cast = Identity()
    >>> cast.set_debug_mode_on()
    >>> spitted = cast.call(1)
    >>> fd.seek(0)
    >>> print fd.read()
    any2any.simple.Identity().call <= 1
    any2any.simple.Identity().call => 1
    <BLANKLINE>
    <BLANKLINE>

..
    >>> logger.removeHandler(h)
