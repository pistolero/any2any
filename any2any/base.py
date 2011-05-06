# -*- coding: utf-8 -*-
"""
.. currentmodule:: any2any.base
"""
# Logging 
#====================================
# TODO : even cooler logging (html page with cast settings and so on)
# anyways, logging needs a bit refactoring.
import logging

class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger()
logger.addHandler(NullHandler())

# Cast 
#====================================
import copy
import re
try:
    import abc
except ImportError:
    from compat import abc
import collections
from functools import wraps
from types import FunctionType

from utils import Mm, Spz, copied_values

mm_to_cast = {}
"""
dict. This dictionary maps a :class:`Mm` to a :class:`Cast`. This is any2any's global default mapping.
"""

def register(cast, mm):
    """
    Registers *cast* as the default cast for metamorphosis *mm*.
    """
    mm_to_cast[mm] = cast


class CastSettings(collections.MutableMapping):
    """
    *settings* of a cast class or a cast instance. It implements :class:`collections.MutableMapping`, and is therefore usable as a dictionary :

        >>> c = CastSettings(my_setting={'a': 1}, my_other_setting=1)
        >>> c['my_other_setting']
        1

    The constructor optionally takes a keyword `_schema` that allows to configure different things for a given setting. For each setting, the schema can contain :

    - *type* : an exception is thrown if the setting's value isn't an instance of `type` :

        >>> c = CastSettings(my_setting=1, _schema={'my_setting': {'type': int}})
        >>> c['my_setting'] = 'a' #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        TypeError: message

    - *override* : method to use when overriding the setting :

        >>> c = CastSettings(my_setting={'a': 1}, _schema={'my_setting': {'override': 'update_item'}})
        >>> c.override({'my_setting': {'b': 2}})
        >>> c['my_setting'] == {'a': 1, 'b': 2}
        True

    - *customize* : method to use when customizing the setting :

        >>> c = CastSettings(my_setting={'a': 1}, _schema={'my_setting': {'customize': 'update_item'}})
        >>> c.customize({'my_setting': {'b': 2}})
        >>> c['my_setting'] == {'a': 1, 'b': 2}
        True
    """
    """
    - *delegate* : synchronizes two settings together :

        >>> c1 = CastSettings(my_setting=1)
        >>> c2 = CastSettings(another_setting=56, _schema={'another_setting': {'delegate': 'my_setting'}})
        >>> c1.override(c2)
        >>> c['my_setting'] == 56
        True
        >>> c['another_setting'] = 59
        >>> c['my_setting']
        59
    """
    def __init__(self, _schema={}, **settings):
        # initializing the schema
        self._schema = dict.fromkeys(settings, {})
        self._schema.update(_schema)
        for name, value in _schema.items():
            # TODO: Not quite working yet, cause problems with overriding
            if 'delegate' in value:
                delegate = value['delegate']
                if not delegate in self:
                    raise ValueError("Invalid 'delegate', setting '%s' is not defined" % delegate)
                _delegated_by = self._schema[delegate].setdefault('_delegated_by', [])
                _delegated_by.append(name)
        # initializing the values
        self._values = dict()
        self.update(settings)
        
    def __getitem__(self, name):
        try:
            return self._values[name]
        except KeyError:
            raise KeyError("%s" % name) 

    def __setitem__(self, name, value):
        if name in self:
            # handling type checking
            type_check = self._schema[name].get('type', None)
            if type_check and not isinstance(value, type_check):
                raise TypeError("Value for setting '%s' must be of type '%s'" % (name, type_check))
            # handling delegation
            delegate = self._schema[name].get('delegate', None)
            _delegated_by = self._schema[name].get('_delegated_by', [])
            to_update = _delegated_by + ([delegate] if delegate else [])
            for uname in to_update:
                self._values[uname] = value
            # at last, setting the value
            self._values[name] = value
        else:
            raise TypeError("Setting '%s' is not defined" % name)

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
        settings_dict = dict(copied_values(self.items())) # TODO: Why oh why ?
        settings_dict['_schema'] = self._schema.copy()
        return self.__class__(**settings_dict)

    def override(self, settings):
        """
        Updates the calling instance and its schema with *settings*. The updating behaviour is taken from `_schema`. This method shall be used for inheritance of settings between two classes.
        """
        # Handling schema updating
        if isinstance(settings, CastSettings):
            for name, value in settings._schema.items():
                if name in self._schema:
                    self._schema[name].update(value)
                else:
                    self._schema[name] = value
        # Handling settings updating
        for name, value in settings.items():
            meth = self._schema[name].get('override', '__setitem__')
            getattr(self, meth)(name, value)

    def customize(self, settings):
        """
        Updates the calling instance with *settings*. The updating behaviour is taken from `_schema`. This method shall be used for transmission of settings between two cast instances.
        """
        for name, value in settings.items():
            try:
                meth = self._schema[name].get('customize', '__setitem__')
            except KeyError:
                pass #TODO : propagation of setting breaks if different cast type in between ...
            else:
                getattr(self, meth)(name, value)   

    def update_item(self, name, value):
        new_value = self.get(name, None)
        if new_value: new_value.update(value)
        self[name] = new_value or value

    def do_nothing(self, name, value):
        pass


class CastType(abc.ABCMeta):

    def __new__(cls, name, bases, attrs):
        # handling multiple inheritance of defaults
        new_defaults = attrs.pop('defaults', CastSettings())
        cast_bases = filter(lambda b: isinstance(b, CastType), bases)
        if cast_bases:
            attrs['defaults'] = CastSettings()
            for base in reversed(cast_bases):
                attrs['defaults'].override(base.defaults)
            attrs['defaults'].override(new_defaults)
        else: # in the case the new class is Cast itself
            attrs['defaults'] = new_defaults

        # creating new class
        new_cast_class = super(CastType, cls).__new__(cls, name, bases, attrs)

        # wrapping *call* to automate logging and context management
        new_cast_class.call = cls.operation_wrapper(new_cast_class.call, new_cast_class)

        return new_cast_class

    # NB : For all wrappers, we should avoid raising errors if it is not justified ... not to mix-up the user. 
    # For example, if we had `_wrapped_func(self, inpt, *args, **kwargs)`, and we call `func` without a
    # parameter, the error will be raised from the wrapper, which will result in a confusing error message:
    #     TypeError: _wrapped_func() takes exactly 2 arguments (1 given)
    # That's why we prefer using `_wrapped_func(self, *args, **kwargs)`

    # NB2 : The wrappers use a hack to avoid executing the wrapping code when the operation is called with
    #     super(MyCast, self).operation(*args, **kwargs) 
    # `meta_wrapper(operation, cast_class)` builds a decorator that by-passes
    # all the wrapping code if `cast_class != type(self)`.

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
            # context management : should be first, because logging might use it.
            self._context = {'input': args[0] if args else None}
            # logging
            self.log('%s.%s' % (self, operation.__name__) + ' <= ' + repr(args[0] if args else None), 'start', throughput=args[0] if args else None)
            # the actual operation
            returned = operation(self, *args, **kwargs)
            # logging
            self.log('%s.%s' % (self, operation.__name__) + ' => ' + repr(returned), 'end', throughput=returned)
            if self._depth == 0:
                self.log('')
            # context management
            self._context = None
            return returned
        return _wrapped_operation


class Cast(object):
    """
    Base class for all casts. This class is virtual, and all subclasses must implement :meth:`Cast.call`.

    :class:`Cast` defines the following settings :

        - mm_to_cast(dict). ``{<mm>: <cast>}``. It allows to specify which cast :meth:`Cast.cast_for` should pick for a given metamorphosis (see also : :ref:`How<configuring-cast_for>` to use *mm_to_cast*).

        - mm(:class:`utils.Mm`). The metamorphosis the cast is customized for.

        - logs(bool). If True, the cast writes debug to :var:`logger`.
    """

    __metaclass__ = CastType

    defaults = CastSettings(
        mm_to_cast = {},
        mm = Mm(object, object),
        logs = False,
        _schema = {
            'mm_to_cast': {'override': 'update_item'},
            'mm': {'type': Mm, 'customize': 'do_nothing'},
        },
    )

    def __new__(cls, *args, **kwargs):
        new_cast = super(Cast, cls).__new__(cls)
        new_cast.settings = copy.copy(cls.defaults)
        return new_cast

    def __init__(self, **settings):
        self._context = None # operation context
        self._depth = 0 # used for logging
        self.settings.update(settings)

    def __repr__(self):
        return '.'.join([self.__class__.__module__, '%s(%s)' % (self.__class__.__name__, self.mm)]) 

    def cast_for(self, mm):
        """
        Returns:
            Cast. A cast suitable for metamorphosis *mm*, and overriden with calling cast's settings.

        .. seealso:: :ref:`How<configuring-cast_for>` to control the behaviour of *cast_for*.
        """
        # builds all choices from global map and local map
        choices = mm_to_cast.copy()
        choices.update(self.mm_to_cast)
        # gets better choice
        closest_mm = mm.pick_closest_in(choices.keys())
        cast = choices[closest_mm]
        # builds a customized version of the cast, override settings
        new_cast = cast.copy({'mm': mm})
        new_cast._depth = cast._depth + 1
        new_cast.settings.customize(self.settings)
        return new_cast

    def copy(self, settings={}):
        """
        Returns:
            Cast. A copy of the calling cast, with settings set to *settings*.
        """
        new_cast = copy.copy(self)
        new_cast.settings.update(settings)
        return new_cast

    @abc.abstractmethod
    def call(self, inpt):
        """
        Casts *inpt*.
        """
        return

    def __call__(self, inpt):
        return self.call(inpt)

    def __copy__(self):
        # TODO : this doesn't copy _schema ... should it ?
        return self.__class__(**copy.copy(self.settings))

    def __getattr__(self, name):
        try:
            return self.settings[name]
        except KeyError:
            return self.__getattribute__(name)

    def log(self, message, state='during', throughput=None):
        """
        Logs a message to **any2any**'s logger.

        Args:
            state(str). 'start', 'during' or 'end' depending on the state of the operation when the logging takes place.
        """
        #TODO: refactor
        if self.logs:
            indent = ' ' * 4 * self._depth
            extra = {
                'cast': self,
                'throughput': throughput,
                'settings': self.settings,
                'state': state,
            }
            logger.debug(indent + message, extra=extra)
