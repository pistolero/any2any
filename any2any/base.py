# -*- coding: utf-8 -*-
import copy
import re
try:
    import abc
except ImportError:
    from compat import abc
import collections
from functools import wraps
import logging
import types

from utils import memoize, Mm, Wrap

 
# Logging 
#====================================
# TODO : cooler logging (html page with cast settings and so on)
logger = logging.getLogger()


# Setting
#====================================
class Setting(property):
    """
    Base class for all setting types. 
    """

    def __init__(self, default=None):
        self.name = None
        self.default = default

    def __get__(self, cast, owner):
        if cast != None:
            return self.get(cast)
        else:
            return self

    def __set__(self, cast, value):
        self.set(cast, value)

    # Hooks for controlling setting's behaviour :
    def get(self, cast):
        """
        Gets and returns the setting's value from `cast`. 
        """
        return cast._settings[self.name]
    
    def set(self, cast, value):
        """
        Sets the setting's value on `cast`.
        """
        # invalidate cache
        cast._cache.clear()
        cast._settings[self.name] = value

    def init(self, cast, value):
        """
        This method handles initialization of the setting's value. 
        """
        self.set(cast, value)

    def customize(self, cast, value):
        """
        This method handles customization of the setting's value. 
        """
        pass

    def inherits(self, setting):
        """
        When overriding a setting, this is called on the new setting 
        to take into account the parent setting.
        """
        pass


class CopiedSetting(Setting):
    """
    A setting that always returns a copy of its value
    """

    def get(self, cast):
        value = super(CopiedSetting, self).get(cast)
        return copy.copy(value)


class ViralSetting(Setting):
    """
    A setting that always catches the value it is customized with. 
    """

    def customize(self, cast, value):
        self.set(cast, value)


# Metaclasses and bases for casts
#====================================
class Options(object):
    # Options for a cast class.

    def __init__(self, settings_dict):
        for name, setting in settings_dict.items():
            setting.name = name
        self.settings = settings_dict.values()
        self.settings_dict = settings_dict


class CastType(abc.ABCMeta):
    # Metaclass for `BaseCast`

    def __new__(cls, class_name, bases, attrs):
        Meta = attrs.pop('Meta', object())
        # collecting new settings
        new_settings_dict = cls.filter_settings(attrs)
        # handling multiple inheritance of settings
        all_settings_dict = {}
        #     1. collecting inherited settings
        for base in reversed(bases):
            if isinstance(base, CastType):
                all_settings_dict.update(base._meta.settings_dict)
            else:
                all_settings_dict.update(cls.collect_settings(base))
        #     2. handling overridings
        for name, setting in new_settings_dict.items():
            if name in all_settings_dict:
                setting.inherits(all_settings_dict[name])
        all_settings_dict.update(new_settings_dict)
        #     3. handling overridings of default values through Meta
        for name, new_default in getattr(Meta, 'defaults', {}).items():
            if name in all_settings_dict:
                setting = all_settings_dict[name]
                new_setting = copy.copy(setting)
                new_setting.default = new_default
                new_setting.inherits(setting)
                all_settings_dict[name] = new_setting
        # creating the new class
        attrs['_meta'] = Options(all_settings_dict)
        return super(CastType, cls).__new__(cls, class_name, bases, attrs)

    @classmethod
    def filter_settings(cls, attrs):
        return dict(filter(lambda (k, v): isinstance(v, Setting), attrs.items()))

    @classmethod
    def collect_settings(cls, klass):
        # uses `collect_settings_names` to collect settings, without
        # caring about mro
        settings_names = cls.collect_settings_names(klass)
        return dict(((name, getattr(klass, name)) for name in settings_names))

    @classmethod
    def collect_settings_names(cls, klass):
        # recursively collects settings names for a non-cast class,
        # following the inheritance hierarchy
        settings_names = set(cls.filter_settings(klass.__dict__))
        for base in klass.__bases__:
            settings_names.update(cls.collect_settings_names(base))
        return settings_names 


class BaseCast(object):
    # Base for `Cast`.

    __metaclass__ = CastType

    def __new__(cls, *args, **kwargs):
        new_cast = super(BaseCast, cls).__new__(cls)
        # initializing raw setting values
        new_cast._settings = {}
        for name, setting in new_cast._meta.settings_dict.items():
            new_cast._settings[name] = setting.default
        return new_cast

    def __init__(self, **settings):
        self._context = {} # operation context
        self._cache = {} # used for caching
        self._depth = 0 # used for logging
        cast_settings = self._meta.settings_dict
        for name, value in settings.items():
            if not name in cast_settings:
                raise TypeError("Setting '%s' is not defined" % name)
            cast_settings[name].init(self, value)

    @abc.abstractmethod
    def call(self, inpt):
        """
        Virtual method. Casts `inpt`.
        """
        return

    def __call__(self, *args, **kwargs):
        # wraps `Cast.call` to automate context management and logging
        self._context = {'input': args[0] if args else None}
        self.log('%s' % self + ' <= ' + repr(args[0] if args else None))
        returned = self.call(*args, **kwargs)
        self.log('%s' % self + ' => ' + repr(returned))
        if self._depth == 0:
            self.log('')
        self._context = {}
        return returned

    def iter_settings(self):
        """
        Returns an iterator on all settings ``(<name>, <value>)``.
        """
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

    def log(self, message):
        """
        Logs a message to `any2any`'s logger.
        """
        pass

    def __copy__(self):
        settings = dict(self.iter_settings())
        return self.__class__(**settings)


# Cast, CastStack 
#====================================
class ToSetting(Setting):
    # Automatically wraps `to` with the setting `to_wrap`, if provided.

    def get(self, instance):
        to = super(ToSetting, self).get(instance)
        if instance.to_wrap and to != None and not isinstance(to, instance.to_wrap):
            to = instance.to_wrap(klass=to)
        return to


class FromSetting(Setting):
    # Automatically wraps `from_` with the setting `from_wrap`, if provided.
    # If `from_` is not provided, guesses it from the cast's input.

    def get(self, instance):
        from_ = super(FromSetting, self).get(instance)
        if from_ == None and 'input' in instance._context:
            from_ = type(instance._context['input'])
        if instance.from_wrap and from_ != None and not isinstance(from_, instance.from_wrap):
            from_= instance.from_wrap(klass=from_)
        return from_


class MmToCastSetting(ViralSetting):
    # Automatically updates `mm_to_cast` value with `extra_mm_to_cast`

    def inherits(self, setting):
        self.default = dict(setting.default, **self.default)

    def get(self, instance):
        mm_to_cast = super(MmToCastSetting, self).get(instance)
        return dict(mm_to_cast, **instance.extra_mm_to_cast)


class Cast(BaseCast):
    """
    Base class for all casts. This class is virtual, and all subclasses must implement :meth:`Cast.call`.
    """

    mm_to_cast = MmToCastSetting(default={})
    """dict. ``{<mm>: <cast>}``. A dictionary mapping a metamorphosis to a cast instance."""

    extra_mm_to_cast = Setting(default={})
    """dict. ``{<mm>: <cast>}``. Overrides :attr:`mm_to_cast` as a dictionary update."""

    from_ = FromSetting()
    """type. The type to cast from. If not given, the type of the input is used."""

    to = ToSetting()
    """type. The type to cast to."""

    from_wrap = Setting()
    """type. A subclass of :class:`any2any.utils.Wrap`. If provided, will cause :attr:`from_` to be automatically wrapped."""

    to_wrap = Setting()
    """type. A subclass of :class:`any2any.utils.Wrap`. If provided, will cause :attr:`to` to be automatically wrapped."""

    logs = ViralSetting(default=False)
    """bool. If True, the cast writes debug informations to the logger."""

    def __repr__(self):
        if self.from_ or self.to:
            return '%s.%s(%s=>%s)' % (self.__class__.__module__, self.__class__.__name__, self.from_ or '', self.to or '')
        else:
            return '%s.%s()' % (self.__class__.__module__, self.__class__.__name__)

    @memoize()
    def cast_for(self, mm):
        """
        Picks in :attr:`mm_to_cast` a cast suitable for `mm`, customizes it with calling cast's settings, and finally returns it.
        """
        # gets best choice
        best_match = self._pick_best_match(mm, self.mm_to_cast.keys())
        cast = self.mm_to_cast[best_match]
        # returns a customized version
        return self.build_customized(cast, mm)

    def build_customized(self, cast, mm):
        if isinstance(cast, types.FunctionType):
            return cast
        # builds a customized version of <cast>.
        cast = copy.copy(cast)
        cast._depth = cast._depth + 1
        cast.customize(self)
        # Sets `from_` and `to` for the calling cast with mm's, only if mm's 
        # are singletons (not `from_any` or `to_any`).
        if mm.from_ and not cast.from_:
            cast.from_ = mm.from_
        if mm.to and not cast.to:
            cast.to = mm.to
        return cast

    def _pick_best_match(self, mm, mm_list):
        # Picks in `mm_list` the best match for `mm`.
        # Keep only the supersets of `mm`.
        filtered = mm.super_mms(mm_list)
        if not filtered:
            raise ValueError("No suitable metamorphosis found for '%s'" % mm)
        # We prefer if `to_set` is more precise.
        # e.g. if mm is `str -> str`, we prefer `any object -> str` than `str -> any object`.
        for v1 in list(filtered):
            for v2 in list(filtered):
                if v1._to_set < v2._to_set:
                    filtered.remove(v2)
        for v1 in list(filtered):
            for v2 in list(filtered):
                if v1._from_set < v2._from_set:
                    filtered.remove(v2)
        # If wraps, we give preference to wrap's `all_superclasses` in the order
        # they are declared.
        # e.g. if mm is `Wrap(int, str) -> object`, we prefer `int -> object` than `str -> object`.
        from_class, to_class = mm._from_set.klass, mm._to_set.klass
        if isinstance(to_class, Wrap):
            for k in to_class.all_superclasses:
                temp = filter(lambda v: k <= v._to_set, filtered)
                if temp:
                    filtered = temp
                    break
        if isinstance(from_class, Wrap):
            for k in from_class.all_superclasses:
                temp = filter(lambda v: k <= v._from_set, filtered)
                if temp:
                    filtered = temp
                    break
        return filtered[0]

    def log(self, message):
        if self.logs:
            indent = ' ' * 4 * self._depth
            logger.debug(indent + message)

    def set_debug_on(self):
        """
        Set debug mode: all debug logs will be printed on stderr.
        """
        self.logs = True
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())


class CastStack(Cast):
    """
    A cast provided for convenience. `CastStack` doesn't do anything else than looking for a suitable cast with :meth:`Cast.cast_for` and calling it. It is therefore very useful for just stacking a bunch of casts, and then casting different types of input. For example :

        >>> cast = CastStack(mm_to_cast={
        ...     Mm(from_any=int): my_int_cast,
        ...     Mm(from_any=str): my_str_cast,
        ... })
        >>> cast('a string')
        'other string'
        >>> cast(1234)
        12345
    """

    def call(self, inpt, from_=None, to=None):
        if not to:
            to = self.to
        if not from_:
            from_ = self.from_
        mm = Mm(from_, to)
        cast = self.cast_for(mm)
        return cast(inpt)

