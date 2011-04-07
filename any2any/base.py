# -*- coding: utf-8 -*-
#'any2any'
#Copyright (C) 2011 Sébastien Piquemal @ futurice
#contact : sebastien.piquemal@futurice.com
#futurice's website : www.futurice.com

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
.. currentmodule:: any2any.base

This module defines the base casts.

.. todo:: even cooler logging (html page with cast settings and so on)
"""
# Logging 
#====================================
import logging

class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger()
logger.addHandler(NullHandler())

# Base serializer 
#====================================
import copy
import re
import collections
from functools import wraps
from types import FunctionType

from utils import Mm, specialize, copied_values

mm_to_cast = {}
"""
dict. This dictionary maps a :class:`Conversion` to a :class:`Cast`. This is any2any's global default mapping.
"""

def register(cast, use_for):
    """
    Registers *cast* as the default cast for every metamorphosis in *use_for*.
    """
    for mm in use_for:
        #no matter if cast for *mm* is already in the map, we override it
        mm_to_cast[mm] = cast


class CastSettings(collections.MutableMapping):
    """
    *settings* of a cast class or a cast instance. Constructor takes a dictionnary as argument:

        >>> CastSettings({
        ...     'my_setting': a_dict, 'spit_my_setting': another_dict,
        ...     'my_other_setting': 1,
        ...     '_schema': {'my_setting': {'update': 'update'}}
        ... })
    """

    def __init__(self, **settings):
        self._schema = settings.pop('_schema', {})
        self._values = dict()
        for name, value in settings.items():
            self._values[name] = value
            self._schema.setdefault(name, {})
        
    def __getitem__(self, name):
        try:
            return self._values[name]
        except KeyError:
            raise KeyError("Setting '%s' is not defined for this serializer" % name) 

    def __setitem__(self, name, value):
        if name in self:
            self._values[name] = value
        else:
            raise TypeError("Setting '%s' is not defined for this serializer" % name)

    def __delitem__(self, name):
        del self._values[name]
        del self._schema[name]

    def __contains__(self, name):
        return name in self._schema

    def __len__(self):
        return len(self._schema)

    def __iter__(self):
        return iter(self._values)

    def __copy__(self):
        settings_dict = dict(copied_values(self.items()))
        settings_dict['_schema'] = self._schema.copy()
        return self.__class__(**settings_dict)

    def override(self, settings):
        """
        Updates the calling instance with *settings*. The updating behaviour is taken from `_schema`

        Args:
            settings(dict).
        """

        #We don't change the schema, only add settings that didn't exist in the calling instance.
        for name, value in settings._schema.items():
            self._schema.setdefault(name, value)
        for name, value in settings.items():
            if name in self:
                if self._schema[name].get('update') == 'update':
                    new_value = self._values.get(name, {})
                    new_value.update(value)
                    self._values[name] = new_value
                else:
                    self._values[name] = value
            else:
                self._values[name] = value

    def configure(self, **settings):
        """
        Sets a bunch of settings:

            >>> settings.configure(setA='a value', spit_setB='some value')
        """
        for name, value in settings.items():
            self[name] = value


class CastType(type):

    def __new__(cls, name, bases, attrs):
        new_defaults = (attrs.pop('defaults', None))

        #trick to be able to wrap call later
        if attrs.get('call'):
            attrs['_original_call'] = attrs.pop('call')

        #just a trick because I don't want to mess up with MRO when overriding settings TODO: I'll have to :-(
        trash = super(CastType, cls).__new__(cls, name, bases, attrs)
        attrs['defaults'] = copy.copy(getattr(trash, 'defaults', None))
        if not attrs['defaults']:#Useful for the base serializer class `Cast`
            attrs['defaults'] = new_defaults

        #create new class
        new_cast_class = super(CastType, cls).__new__(cls, name, bases, attrs)
        if new_defaults:
            new_cast_class.defaults.override(new_defaults)

        #wrap *call* to automate logging and context management
        new_cast_class.call = cls.operation_wrapper(new_cast_class._original_call, new_cast_class)

        return new_cast_class

    #NB : For all wrappers, we should avoid raising errors if it is not justified ... not to mix-up the user. 
    #For example, if we had `_wrapped_func(self, inpt, *args, **kwargs)`, and we call `func` without a
    #parameter, the error will be raised from the wrapper, which will result in a confusing error message:
    #    TypeError: _wrapped_func() takes exactly 2 arguments (1 given)
    #That's why we prefer using `_wrapped_func(self, *args, **kwargs)`

    #NB2 : The wrappers use a hack to avoid executing the wrapping code when the operation is called with
    #    super(MyCast, self).operation(*args, **kwargs) 
    #`meta_wrapper(operation, cast_class)` builds a decorator that by-passes
    #all the wrapping code if `cast_class != type(self)`.

    @classmethod
    def meta_wrapper(cls, operation, cast_class):
        def _decorator(wrapped_operation):
            def _wrapped_again(self, *args, **kwargs):
                if (type(self) == cast_class):
                    return wrapped_operation(self, *args, **kwargs)
                else:
                    return operation(self, *args, **kwargs)
            return _wrapped_again
        return _decorator

    @classmethod
    def operation_wrapper(cls, operation, cast_class):
        @wraps(operation)
        @cls.meta_wrapper(operation, cast_class)
        def _wrapped_operation(self, *args, **kwargs):
            #context management : should be first, because logging might use it.
            self._context = {'input': args[0] if args else None}
            #logging
            self.log('%s.%s' % (self, operation.__name__) + ' <= ' + repr(args[0] if args else None), 'start', throughput=args[0] if args else None)
            #the actual operation
            returned = operation(self, *args, **kwargs)
            #logging
            self.log('%s.%s' % (self, operation.__name__) + ' => ' + repr(returned), 'end', throughput=returned)
            if self._depth == 0:
                self.log('')
            #context management
            self._context = None
            return returned
        return _wrapped_operation

class Cast(object):
    """
    Base class for all serializers. This class is virtual, and all subclasses must implement :meth:`spit` and :meth:`eat`.

        >>> my_cast = MyCastClass(mm=SomeClass, some_setting='some value')

    Settings available for instances of :class:`Cast` :

    dict. This is a dict ``{<class>: <srz>}``. It allows to specify which serializer :meth:`Srz.srz_for` should pick for a given class.

    .. seealso:: :ref:`How<configuring-srz_for>` to use *mm_to_cast*.

    type. The class the serializer is customized for.

    list. When calling :meth:`srz_for`, all settings whose name are in this list will be transmitted from the calling serializer to the returned serializer (if this serializer defines them).

    .. todo:: FIXME : propagate breaks if different serializer type in between ...

    bool. If True, the serializer writes debug to the logger.
    """

    __metaclass__ = CastType

    defaults = CastSettings(
        _schema={
            'mm_to_cast': {
                'update': 'update',
            }
        },
        mm_to_cast={},
        mm=None,
        propagate=['mm_to_cast', 'propagate'],
        logs=True,
    )

    def __new__(cls, *args, **kwargs):
        new_cast = super(Cast, cls).__new__(cls)
        new_cast.settings = copy.copy(cls.defaults)
        return new_cast

    def __init__(self, **settings):
        self._context = None #operation context
        self._depth = 0 #used for logging
        self.settings.configure(**settings)

    def __repr__(self):
        return '.'.join([self.__class__.__module__, '%s(%s)' % (self.__class__.__name__, self.mm)]) 

    def cast_for(self, mm, settings={}):
        """
        Returns:
            Cast. A cast suitable for objects of type *mm*, and customized with *settings*.

        .. seealso:: :ref:`How<configuring-srz_for>` to control the behaviour of *srz_for*.
        """
        #builds all choices from global map and local map
        choices = mm_to_cast.copy()
        choices.update(self.mm_to_cast)
        #gets better choice
        closest_mm = mm.pick_closest_in(choices.keys())
        cast = choices[closest_mm]
        return cast.copy(settings, self)

    def copy(self, settings, cast=None):
        """
        Returns:
            Cast. A copy of the calling serializer, whose settings are overriden in the following order:
                
                #. settings of *cast* (in respect to *cast*'s :attr:`propagate` attribute).
                #. *settings*
        """
        new_cast = copy.copy(self)
        if cast:
            new_cast._depth = cast._depth + 1
            for name in cast.propagate:
                new_cast.settings.configure(**{name: copy.copy(getattr(cast, name))})
        new_cast.settings.configure(**settings)
        return new_cast

    def call(self, inpt):
        """
        Serializes *obj*.
        """
        raise NotImplementedError('This class is virtual')

    def log(self, message, state='during', throughput=None):
        """
        Logs a message to **SpitEat**'s logger.

        Args:
            state(str). 'start', 'during' or 'end' depending on the state of the operation when the logging takes place. 
        """
        if self.logs:
            indent = ' ' * 4 * self._depth
            extra = {
                'cast': self,
                'throughput': throughput,
                'settings': self.settings,
                'state': state,
            }
            logger.debug(indent + message, extra=extra)

    def __copy__(self):
        copied_cast = self.__class__()
        copied_cast.settings = copy.copy(self.settings)
        return copied_cast

    def __getattr__(self, name):
        #This allows to get the settings like normal attributes
        try:
            return self.settings[name]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" % (self, name))

