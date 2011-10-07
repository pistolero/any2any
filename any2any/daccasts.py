# -*- coding: utf-8 -*-
import copy
try:
    import abc
except ImportError:
    from compat import abc
from base import Cast, Setting, CopiedSetting, CastMixin
from utils import closest_parent, Wrap, DeclarativeWrapType, Mm, memoize


# Abstract DivideAndConquerCast
#======================================
class DivideAndConquerCast(Cast):
    """
    Abstract base cast for metamorphosing `from` and `to` any complex object or container.

    In order to achieve casting, this class uses a "divide and conquer" strategy :

        1. `Divide into sub-problems` - :meth:`DivideAndConquerCast.iter_input`
        2. `Solve sub-problems` - :meth:`DivideAndConquerCast.iter_output`
        3. `Combine solutions` - :meth:`DivideAndConquerCast.build_output`
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
        Returns:
            type or NotImplemented. The type of the value associated with `key` if it is known "a priori" (without knowing the input), or `NotImplemented` to let the cast guess.
        """
        return NotImplemented

    def get_item_to(self, key):
        """
        Returns:
            type or NotImplemented. Type the value associated with `key` must be casted to, if it is known `a priori` (without knowing the input), or `NotImplemented` to let the cast guess.
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
    Wrapper for any subclass of object. `ObjectWrap` allows to fully customize the wrapped class' behaviour :

        - attribute schema - :meth:`ObjectWrap.default_schema`
        - attribute access - :meth:`ObjectWrap.setattr` and :meth:`ObjectWrap.getattr`
        - creation of new instances - :meth:`ObjectWrap.new`

    Kwargs:

        factory(type). The type the wrap will use for instance creation.
        include(list). The list of attributes to include in the schema see, :meth:`ObjectWrap.get_schema`.
        exclude(list). The list of attributes to exclude from the schema see, :meth:`ObjectWrap.get_schema`.
        extra_schema(dict). ``{<attribute_name>: <attribute_type>}``. Adds extra attributes to the default schema, see :meth:`ObjectWrap.get_schema`.
    """

    defaults = dict(
        extra_schema = {},
        include = [],
        exclude = [],
        factory = None,
    )

    def get_class(self, attr_name):
        """
        Returns the class of attribute `attr_name`.
        """
        schema = self.get_schema()
        if attr_name in schema:
            return schema[attr_name]
        else:
            raise KeyError("'%s' not in schema" % attr_name)
    
    def get_schema(self):
        """
        Returns the full schema ``{<attribute_name>: <attribute_type>}`` of the object, taking into account : `default_schema`, `extra_schema`, `include` and `exclude`.
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
        Subclass in order to provide the schema - known a priori - of the wrapped object. Must return a dictionary with the format ``{<attribute_name>: <attribute_type>}``. 
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
        Subclass to create and return a new instance of the wrapped type. 
        """
        return self.factory(**kwargs)

    def __call__(self, *args, **kwargs):
        return self.new(**kwargs)


class WrappedObject(object):
    """
    Subclass this to create a wrapped type using a declarative syntax, e.g. 

        >>> class MyWrappedObject(WrappedObject):
        ...     
        ...     @classmethod
        ...     def get_attr1(cls, instance):
        ...         return instance['attr1']
        ... 
        ...     class Meta:
        ...         superclasses = (MyInt, int)
        ...         include = ['attr1', 'attr2']
        ...         

    Which is equivalent to :

        >>> class MyObjectWrap(ObjectWrap):
        ...
        ...     def get_attr1(self, instance):
        ...         return instance['attr1']
        ...
        >>> MyWrappedObject = MyObjectWrap(MyInt, int, include=['attr1', 'attr2']
    """

    __metaclass__ = DeclarativeWrapType(ObjectWrap)

    class Meta:
        superclasses = (object,)


class ContainerWrap(Wrap):
    """
    Wrapper for any type of container.
    """

    defaults = dict(
        value_type = NotImplemented,
        factory = None,
    )

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
        return 'Wrapped%s%s' % (self.base.__name__.capitalize(),
        '' if self.value_type == NotImplemented else 'Of%s' % self.value_type)


class WrappedContainer(object):
    """
    Subclass this to create a wrapped container type using a declarative syntax, e.g. 

        >>> class MyWrappedContainer(WrappedContainer):
        ... 
        ...     class Meta:
        ...         superclasses = (set, list)
        ...         value_type = int
        ...         

    Which is equivalent to :

        >>> MyWrappedContainer = ContainerWrap(set, list, value_type=int)
    """

    __metaclass__ = DeclarativeWrapType(ObjectWrap)

    class Meta:
        superclasses = (object,)


# Mixins for DivideAndConquerCast
#========================================
class CastItems(CastMixin):
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


class FromMapping(CastMixin):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.
    :class:`FromMapping` is more comfortable when the setting `from_` is a :class:`ContainerWrap`.
    """

    from_wrap = Setting(default=ContainerWrap)

    def get_item_from(self, key):
        return self.from_.value_type

    def iter_input(self, inpt):
        return inpt.iteritems()


class ToMapping(CastMixin):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.build_output`.
    :class:`ToMapping` is more comfortable when the setting `to` is a :class:`ContainerWrap`.
    """

    to_wrap = Setting(default=ContainerWrap)

    def get_item_to(self, key):
        return self.to.value_type

    def build_output(self, items_iter):
        return self.to(items_iter)


class FromIterable(CastMixin):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.
    :class:`FromIterable` is more comfortable when the setting `from_` is a :class:`ContainerWrap`.
    """

    from_wrap = Setting(default=ContainerWrap)

    def get_item_from(self, key):
        return self.from_.value_type

    def iter_input(self, inpt):
        return enumerate(inpt)


class ToIterable(CastMixin):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.build_output`.
    :class:`ToIterable` is more comfortable when the setting `to` is a :class:`ContainerWrap`.
    """

    to_wrap = Setting(default=ContainerWrap)

    def get_item_to(self, key):
        return self.to.value_type

    def build_output(self, items_iter):
        return self.to((value for key, value in items_iter))


class FromObject(CastMixin):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.
    :class:`FromObject` is more comfortable when the setting `from_` is an :class:`ObjectWrap`.
    """

    from_wrap = Setting(default=ObjectWrap)

    def get_item_from(self, key):
        return self.from_.get_class(key)

    def iter_input(self, inpt):
        for name in self.from_.get_schema().keys():
            yield name, self.from_.getattr(inpt, name)


class ToObject(CastMixin):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.build_output`.
    :class:`ToObject` is more comfortable when the setting `to` is an :class:`ObjectWrap`.
    """

    to_wrap = Setting(default=ObjectWrap)

    def get_item_to(self, key):
        return self.to.get_class(key)

    def build_output(self, items_iter):
        return self.to(**dict(items_iter))

