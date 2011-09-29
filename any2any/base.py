# -*- coding: utf-8 -*-
"""
.. currentmodule:: any2any.base
"""
 
# Logging 
#====================================
# TODO : cooler logging (html page with cast settings and so on)
import logging
logger = logging.getLogger()

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
    Settings of a cast class or a cast instance. It implements :class:`collections.MutableMapping`, and is therefore usable as a dictionary.
    The constructor optionally takes a keyword argument `_meta` which allows to configure the behaviour of some of the setting's methods.
    """

    def __init__(self, **settings):
        self._meta, self._values = {}, {}
        self._update_values_and_meta(settings, '__init__', CastSettings.__setitem__)
        
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
        # iter values only, because _meta might contain unset settings
        return iter(self._values)

    def __copy__(self):
        copied = {'_meta': self._meta.copy()}
        copied.update(self)
        return self.__class__(**copied)

    def override(self, settings):
        """
        Performs override of the calling instance with <settings>.
        This method is used for inheritance of settings between two classes.
        """
        self._update_values_and_meta(settings, 'override', CastSettings.__setitem__)

    def customize(self, settings):
        """
        Customizes the calling instance with <settings>.
        This method is used for transmission of settings between two cast instances.
        """
        self._update_values_and_meta(settings, 'override', lambda *args: None)

    def _update_values_and_meta(self, settings, op_name, default_cb):
        if hasattr(settings, '_meta'):
            _meta = settings._meta
        elif '_meta' in settings:
            _meta = settings['_meta']
        else:
            _meta = {}
        # We must iterate over both values and meta, because there might be
        # values with no meta, and meta with no value.
        for name, value in _meta.items():
            self._declare_setting(name, value)
        for name in set(settings) - {'_meta'}:
            self._declare_setting(name)
            cb = self._meta[name].get(op_name, default_cb)
            cb(self, name, settings[name])

    def _declare_setting(self, name, meta={}):
        self._meta[name] = dict(self._meta.get(name, {}), **meta)

class CastType(abc.ABCMeta):

    def __new__(cls, name, bases, attrs):        
        # handling multiple inheritance of defaults
        new_defaults = attrs.pop('defaults', {})
        attrs['defaults'] = CastSettings()
        parents = [b for b in bases if isinstance(b, CastType)]
        for base in reversed(parents):
            attrs['defaults'].override(base.defaults)
        attrs['defaults'].override(new_defaults)
        # generating docs
        doc = cls.build_doc(attrs.get('__doc__', ''), attrs['defaults'])
        if doc: attrs['__doc__'] = doc
        # creating new class
        new_cast_class = super(CastType, cls).__new__(cls, name, bases, attrs)
        # wrapping `call` to automate logging and context management
        new_cast_class.call = cls.wrap_call(new_cast_class)
        return new_cast_class

    @classmethod
    def wrap_call(cls, cast_class):
        call = cast_class.call
        @wraps(call)
        def _wrapped_call(self, *args, **kwargs):
            # The if/else block is a hack to avoid executing the wrapping code when doing :
            #     super(MyCast, self).call(*args, **kwargs)
            if (type(self) == cast_class):
                # context management should be first, because logging might use it.
                self._context = {'input': args[0] if args else None}
                self.log('%s.%s' % (self, call.__name__) + ' <= ' + repr(args[0] if args else None))
                returned = call(self, *args, **kwargs)
                self.log('%s.%s' % (self, call.__name__) + ' => ' + repr(returned))
                if self._depth == 0:
                    self.log('')
                self._context = {}
                return returned
            else:
                return call(self, *args, **kwargs)
        return _wrapped_call

    @classmethod
    def build_doc(cls, class_doc, settings):
        # Builds the doc of the new cast, by collecting docs of all settings,
        # and appending them to the doc of the class.
        settings_docs = ['\t' + v['__doc__'] for k, v in settings._meta.items() if '__doc__' in v]
        all_docs = [class_doc] + settings_docs
        all_docs = filter(bool, all_docs)
        return '\n'.join(all_docs)

# callbacks for setting's meta
def set_setting_cb(s, n, v):
    s[n] = v
def update_setting_cb(s, n, v):
    s[n] = dict(s.get(n, {}), **v)
def update_setting_if_not_none_cb(s, n, v):
    if v != None or not n in s: s[n] = v

class Cast(object):
    """
    Base class for all casts. This class is virtual, and all subclasses must implement :meth:`Cast.call`.
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
            'to': {
                '__doc__': 'to(type). The type to cast to.',
            },
            'from_': {
                '__doc__': 'from_(type). The type to cast from. If not given, the type of the input is used.',
            },
            'mm_to_cast': {
                '__doc__': 'mm_to_cast(dict). ``{<mm>: <cast>}``. Allows to configure which cast :meth:`Cast.cast_for` should pick for a given metamorphosis.',
                'override': update_setting_cb, 'customize': set_setting_cb,
            },
            'logs': {
                '__doc__': 'logs(bool). If True, the cast writes debug to :var:`logger`.',
                'customize': set_setting_cb,
            },
            'from_wrap': {
                '__doc__': 'from_wrap(type). A subclass of :class:`any2any.utils.Wrap` that will be used to wrap `from_`.',
                'override': update_setting_if_not_none_cb,
            },
            'to_wrap': {
                '__doc__': 'to_wrap(type). A subclass of :class:`any2any.utils.Wrap` that will be used to wrap `to`.',
                'override': update_setting_if_not_none_cb,
            },
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
        self.configure(**settings)

    def __repr__(self):
        if self.from_ or self.to:
            return '%s.%s(%s=>%s)' % (self.__class__.__module__, self.__class__.__name__, self.from_ or '', self.to or '')
        else:
            return '%s.%s()' % (self.__class__.__module__, self.__class__.__name__)

    @property
    def from_(self):
        from_ = self.settings['from_']
        if from_ == None and 'input' in self._context:
            from_ = type(self._context['input'])
        if self.from_wrap and from_ != None and not isinstance(from_, self.from_wrap):
            from_= self.from_wrap(from_)
        return from_

    @property
    def to(self):
        to = self.settings['to']
        if self.to_wrap and to != None and not isinstance(to, self.to_wrap):
            to = self.to_wrap(to)
        return to

    @memoize()
    def cast_for(self, mm):
        """
        Returns:
            Cast. A cast suitable for metamorphosis `mm`, and customized with calling cast's settings.
        """
        # gets best choice
        closest_mm = mm.pick_closest_in(self.mm_to_cast.keys())
        cast = self.mm_to_cast[closest_mm]
        # copies and builds a customized version
        cast = copy.copy(cast)
        cast._depth = cast._depth + 1
        cast.customize(**self.settings)
        cast.customize_mm(mm)
        return cast

    @abc.abstractmethod
    def call(self, inpt):
        """
        Casts `inpt`.
        """
        return

    def __call__(self, inpt):
        return self.call(inpt)

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
        # Sets `from_` and `to` for the calling cast only if they 
        # are unique classes (not `from_any` or `to_any`).
        if mm.from_ and not self.from_:
            self.configure(from_=mm.from_)
        if mm.to and not self.to:
            self.configure(to=mm.to)

    def __copy__(self):
        return self.__class__(**copy.copy(self.settings))

    def __getattr__(self, name):
        try:
            return self.settings[name]
        except KeyError:
            return self.__getattribute__(name)

    def log(self, message):
        """
        Logs a message to `any2any`'s logger.

        Args:
            state(str). 'start', 'during' or 'end' depending on the state of the operation when the logging takes place.
        """
        if self.logs:
            indent = ' ' * 4 * self._depth
            logger.debug(indent + message)

    def set_debug_mode_on(self):
        """
        Set debug mode: all debug logs will be printed on stderr.
        """
        self.configure(logs=True)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())

class CastStack(Cast):
    """
    A cast provided for convenience. `CastStack` doesn't do anything else than looking for a suitable cast with `cast_for` and calling it. For example. 
    """

    defaults = dict(_meta={'mm_to_cast': {'__init__': update_setting_cb}})

    def __call__(self, inpt, *args, **kwargs):
        return self.call(inpt, *args, **kwargs)

    def call(self, inpt, from_=None, to=None):
        if not to:
            to = self.to
        if not from_:
            from_ = self.from_
        mm = Mm(self.from_, to)
        cast = self.cast_for(mm)
        return cast(inpt)

