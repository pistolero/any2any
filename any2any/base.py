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
import abc
import collections
from functools import wraps
from types import FunctionType

from utils import Mm, Spz, copied_values

mm_to_cast = {}
"""
dict. This dictionary maps a :class:`Conversion` to a :class:`Cast`. This is any2any's global default mapping.
"""

def register(cast, mm):
    """
    Registers *cast* as the default cast for metamorphosis *mm*.
    """
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
        schema = settings.pop('_schema', {})
        self._schema = dict.fromkeys(settings, {})
        self._schema.update(schema)
        self._values = dict()
        self.update(settings)
        
    def __getitem__(self, name):
        try:
            return self._values[name]
        except KeyError:
            raise KeyError("%s" % name) 

    def __setitem__(self, name, value):
        if name in self:
            type_check = self._schema[name].get('type', None)
            if type_check and not isinstance(value, type_check):
                raise TypeError("Value for setting '%s' must be of type '%s'" % (name, type_check))
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
        for name, value in settings._schema.items():
            if name in self._schema:
                self._schema[name].update(value)
            else:
                self._schema[name] = value
        for name, value in settings.items():
            meth = self._schema[name].get('override', '__setitem__')
            getattr(self, meth)(name, value)

    def update_item(self, name, value):
        new_value = self.get(name, None)
        if new_value: new_value.update(value)
        self[name] = new_value or value

class CastType(abc.ABCMeta):

    def __new__(cls, name, bases, attrs):
        # handling multiple inheritance of defaults
        new_defaults = attrs.pop('defaults', CastSettings())
        attrs['defaults'] = CastSettings()
        cast_bases = filter(lambda b: isinstance(b, CastType), bases)
        if cast_bases:
            for base in reversed(cast_bases):
                attrs['defaults'].override(base.defaults)
            attrs['defaults'].override(new_defaults)
        else: #in the case the new class is Cast itself
            attrs['defaults'] = new_defaults

        #create new class
        new_cast_class = super(CastType, cls).__new__(cls, name, bases, attrs)
        if new_defaults:
            new_cast_class.defaults.override(new_defaults)

        #wrap *call* to automate logging and context management
        new_cast_class.call = cls.operation_wrapper(new_cast_class.call, new_cast_class)

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
        mm_to_cast = {},
        mm = Mm(object, object),
        propagate = ['mm_to_cast', 'propagate'],
        logs = True,
        _schema = {
            'mm_to_cast': {'override': 'update_item'},
            'mm': {'type': Mm}
        },
    )

    def __new__(cls, *args, **kwargs):
        new_cast = super(Cast, cls).__new__(cls)
        new_cast.settings = copy.copy(cls.defaults)
        return new_cast

    def __init__(self, **settings):
        self._context = None #operation context
        self._depth = 0 #used for logging
        self.settings.update(settings)

    def __repr__(self):
        return '.'.join([self.__class__.__module__, '%s(%s)' % (self.__class__.__name__, self.mm)]) 

    def cast_for(self, mm):
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
        # We set the cast's mm
        return cast.copy({'mm': mm}, self)

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
                new_cast.settings.update({name: copy.copy(getattr(cast, name))})
        new_cast.settings.update(settings)
        return new_cast

    @abc.abstractmethod
    def call(self, inpt):
        """
        Serializes *obj*.
        """
        return

    def __call__(self, inpt):
        return self.call(inpt)

    def __copy__(self):
        copied_cast = self.__class__()
        copied_cast.settings = copy.copy(self.settings)
        return copied_cast

    def __getattr__(self, name):
        #This allows to get the settings like normal attributes
        try:
            return self.settings[name]
        except KeyError:
            pass

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
