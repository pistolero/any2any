# -*- coding: utf-8 -*-
import copy
try:
    import abc
except ImportError:
    from compat import abc
from base import Cast
from utils import closest_parent, SpecializedType, Mm

# Abstract DivideAndConquerCast
#======================================

class DivideAndConquerCast(Cast):
    """
    Abstract base cast for metamorphosing *from* and *to* any complex object or container.

    In order to achieve casting, this class uses a "divide and conquer" strategy :

        1. *Divide into sub-problems* - :meth:`DivideAndConquerCast.iter_input`
        2. *Solve sub-problems* - :meth:`DivideAndConquerCast.iter_output`
        3. *Combine solutions* - :meth:`DivideAndConquerCast.build_output`
    """

    @abc.abstractmethod
    def iter_input(self, inpt):
        """
        Divides a complex casting into several simpler castings.
 
        Args:
            inpt(object). The cast's input.

        Returns:
            iterator. ``(<key>, <value_to_cast>)``. An iterator on all items to cast in order to completely cast *inpt*.
        """
        return

    @abc.abstractmethod
    def iter_output(self, items_iter):
        """
        Casts all the items from *items_iter*.

        Args:
            items_iter(iterator). ``(<key>, <value_to_cast>)``. An iterator on items to cast.

        Returns:
            iterator. ``(<key>, <casted_value>)``. An iterator on casted items.
        """
        return

    @abc.abstractmethod
    def build_output(self, items_iter):
        """
        Combines all the items from *items_iter* into a final output.

        Args:
            items_iter(iterator). ``(<key>, <casted_value>)``. Iterator on casted items.

        Returns:
            object. The casted object in its final shape.
        """
        return

    def get_from_class(self, key):
        """
        Returns:
            type or NotImplemented. The type of the value associated with *key* if it is known `a priori` (without knowing the input), or *NotImplemented* to let the cast guess.
        """
        # TODO: Name sucks
        return NotImplemented

    def get_to_class(self, key):
        """
        Returns:
            type or NotImplemented. Type the value associated with *key* must be casted to, if it is known `a priori` (without knowing the input), or NotImplemented.
        """
        # TODO: Name sucks
        return NotImplemented

    def call(self, inpt):
        iter_input = self.iter_input(inpt)
        iter_ouput = self.iter_output(iter_input)
        return self.build_output(iter_ouput)

# Mixins
#========================================

class CastItems(DivideAndConquerCast):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_output`.

    :class:`CastItems` defines the following settings :

        - key_to_cast(dict). ``{<key>: <cast>}``. Maps a key with the cast to use.
        - key_to_mm(dict). ``{<key>: <mm>}``. Maps a key with the metamorphosis to realize.
        - value_cast(Cast). The cast to use on all values.
        - key_cast(Cast). The cast to use on all keys.
    """
    #TODO: key_cast is ugly ...

    defaults = dict(
        key_to_cast = {},
        key_to_mm = {},
        value_cast = None,
        key_cast = None,
    )

    def iter_output(self, items_iter):
        for key, value in items_iter:
            if self.strip_item(key, value): continue
            if self.key_cast: key = self.key_cast(key)
            cast = self.cast_for_item(key, value)
            yield key, cast(value)

    def get_item_mm(self, key, value):
        # Returns the metamorphosis *mm* to apply on item *key*, *value*.
        # try to get *mm* from *key_to_mm*
        if key in self.key_to_mm:
            return self.key_to_mm[key]
        # otherwise, builds it by getting *from_* and *to*. 
        from_ = self.get_from_class(key)
        to = self.get_to_class(key)
        # If NotImplemented, we make guesses
        if from_ == NotImplemented:
            from_ = type(value)
        if to == NotImplemented:
            return Mm(from_=from_, to_any=object)
        return Mm(from_, to)

    def cast_for_item(self, key, value):
        # Returns the cast to use for item *key*, *value*.
        # The lookup order is the following :
        #   1. setting *key_to_cast*
        #   2. setting *value_cast*
        #   3. finally, the method gets the metamorphosis to apply on the item
        #       and a suitable cast by calling *Cast.cast_for*.  
        if self.logs: self.log('Item %s' % key)
        mm = self.get_item_mm(key, value)
        # try to get cast with the per-key map
        if key in self.key_to_cast:
            cast = self.key_to_cast.get(key)
            cast = copy.copy(cast)
            cast.set_mm(mm)
        elif self.value_cast:
            cast = self.value_cast
            cast.set_mm(mm)
        # otherwise try to get it by getting item's *mm* and calling *cast_for*.
        else:
            cast = self.cast_for(mm)
        cast._depth = self._depth + 1
        return cast

    @property
    def key_cast(self):
        if not 'key_cast' in self._context:
            key_cast = copy.copy(self.settings['key_cast'])
            key_cast.settings.update({
                'from_': self.from_,
                'to': self.to
            })
            self._context['key_cast'] = key_cast
        return self._context['key_cast']
            
    @property
    def value_cast(self):
        if not 'value_cast' in self._context:
            value_cast = copy.copy(self.settings['value_cast'])
            self._context['value_cast'] = value_cast
        return self._context['value_cast']

    def strip_item(self, key, value):
        """
        Override for use. If *True* is returned, the item ``<key>, <value>`` will be stripped
        from the output.

        Args:
            key (object). Item's key
            value (object). Item's value, before casting.

        Returns:
            bool. True to strip the item, False to keep it.
        """
        return False

class FromContainer(DivideAndConquerCast):

    def get_from_class(self, key):
        if isinstance(self.from_, SpecializedType) and hasattr(self.from_, 'value_type'):
            return self.from_.value_type
        else:
            return NotImplemented

class ToContainer(DivideAndConquerCast):

    def get_to_class(self, key):
        if isinstance(self.to, SpecializedType) and hasattr(self.to, 'value_type'):
            return self.to.value_type
        else:
            return NotImplemented

class FromMapping(FromContainer):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.

    :meth:`get_from_class` can guess the type of values if *to* is a :class:`ContainerType`.    
    """
    def iter_input(self, inpt):
        return inpt.iteritems()

class ToMapping(ToContainer):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.build_output`.

    :meth:`get_to_class` can guess the type of values if *to* is a :class:`ContainerType`.    
    """
    def build_output(self, items_iter):
        to = self.to.base if isinstance(self.to, SpecializedType) else self.to
        return to(items_iter)

class FromIterable(FromContainer):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.

    :meth:`get_from_class` can guess the type of values if *from_* is a :class:`ContainerType`.    
    """
    def iter_input(self, inpt):
        return enumerate(inpt)

class ToIterable(ToContainer):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.build_output`.

    :meth:`get_to_class` can guess the type of values if *to* is a :class:`ContainerType`.    
    """
    def build_output(self, items_iter):
        to = self.to.base if isinstance(self.to, SpecializedType) else self.to
        return to((value for key, value in items_iter))

class FromObject(DivideAndConquerCast):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.
    """
    # TODO: document settings
    # TODO: refactor with object SpecializedType
    defaults = dict(
        class_to_getter = {object: getattr,},
        attrname_to_getter = {},
        include = None,
        exclude = None,
        include_extra = [],
    )

    def iter_input(self, inpt):
        for name in self.calculate_include():
            yield name, self.get_getter(name)(inpt, name)

    @abc.abstractmethod
    def attr_names(self):
        """
        Returns:
            list. The list of attribute names included by default.
    
        .. warning:: This method will only be called if `include` is None.
        """
        return

    def calculate_include(self):
        # This method returns the set of attributes to include for the cast.
        # Take into account *include* or *attr_names*, and *exclude*.
        include = self.include if self.include != None else self.attr_names()
        include += self.include_extra
        exclude = self.exclude if self.exclude != None else []
        return set(include) - set(exclude)

    def get_getter(self, name):
        # try to get accessor on a per-attribute basis
        if name in self.attrname_to_getter:
            return self.attrname_to_getter[name]
        # otherwise try to get it on a per-class basis
        else:
            attr_class = self.get_from_class(name)
            # If NotImplemented, we guess ...
            if attr_class == NotImplemented:
                attr_class = object
            parent = closest_parent(attr_class, self.class_to_getter.keys())
            return self.class_to_getter.get(parent, getattr)

class ToObject(DivideAndConquerCast):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.build_output`.
    """
    # TODO: document settings
    # TODO: refactor with object SpecializedType
    defaults = dict(
        class_to_setter = {object: setattr,},
        attrname_to_setter = {}
    )

    def build_output(self, items_iter):
        items = dict(items_iter)
        new_object = self.new_object(items)
        for name, value in items.items():
            self.get_setter(name)(new_object, name, value)
        return new_object

    @abc.abstractmethod
    def new_object(self, items):
        """
        Args:
            items(dict). A dictionary containing all the casted items. Delete items from the dictionary if you don't want them to be handled automatically by the cast.

        Returns:
            object. An object created with the bare minimum from *items*. The rest will be automatically set by the cast, using the defined setters.
        """
        return

    def get_setter(self, name):
        # try to get accessor on a per-attribute basis
        if name in self.attrname_to_setter:
            return self.attrname_to_setter[name]
        # otherwise try to get it on a per-class basis
        else:
            attr_class = self.get_to_class(name)
            # If NotImplemented, we guess ...
            if attr_class == NotImplemented:
                attr_class = object
            parent = closest_parent(attr_class, self.class_to_setter.keys())
            return self.class_to_setter.get(parent, setattr)

class RouteToOperands(DivideAndConquerCast):
    #TODO: document
    defaults = dict(
        operands = []
    )

    def iter_output(self, items_iter):
        for key, value in items_iter:            
            yield key, self.operands[key](value)

class ConcatMapping(DivideAndConquerCast):
    #TODO: document

    def build_output(self, items_iter):
        concat_dict = {}
        for key, value in items_iter:
            concat_dict.update(value)
        return concat_dict

class SplitMapping(DivideAndConquerCast):
    #TODO: document

    defaults = dict(
        key_to_route = {}
    )

    def iter_input(self, inpt):
        dict_list = [dict() for o in self.operands]
        for key, value in inpt.iteritems():
            ind = self.route(key, value)
            dict_list[ind][key] = value
        return enumerate(dict_list)
    
    def get_route(self, key, value):
        raise ValueError("Couldn't find route for key '%s'" % key)

    def route(self, key, value):
        if key in self.key_to_route:
            return self.key_to_route[key]
        else:
            return self.get_route(key, value)

# Specialized types
#========================================

class ContainerType(SpecializedType):
    """
    Specialization for container types. For example, the following stands for "a list of int" :

        >>> ListOfInt = ContainerType(list, value_type=int)
    """

    defaults = {'value_type': object}
    
    def __subclasshook__(self, C):
        if super(ContainerType, self).__subclasshook__(C) and isinstance(C, ContainerType):
            return issubclass(C.value_type, self.value_type)
        else:
            return False

    def __repr__(self):
        return '%sOf%s' % (self.__base__.__name__.capitalize(), self.value_type.__name__.capitalize())
