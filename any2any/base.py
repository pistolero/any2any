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

class Setting(property):

    def __init__(self, default=None, doc=None):
        self.name = None
        self.default = default
        self.doc = doc

    def __get__(self, instance, owner):
        if instance != None:
            return self.get(instance)
        else:
            return self

    def __set__(self, instance, value):
        self.set(instance, value)

    def get(self, instance):
        return instance._settings[self.name]
    
    def set(self, instance, value):
        # invalidate cache
        instance._cache.clear()
        instance._settings[self.name] = value

    def customize(self, instance, value):
        pass

    def inherits(self, setting):
        pass

    @staticmethod
    def mixin(*settings):
        return settings[0]

class CopiedSetting(Setting):

    def get(self, instance):
        value = super(CopiedSetting, self).get(instance)
        return copy.copy(value)

class ViralSetting(Setting):

    def customize(self, instance, value):
        self.set(instance, value)

class ViralDictSetting(ViralSetting):

    def inherits(self, setting):
        self.default = dict(setting.default, **self.default)

class ToSetting(Setting):
    
    def get(self, instance):
        to = super(ToSetting, self).get(instance)
        if instance.to_wrap and to != None and not isinstance(to, instance.to_wrap):
            to = instance.to_wrap(to)
        return to

class FromSetting(Setting):
    
    def get(self, instance):
        from_ = super(FromSetting, self).get(instance)
        if from_ == None and 'input' in instance._context:
            from_ = type(instance._context['input'])
        if instance.from_wrap and from_ != None and not isinstance(from_, instance.from_wrap):
            from_= instance.from_wrap(from_)
        return from_

class WrapSetting(Setting):

    @staticmethod
    def mixin(*settings):
        candidates = filter(lambda s: not s.default is None, settings)
        if candidates:
            return candidates[0]
        else:
            return settings[0]
                

class Options(object):

    def __init__(self, settings_dict):
        for name, setting in settings_dict.items():
            setting.name = name
        self.settings = settings_dict.values()
        self.settings_dict = settings_dict

class CastType(abc.ABCMeta):

    def __new__(cls, class_name, bases, attrs):
        # collecting new settings
        new_settings_dict = dict(filter(lambda (k, v): isinstance(v, Setting), attrs.items()))
        # handling multiple inheritance of settings
        parents = [b for b in bases if isinstance(b, CastType)]
        all_settings_dict = {}
        # 1. mixing-in inherited settings
        inherited_settings = collections.defaultdict(list)
        for parent in parents:
            for name, setting in parent._meta.settings_dict.items():
                inherited_settings[name].append(setting)
        for name, setting_list in inherited_settings.items():
            setting = setting_list[0].mixin(*setting_list)
            all_settings_dict[name] = setting
        # 2. handling overridings of inherited settings
        for name, setting in new_settings_dict.items():
            if name in all_settings_dict:
                setting.inherits(all_settings_dict[name])
        all_settings_dict.update(new_settings_dict)
        # creating new class
        attrs['_meta'] = Options(all_settings_dict)
        new_cast_class = super(CastType, cls).__new__(cls, class_name, bases, attrs)
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

class BaseCast(object):

    __metaclass__ = CastType

    def __new__(cls, *args, **kwargs):
        new_cast = super(BaseCast, cls).__new__(cls)
        new_cast._settings = _settings = {} # raw settings values
        for name, setting in new_cast._meta.settings_dict.items():
            _settings[name] = setting.default
        return new_cast

    def __init__(self, **settings):
        self._context = {} # operation context
        self._cache = {} # used for caching
        self._depth = 0 # used for logging
        for name, value in settings.items():
            if not name in self._meta.settings_dict:
                raise TypeError("Setting '%s' is not defined" % name)
            setattr(self, name, value)

    @abc.abstractmethod
    def call(self, inpt):
        """
        Casts `inpt`.
        """
        return

    def __call__(self, inpt):
        return self.call(inpt)

    def iter_settings(self):
        for name in self._meta.settings_dict:
            yield name, getattr(self, name)

    def customize(self, cast):
        """
        Customizes the calling instance with settings of <cast>.
        This method is used for transmission of settings between two cast instances.
        """
        for name, value in cast.iter_settings():
            setting = self._meta.settings_dict.get(name, None)
            if setting: setting.customize(self, value)

    def __copy__(self):
        settings = dict(((k, copy.copy(v)) for k, v in self.iter_settings()))
        return self.__class__(**settings)

    def log(self, message):
        """
        Logs a message to `any2any`'s logger.

        Args:
            state(str). 'start', 'during' or 'end' depending on the state of the operation when the logging takes place.
        """
        pass

class Cast(BaseCast):
    """
    Base class for all casts. This class is virtual, and all subclasses must implement :meth:`Cast.call`.
    """

    mm_to_cast = ViralDictSetting(default={})
    """mm_to_cast(dict). ``{<mm>: <cast>}``. Allows to configure which cast :meth:`Cast.cast_for` should pick for a given metamorphosis."""
    from_ = FromSetting()
    """from_(type). The type to cast from. If not given, the type of the input is used."""
    to = ToSetting()
    """to(type). The type to cast to."""
    from_wrap = WrapSetting()
    """from_wrap(type). A subclass of :class:`any2any.utils.Wrap` that will be used to wrap `from_`."""
    to_wrap = WrapSetting()
    """to_wrap(type). A subclass of :class:`any2any.utils.Wrap` that will be used to wrap `to`."""
    logs = ViralSetting(default=False)
    """logs(bool). If True, the cast writes debug to :var:`logger`."""
            #'from_wrap': {
            #    'override': update_setting_if_not_none_cb, 

    def __repr__(self):
        if self.from_ or self.to:
            return '%s.%s(%s=>%s)' % (self.__class__.__module__, self.__class__.__name__, self.from_ or '', self.to or '')
        else:
            return '%s.%s()' % (self.__class__.__module__, self.__class__.__name__)

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
        cast.customize(self)
        cast.customize_mm(mm)
        return cast

    def customize_mm(self, mm):
        # Sets `from_` and `to` for the calling cast only if they 
        # are unique classes (not `from_any` or `to_any`).
        if mm.from_ and not self.from_:
            self.from_ = mm.from_
        if mm.to and not self.to:
            self.to = mm.to

    def log(self, message):
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

    #defaults = dict(_meta={'mm_to_cast': {'init': update_setting_cb}})

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

