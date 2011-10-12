# -*- coding: utf-8 -*-
import copy
try:
    import abc
except ImportError:
    from compat import abc
from base import Cast, Setting, CopiedSetting
from utils import closest_parent, Wrap, DeclarativeWrap, Mm, memoize


# Abstract DivideAndConquerCast
#======================================
class DivideAndConquerCast(Cast):
    """
    Abstract base cast for metamorphosing `from` and `to` any complex object or container.

    In order to achieve casting, this class implements a "divide and conquer" strategy :

        1. `Divide into sub-problems` - :meth:`iter_input`
        2. `Solve sub-problems` - :meth:`iter_output`
        3. `Combine solutions` - :meth:`build_output`
    """

    @abc.abstractmethod
    def iter_input(self, inpt):
        """
        Divides a complex casting into several simpler castings.
 
        Args:
            inpt(object). The cast's input.

        Returns:
            iterator. ``(<key>, <value_to_cast>)``. An iterator on all items to cast in order to completely cast `inpt`.
        """
        return

    @abc.abstractmethod
    def iter_output(self, items_iter):
        """
        Casts all the items from `items_iter`.

        Args:
            items_iter(iterator). ``(<key>, <value_to_cast>)``. An iterator on items to cast.

        Returns:
            iterator. ``(<key>, <casted_value>)``. An iterator on casted items.
        """
        return

    @abc.abstractmethod
    def build_output(self, items_iter):
        """
        Combines all the items from `items_iter` into a final output.

        Args:
            items_iter(iterator). ``(<key>, <casted_value>)``. Iterator on casted items.

        Returns:
            object. The casted object in its final shape.
        """
        return

    def get_item_from(self, key):
        """
        Returns the type of the value associated with `key` if it is known "a priori" (without knowing the input), or `NotImplemented` to let the cast guess.
        """
        return NotImplemented

    def get_item_to(self, key):
        """
        Returns the type the value associated with `key` must be casted to, if it is known `a priori` (without knowing the input), or `NotImplemented` to let the cast guess.
        """
        return NotImplemented

    def call(self, inpt):
        iter_input = self.iter_input(inpt)
        iter_ouput = self.iter_output(iter_input)
        return self.build_output(iter_ouput)


# Type wraps
#======================================
class ObjectWrap(Wrap):
    """
    Wrapper for any type, providing extra-informations such as attribute schema, accessors, constructor :

        - attribute schema - :meth:`default_schema`
        - attribute access - :meth:`setattr` and :meth:`getattr`
        - creation of new instances - :meth:`new`

    Features:

        - include(list). The list of attributes to include in the schema see, :meth:`get_schema`.
        - exclude(list). The list of attributes to exclude from the schema see, :meth:`get_schema`.
        - extra_schema(dict). ``{<attribute_name>: <attribute_type>}``. Adds extra attributes to the default schema, see :meth:`get_schema`.
    """

    defaults = {
        'extra_schema': {},
        'include': [],
        'exclude': [],
    }

    def get_class(self, attr_name):
        """
        Returns the class of attribute `attr_name`, as found from the schema, see :meth:`get_schema`.
        """
        schema = self.get_schema()
        if attr_name in schema:
            return schema[attr_name]
        else:
            raise KeyError("'%s' not in schema" % attr_name)
    
    def get_schema(self):
        """
        Returns the full schema ``{<attribute_name>: <attribute_type>}`` of the type, taking into account : `default_schema`, `extra_schema`, `include` and `exclude`.
        """
        schema = self.default_schema()
        schema.update(self.extra_schema)
        if self.include:
            [schema.setdefault(k, NotImplemented) for k in self.include]
            [schema.pop(k) for k in schema.keys() if k not in self.include]
        if self.exclude:
            [schema.pop(k, None) for k in self.exclude]
        for attr_name, cls in schema.iteritems():
            schema[attr_name] = cls
        return schema

    def default_schema(self):
        """
        Returns the schema - known a priori - of the wrapped type. Must return a dictionary with the format ``{<attribute_name>: <attribute_type>}``. 
        """
        return {}

    def setattr(self, obj, name, value):
        """
        Sets the attribute `name` on `obj`, with value `value`. If the calling :class:`ObjectWrap` has a method `set_<name>`, this method will be used to set the attribute.
        """
        if hasattr(self, 'set_%s' % name):
            getattr(self, 'set_%s' % name)(obj, value)
        else:
            setattr(obj, name, value)

    def getattr(self, obj, name):
        """
        Gets the attribute `name` from `obj`. If the calling :class:`ObjectWrap` has a method `get_<name>`, this method will be used to get the attribute.
        """
        if hasattr(self, 'get_%s' % name):
            return getattr(self, 'get_%s' % name)(obj)
        else:
            return getattr(obj, name)

    def new(self, **kwargs):
        """
        Creates and returns a new instance of the wrapped type.
        """
        return (self.factory or self.klass)(**kwargs)

    def __call__(self, *args, **kwargs):
        return self.new(**kwargs)


class DeclarativeObjectWrap(ObjectWrap, DeclarativeWrap): pass
class WrappedObject(object):
    """
    Subclass this to create an :class:`ObjectWrap` instance using a declarative syntax, e.g. 

        >>> class MyWrappedObject(WrappedObject):
        ... 
        ...     klass = int
        ...     superclasses = (MyInt,)
        ...     include = ['attr1', 'attr2']
        ...    
        ...     @classmethod
        ...     def get_attr1(cls, instance):
        ...         return instance['attr1']
        ... 
        ...         

    Which is equivalent to :

        >>> class MyObjectWrap(ObjectWrap):
        ...
        ...     def get_attr1(self, instance):
        ...         return instance['attr1']
        ...
        >>> MyWrappedObject = MyObjectWrap(klass=int, superclasses=(MyInt,) include=['attr1', 'attr2']
    """

    __metaclass__ = DeclarativeObjectWrap

    klass = object


class ContainerWrap(Wrap):
    """
    Wrapper for any type of container.

    Features:
        
        value_type(type or NotImplemented). The type of values in that container.
    """

    defaults = {'value_type': NotImplemented}

    def __superclasshook__(self, C):
        # this allows to implement the following behaviour :
        # >>> Wrap.issubclass(ContainerWrap(list, value_type=str), ContainerWrap(list, value_type=basestring))
        # True
        if super(ContainerWrap, self).__superclasshook__(C):
            if isinstance(C, ContainerWrap):
                return Wrap.issubclass(self.value_type, C.value_type)
            else:
                return True
        else:
            return False

    def __repr__(self):
        return 'Wrapped%s%s' % (self.klass.__name__.capitalize(),
        '' if self.value_type == NotImplemented else 'Of%s' % self.value_type)


class DeclarativeContainerWrap(ContainerWrap, DeclarativeWrap): pass
class WrappedContainer(object):
    """
    Subclass this to create a :class:`ContainerWrap` instance using a declarative syntax, e.g. 

        >>> class MyWrappedContainer(WrappedContainer):
        ... 
        ...     klass = set
        ...     superclasses = (list,)
        ...     value_type = int
        ...         

    Which is equivalent to :

        >>> MyWrappedContainer = ContainerWrap(klass=set, superclasses=(list,), value_type=int)
    """

    __metaclass__ = DeclarativeContainerWrap

    klass = object


# Mixins for DivideAndConquerCast
#========================================
class CastItems(object):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_output`.
    """

    key_to_cast = Setting(default={})
    """dict. ``{<key>: <cast>}``. Maps a key with the cast to use."""

    value_cast = CopiedSetting()
    """Cast. The cast to use on all values."""

    key_cast = CopiedSetting()
    """Cast. The cast to use on all keys."""

    def iter_output(self, items_iter):
        """
        Casts each item. The cast is looked-up for in the following order :

            #. setting :attr:`key_to_cast`
            #. setting :attr:`value_cast`
            #. finally, using :meth:`any2any.base.Cast.cast_for`
        """
        for key, value in items_iter:
            if self.strip_item(key, value): continue
            cast = self.cast_for_item(key, value)
            if self.key_cast: key = self.key_cast(key)
            yield key, cast(value)

    def get_item_mm(self, key, value):
        # Returns the metamorphosis `mm` to apply on item `key`, `value`.
        from_ = self.get_item_from(key)
        to = self.get_item_to(key)
        # If NotImplemented, we make guesses
        if from_ == NotImplemented:
            from_ = type(value)
        if to == NotImplemented:
            return Mm(from_=from_, to_any=object)
        return Mm(from_, to)

    def cast_for_item(self, key, value):
        # Returns the cast to use for item `key`, `value`.
        # The lookup order is the following :
        #   1. setting `key_to_cast`
        #   2. setting `value_cast`
        #   3. finally, the method gets the metamorphosis to apply on the item
        #       and a suitable cast by calling `Cast.cast_for`.
        self.log('Item %s' % key)
        mm = self.get_item_mm(key, value)
        # try to get cast with the per-key map
        if key in self.key_to_cast:
            cast = self.key_to_cast.get(key)
            cast = copy.copy(cast)
            cast.customize(self)
            cast.set_mm(mm)
        elif self.value_cast:
            cast = self.value_cast
            cast.customize(self)
            cast.set_mm(mm)
        # otherwise try to get it by getting item's `mm` and calling `cast_for`.
        else:
            cast = self.cast_for(mm)
        cast._depth = self._depth + 1
        return cast

    def strip_item(self, key, value):
        """
        Override for use. If `True` is returned, the item ``<key>, <value>`` will be stripped from the output.
        """
        return False


class FromMapping(object):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.
    
    Note that `FromMapping` is more clever when `from_` is a :class:`ContainerWrap`.
    """

    from_wrap = Setting(default=ContainerWrap)

    def get_item_from(self, key):
        return self.from_.value_type

    def iter_input(self, inpt):
        return inpt.iteritems()


class ToMapping(object):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.build_output`.
    
    Note that `ToMapping` is more clever when `to` is a :class:`ContainerWrap`.
    """

    to_wrap = Setting(default=ContainerWrap)

    def get_item_to(self, key):
        return self.to.value_type

    def build_output(self, items_iter):
        return self.to(items_iter)


class FromIterable(object):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.
    
    Note that `FromIterable` is more clever when `from_` is a :class:`ContainerWrap`.
    """

    from_wrap = Setting(default=ContainerWrap)

    def get_item_from(self, key):
        return self.from_.value_type

    def iter_input(self, inpt):
        return enumerate(inpt)


class ToIterable(object):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.build_output`.
    
    Note that `ToIterable` is more clever when `to` is a :class:`ContainerWrap`.
    """

    to_wrap = Setting(default=ContainerWrap)

    def get_item_to(self, key):
        return self.to.value_type

    def build_output(self, items_iter):
        return self.to((value for key, value in items_iter))


class FromObject(object):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.
    
    Note that `FromObject` is more clever when `from_` is an :class:`ObjectWrap`.
    """

    from_wrap = Setting(default=ObjectWrap)

    def get_item_from(self, key):
        return self.from_.get_class(key)

    def iter_input(self, inpt):
        for name in self.from_.get_schema().keys():
            yield name, self.from_.getattr(inpt, name)


class ToObject(object):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.build_output`.
    
    Note that `ToObject` is more clever when `to` is an :class:`ObjectWrap`.
    """

    to_wrap = Setting(default=ObjectWrap)

    def get_item_to(self, key):
        return self.to.get_class(key)

    def build_output(self, items_iter):
        return self.to(**dict(items_iter))

