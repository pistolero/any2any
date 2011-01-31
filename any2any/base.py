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

.. todo:: maps in settings could be updated (with parent_default.update(child_default)) so you don't have to redefine it completely when subclassing
"""
# Logging 
#====================================
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
formatter = logging.Formatter("%(message)s")
logger = logging.getLogger()
logger.addHandler(NullHandler())

# Base class for casts 
#====================================
import copy
from functools import wraps
from types import FunctionType

from utils import closest_conversion, specialize, FROM, TO
from validation import validate_input, ValidationError

cast_map = {}
"""
dict. This dictionary maps a conversion **(<from>, <to>)** to a :class:`Cast`.
"""

def register(cast, conversions=[]):
    """
    If *conversions* is not empty, this function registers *cast* as the default cast for every conversion in *conversions*.
    """
    if conversions:
        for conversion in conversions:
            #no matter if cast for *conversion* is already in the map, we override it
            cast_map[conversion] = cast

class CastClassSettings(object):
    """
    *settings* of a cast class. Takes a setting placeholder (``class Settings: ...``) as unique argument.
    """
    def __init__(self, placeholder):
        settings = placeholder.__dict__.copy()
        self.schema = settings.pop('_schema', {})
        setting_names = filter(lambda n: n[0] != '_', list(settings))
        for name in setting_names:
            self.schema.setdefault(name, {})
            setattr(self, name, settings[name])

    def items(self):
        return ((name, getattr(self, name)) for name in self.schema)

    def update(self, settings):
        for name, value in settings.schema.items():
            self.schema.setdefault(name, value)
        for name, value in settings.items():
            if self.schema[name].get('inheritance') == 'update':
                new_value = getattr(self, name, {})
                new_value.update(value)
            else:
                new_value = value
            setattr(self, name, new_value)

    def copy(self):
        class Placeholder: pass
        placeholder = Placeholder()
        for name, value in self.items():
            setattr(placeholder, name, value)
            placeholder.schema = self.schema.copy() #TODO : should that be a deepcopy ? 
        return CastClassSettings(placeholder)

    def __iter__(self):
        return self.items()

    def __contains__(self, setting):
        return setting in self.schema


class CastMetaclass(type):

    def __new__(cls, name, bases, attrs):
        new_settings = CastClassSettings(attrs.get('Settings', object))
        #Just a trick to get parent's settings without messing-up with mro
        trash = super(CastMetaclass, cls).__new__(cls, name, bases, attrs)
        #We give the new class a copy of its parent's settings
        attrs['settings'] = getattr(trash, 'settings', new_settings).copy()

        #wrap *__call__* to automate logging
        if '__call__' in attrs:
            attrs['__call__'] = cls.log_wrapper(attrs['__call__'])
            attrs['__call__'] = cls.validators_wrapper(attrs['__call__'])

        #create new class
        new_cast_class = super(CastMetaclass, cls).__new__(cls, name, bases, attrs)
        new_cast_class.settings.update(new_settings)

        return new_cast_class

    @staticmethod
    def log_wrapper(func):
        @wraps(func)
        def _wraped_func(self, obj, *args, **kwargs):
            self.log(str(self) + ' <= ' + repr(obj))
            returned = func(self, obj, *args, **kwargs)
            self.log(str(self) + ' => ' + repr(returned))
            if self._depth == 0:
                self.log('')
            return returned
        return _wraped_func

    @staticmethod
    def validators_wrapper(func):
        @wraps(func)
        def _wraped_func(self, obj, *args, **kwargs):
            for validator in self.validators:
                validator(self, obj)
            return func(self, obj, *args, **kwargs)
        return _wraped_func

class Cast(object):
    """
    Base class for all casts. This class is virtual, all subclasses MUST implement :meth:`__call__`, and CAN declare new settings or override parent settings. For example :

        >>> class CastSubclass(Cast):
        ...
        ...     class Settings:
        ...         a_new_setting = 'its_default_value'
        ...         conversion = (int, str) # Overriden setting, new default value 

        ...     def __call__(self, input):
        ...         # ...
        ...         return output
        ...

    Then, all declared settings are available as keyword arguments. Parent settings being inherited they are available too ::

        >>> cast = CastSubclass(a_new_setting='my value', propagate=['a_new_setting'])
        >>> cast.conversion = (int, str) #Overriden default value
        True
        >>> cast.cast_map == {} #Inherited default value
        True
        >>> cast.a_new_setting #Our new setting, configured with a different value on this instance
        'my value'
    """

    __metaclass__ = CastMetaclass

    class Settings:
        """
        Settings available for instances of :class:`Cast` :
        """

        _schema = {
            'cast_map': {
                'inheritance': 'update',
            }
        }

        cast_map = {}
        """
        {(type, type): Cast}. This is a dict **{<conversion>: <cast>}**. It allows to control the behaviour of :meth:`cast_for`.
        """

        conversion = (object, object)
        """
        (type, type). The conversion this cast realizes.
        """

        propagate = ['cast_map', 'propagate']
        """
        list. When calling :meth:`cast_for`, all settings whose name are in this list will be transmitted from the calling cast to the returned cast (if this cast defines them).

        .. todo:: FIXME : propagate breaks if different serializer type in between ...
        """

        validators = [validate_input,]
        """
        list. A list of validator functions. Those functions must accept two arguments : the cast and the input value, and raise :class:`ValidationError` if validation has failed. For example :

            >>> def validate_gt_0(cast, input_val):
            ...     if not input_val > 0:
            ...         raise ValidationError 
        """


    def __new__(cls, *args, **kwargs):
        #set the cast's settings with all the default values.
        new_cast = super(Cast, cls).__new__(cls)
        for name, value in cls.settings.items():
            setattr(new_cast, name, value)
        return new_cast

    def __init__(self, **settings):
        self.configure(**settings)
        self._depth = 0 #used for logging

    def __repr__(self):
        return '.'.join([self.__class__.__module__, '%s(%s)' % (self.__class__.__name__, self.conversion)]) 

    def cast_for(self, conversion, settings={}):
        """
        Returns:
            Cast. The cast to use for *conversion*. To find the right typecast, any2any looks-up for the closest *conversion* in :

                #. calling cast's :attr:`cast_map` setting.
                #. any2any's global :attr:`cast_map`.
        """
        #builds all choices from global map and local map
        choices = cast_map.copy()
        choices.update(self.cast_map)
        #gets better choice
        chosen = closest_conversion(conversion, choices.keys())
        cast = choices[chosen]
        return cast.copy(settings, self)

    def copy(self, settings, cast=None):
        """
        Returns:
            Cast. A copy of the calling cast with its settings overriden.

        Args:
            cast(Cast). All settings in *cast*'s :attr:`propagate` will be transmitted to the returned cast.
            settings(dict). All settings in this dictionary will override the returned cast's settings (including settings transmitted from *cast*).
        """
        new_cast = copy.deepcopy(self)
        if cast:
            new_cast._depth = cast._depth + 1
            for name in cast.propagate:
                new_cast.configure(**{name: copy.copy(getattr(cast, name))})
        new_cast.configure(**settings)
        return new_cast
    
    def __call__(self, obj):
        raise NotImplementedError('This class is virtual')

    def configure(self, **settings):
        """
        Configure the calling cast's *settings*. For example :
        
            >>> cast.configure(conversion=(int, str), a_setting='some_value')
        """
        for name, value in settings.items():
            if name in self.settings:
                setattr(self, name, value)
            else:
                raise TypeError("Setting '%s' is not defined for casts of class %s" % (name, self.__class__))

    def log(self, message):
        """
        Logs a message to **any2any**'s logger.
        """
        indent = ' ' * 4 * self._depth
        logger.debug(indent + message)

# Simple serializers for base types
#====================================
class Identity(Cast):
    """
    Identity operation. Default cast for the conversion **(object, object)**.

        >>> Identity()('1')
        '1'
    """

    def __call__(self, obj):
        return obj

class ContainerCast(Cast):
    """
    Base cast for container types. This class is virtual. The casting goes this way ::

        SomeContainer(obj1, ..., objN) ----> SomeContainer(obj1_converted, ..., objN_converted)

    Which means that only the content is converted.
    """

    class Settings:
        conversion = (object, object)

    @classmethod
    def new_container(cls):
        """
        Returns an empty container.
        """
        raise NotImplementedError('This class is virtual')

    @classmethod
    def container_iter(cls, container):
        """
        Returns an iterator on pairs **(index, value)**, where *index* and *value* are such as ::
        
            container[index] == value
        """
        raise NotImplementedError('This class is virtual')

    @classmethod
    def container_insert(cls, container, index, value):
        """
        Inserts *value* at *index* in container.
        """
        raise NotImplementedError('This class is virtual')

    @classmethod
    def reset_container(self, container):
        """
        Empties *container*.
        """
        raise NotImplementedError('This class is virtual')

    def __call__(self, obj):
        new_container = self.new_container()
        elem_conversion = (self.conversion[FROM].feature, self.conversion[TO].feature)
        elem_cast = self.cast_for(elem_conversion, {'conversion': elem_conversion})
        for index, value in self.container_iter(obj):
            self.container_insert(new_container, index, elem_cast(value))
        return new_container

class MappingCast(ContainerCast):
    """
    Cast for dictionaries.

        >>> MappingCast()({'1': anObject1, '2': anObject2})
        {'1': 'its converted version 1', '2': 'its converted version 2'}
    """
    
    @classmethod
    def new_container(cls):
        return dict()
    
    @classmethod
    def container_iter(cls, container):
        return container.items()
    
    @classmethod
    def container_insert(cls, container, index, value):
        container[index] = value

    @classmethod
    def reset_container(cls, container):
        container.clear()
    

class SequenceCast(ContainerCast):
    """
    Cast for lists and tuples.

        >>> SequenceCast()([anObject1, anObject2])
        ['its converted version 1', 'its converted version 2']
    """

    @classmethod
    def new_container(cls):
        return list()
    
    @classmethod
    def container_iter(cls, container):
        return enumerate(container)
    
    @classmethod
    def container_insert(cls, container, index, value):
        container.insert(index, value)

    @classmethod
    def reset_container(cls, container):
        for index in range(0, len(container)):
            container.pop()
