# -*- coding: utf-8 -*-
"""
.. currentmodule:: any2any.base
"""
 
# Logging 
#====================================
# TODO : cooler logging (html page with cast settings and so on)
# TODO : rename to 'debug', and have a simpler way to activate that
# TODO : better way of documenting settings
# anyways, logging needs a bit refactoring.
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

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
from utils import memoize, Mm

class CastSettings(collections.MutableMapping):
    """
    *settings* of a cast class or a cast instance. It implements :class:`collections.MutableMapping`, and is therefore usable as a dictionary :

        >>> c = CastSettings(my_setting={'a': 1}, my_other_setting=1)
        >>> c['my_other_setting']
        1

    The constructor optionally takes a keyword `_meta` that allows to configure different things for a given setting.
    For each setting, the schema can contain :

    - *override* : method to use when overriding the setting :

        >>> c = CastSettings(my_setting={'a': 1}, _meta={'my_setting': {'override': 'copy_and_update'}})
        >>> c.override({'my_setting': {'b': 2}})
        >>> c['my_setting'] == {'a': 1, 'b': 2}
        True

    - *customize* : method to use when customizing the setting :

        >>> c = CastSettings(my_setting={'a': 1}, _meta={'my_setting': {'customize': 'copy_and_update'}})
        >>> c.customize({'my_setting': {'b': 2}})
        >>> c['my_setting'] == {'a': 1, 'b': 2}
        True
    """
    def __init__(self, _meta={}, **settings):
        # initializing the schema
        self._meta = dict.fromkeys(settings, {})
        self._meta.update(_meta)
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
            self._values[name] = value
        else:
            raise TypeError("Setting '%s' is not defined" % name)

    def __delitem__(self, name):
        self._values.pop(name, None)
        self._meta.pop(name, None)

    def __contains__(self, name):
        return name in self._meta

    def __len__(self):
        return len(self._meta)

    def __iter__(self):
        return iter(self._values)

    def __copy__(self):
        # Only shallow copy is realized
        copied = {'_meta': self._meta.copy()}
        copied.update(self)
        return self.__class__(**copied)

    def override(self, settings):
        # Performs override of the calling instance and its schema with *settings*.
        # This method is used for inheritance of settings between two classes.
        # Handling schema updating
        if isinstance(settings, CastSettings):
            _meta = settings._meta
        elif isinstance(settings, dict):
            _meta = settings.pop('_meta', {})
        for name, value in _meta.items():
            if name in self._meta:
                self._meta[name].update(value)
            else:
                self._meta[name] = copy.copy(value)
        # Create default schema for all settings
        for name in settings:
            self._meta.setdefault(name, {})
        # Handling settings updating
        for name, value in copy.copy(settings).items():
            meth = self._meta[name].get('override', '__setitem__')
            getattr(self, meth)(name, value)

    def customize(self, settings):
        # Customizes the calling instance with *settings*.
        # This method is used for transmission of settings between two cast instances.
        for name, value in copy.copy(settings).items():
            try:
                meth = self._meta[name].get('customize', 'do_nothing')
            except KeyError:
                pass #TODO : propagation of setting breaks if different cast type in between ...
            else:
                getattr(self, meth)(name, value) 

    def init(self, settings):
        # Updates the calling instance with *settings*.
        # This method is used as to initialize the calling instance with *settings*.
        for name, value in copy.copy(settings).items():
            try:
                meth = self._meta[name].get('init', '__setitem__')
            except KeyError:
                pass #TODO : propagation of setting breaks if different cast type in between ...
            else:
                getattr(self, meth)(name, value)

    def copy_and_update(self, name, value):
        new_value = copy.copy(self.get(name, None))
        if new_value: new_value.update(value)
        self[name] = new_value or copy.copy(value)

    def do_nothing(self, name, value):
        pass
    
    def update_if_not_none(self, name, value):
        if value != None or self.get(name, None) == None:
            self[name] = value

class CastType(abc.ABCMeta):

    def __new__(cls, name, bases, attrs):        
        # handling multiple inheritance of defaults
        new_defaults = attrs.pop('defaults', {})
        attrs['defaults'] = CastSettings()
        parents = [b for b in bases if isinstance(b, CastType)]
        for base in reversed(parents):
            attrs['defaults'].override(base.defaults)
        attrs['defaults'].override(new_defaults)
        # creating new class
        new_cast_class = super(CastType, cls).__new__(cls, name, bases, attrs)
        # wrapping *call* to automate logging and context management
        new_cast_class.call = cls.wrap_call(new_cast_class)
        return new_cast_class

    @classmethod
    def wrap_call(cls, cast_class):
        call = cast_class.call
        @wraps(call)
        def _wrapped_call(self, *args, **kwargs):
            # Following is a hack to avoid executing the wrapping code when doing :
            #     super(MyCast, self).call(*args, **kwargs)
            if (type(self) == cast_class):
                # context management : should be first, because logging might use it.
                self._context = {'input': args[0] if args else None}
                # logging
                self.log('%s.%s' % (self, call.__name__) + ' <= ' + repr(args[0] if args else None))
                # the actual call
                returned = call(self, *args, **kwargs)
                # logging
                self.log('%s.%s' % (self, call.__name__) + ' => ' + repr(returned))
                if self._depth == 0:
                    self.log('')
                # context management
                self._context = {}
                return returned
            else:
                return call(self, *args, **kwargs)
        return _wrapped_call

class Cast(object):
    """
    Base class for all casts. This class is virtual, and all subclasses must implement :meth:`Cast.call`.

    :class:`Cast` defines the following settings :

        - mm_to_cast(dict). ``{<mm>: <cast>}``. It allows to specify which cast :meth:`Cast.cast_for` should pick for a given metamorphosis (see also : :ref:`How<configuring-cast_for>` to use *mm_to_cast*).

        - to(type). The type to cast to.
        
        - from_(type). The type to cast from. If not given, the type of the input is used.

        - logs(bool). If True, the cast writes debug to :var:`logger`.
    """

    __metaclass__ = CastType

    defaults = dict(
        mm_to_cast = {},
        from_ = None,
        to = None,
        from_wrap = None,
        to_wrap = None,
        logs = False,
        _meta = {
            'mm_to_cast': {'override': 'copy_and_update', 'customize': '__setitem__'},
            'logs': {'customize': '__setitem__'},
            'from_wrap': {'override': 'update_if_not_none'},
            'to_wrap': {'override': 'update_if_not_none'},
        },
    )

    def __new__(cls, *args, **kwargs):
        new_cast = super(Cast, cls).__new__(cls)
        new_cast.settings = copy.copy(cls.defaults)
        return new_cast

    def __init__(self, **settings):
        self._context = {} # operation context
        self._cache = {} # used for caching
        self._depth = 0 # used for logging
        self.settings.init(settings)

    def __repr__(self):
        if self.from_ or self.to:
            return '%s.%s(%s=>%s)' % (self.__class__.__module__, self.__class__.__name__, self.from_ or '', self.to or '')
        else:
            return '%s.%s()' % (self.__class__.__module__, self.__class__.__name__)

    @property
    def from_(self):
        from_ = self.settings['from_']
        # Getting *from_* from input, if needed and if possible
        if from_ == None and 'input' in self._context:
            from_ = type(self._context['input'])
        # Wrapping *from_* in specialized type, if provided.
        if self.from_wrap and from_ != None and not isinstance(from_, self.from_wrap):
            from_= self.from_wrap(from_)
        return from_

    @property
    def to(self):
        to = self.settings['to']
        # Wrapping *to* in specialized type, if provided.
        if self.to_wrap and to != None and not isinstance(to, self.to_wrap):
            to = self.to_wrap(to)
        return to

    @memoize()
    def cast_for(self, mm):
        """
        Returns:
            Cast. A cast suitable for metamorphosis *mm*, and customized with calling cast's settings.

        .. seealso:: :ref:`How<configuring-cast_for>` to control the behaviour of *cast_for*.
        """
        # gets better choice
        closest_mm = mm.pick_closest_in(self.mm_to_cast.keys())
        cast = self.mm_to_cast[closest_mm]
        # builds a customized version of the cast, override settings
        cast = copy.copy(cast)
        cast._depth = cast._depth + 1
        cast.customize(**self.settings)
        cast.customize_mm(mm)
        return cast

    @abc.abstractmethod
    def call(self, inpt):
        """
        Casts *inpt*.
        """
        return

    def __call__(self, inpt):
        return self.call(inpt)

    def __copy__(self):
        return self.__class__(**copy.copy(self.settings))

    def __getattr__(self, name):
        try:
            return self.settings[name]
        except KeyError:
            return self.__getattribute__(name)

    def configure(self, **settings):
        """
        Interface for configuring the cast's settings. 
        """
        self._cache.clear()
        self.settings.update(settings)

    def customize(self, **settings):
        """
        Interface for customizing the cast's settings. 
        """
        self._cache.clear()
        self.settings.customize(settings)

    def customize_mm(self, mm):
        # Sets *from_* and *to* for the calling cast only if they 
        # are unique classes (not *from_any* or *to_any*).
        if mm.from_ and not self.from_:
            self.configure(from_=mm.from_)
        if mm.to and not self.to:
            self.configure(to=mm.to)

    def log(self, message):
        """
        Logs a message to **any2any**'s logger.

        Args:
            state(str). 'start', 'during' or 'end' depending on the state of the operation when the logging takes place.
        """
        if self.logs:
            indent = ' ' * 4 * self._depth
            logger.debug(indent + message)

class CastStack(Cast):
    #TODO: document

    defaults = dict(_meta={'mm_to_cast': {'init': 'copy_and_update'}})

    def call(self, inpt, from_=None, to=None):
        if not to:
            to = self.to
        if not from_:
            from_ = self.from_
        mm = Mm(self.from_, to)
        cast = self.cast_for(mm)
        return cast(inpt)

