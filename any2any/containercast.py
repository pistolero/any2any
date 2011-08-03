# -*- coding: utf-8 -*-
# TODO: rewrite doc
import copy
try:
    import abc
except ImportError:
    from compat import abc
from base import Cast
from utils import closest_parent, SpecializedType, Mm

# Abstract ContainerCast + ContainerType
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

class ContainerCast(Cast):
    """
    Abstract base cast for metamorphosing `from` and `to` containers-like objects, and complex objects.

    In order to cast containers, this class uses the following flow :

        1. Iterating on input's items, see :meth:`ContainerCast.iter_input`.
        2. Casting all items, see :meth:`ContainerCast.iter_output`.
        3. Building output with casted items, see :meth:`ContainerCast.build_output`.
    """

    @abc.abstractmethod
    def iter_input(self, inpt):
        """
        Args: 
            inpt(object). The cast's input.

        Returns:
            iterator. ``(<key>, <value>)``. Iterator on *inpt*'s items.
        """
        return

    @abc.abstractmethod
    def iter_output(self, items_iter):
        """
        Args:
            items_iter(iterator). An iterator on input's items.

        Returns:
            iterator. An iterator on casted items.
        """
        return

    @abc.abstractmethod
    def build_output(self, items_iter):
        """
        Args:
            items_iter(iterator). ``(<key>, <casted_value>)``. Iterator on casted items.

        Returns:
            object. The casted object in its final shape.
        """
        return

    def get_from_class(self, key):
        """
        Returns:
            type or NotImplemented. The type of the value associated with *key* if it is known `a priori` (without knowing the input), or `NotImplemented` to let the cast guess.
        """
        return NotImplemented

    def get_to_class(self, key):
        """
        Returns:
            type or NotImplemented. Type the value associated with *key* must be casted to, if it is known `a priori` (without knowing the input), or NotImplemented.
        """
        return NotImplemented

    def call(self, inpt):
        iter_input = self.iter_input(inpt)
        iter_ouput = self.iter_output(iter_input)
        return self.build_output(iter_ouput)

# Mixins
#========================================

class CastItems(ContainerCast):
    """
    Mixin for ContainerCast. Implements :meth:`ContainerCast.iter_output`.

    :class:`CastItems` defines the following settings :

        - key_to_cast(dict). ``{<key>: <cast>}``. Maps a key with the cast to use.
        - key_to_mm(dict). ``{<key>: <mm>}``. Maps a key with the metamorphosis to realize.
        - value_cast(Cast). The cast to use on all values.
        - key_cast(Cast). The cast to use on all keys.
    """
    #TODO: document
    #TODO: document key_cast + item_strip
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
            if self.key_cast: key = self.cast_key(key)
            cast = self.cast_for_item(key, value)
            yield key, cast(value)

    def get_item_mm(self, key, value):
        """
        Returns:
            Mm. The metamorphosis to apply on item *key*, *value*.
        """
        # try to get mm from `key_to_mm`
        if key in self.key_to_mm:
            return self.key_to_mm[key]
        # otherwise, builds it by getting `from_` and `to`. 
        from_ = self.get_from_class(key)
        to = self.get_to_class(key)
        # If NotImplemented, we make guesses
        if from_ == NotImplemented:
            from_ = type(value)
        if to == NotImplemented:
            to = object
        return Mm(from_, to)

    def cast_for_item(self, key, value):
        """
        Returns:
            Cast. The cast to use for item *key*, *value*. The lookup order is the following :

                1. setting :attr:`key_to_cast`
                2. setting :attr:`value_cast`
                3. finally, the method gets the metamorphosis to apply on the item and a suitable cast by calling :meth:`Cast.cast_for`.  
        """
        self.log('Item %s' % key)
        mm = self.get_item_mm(key, value)
        # try to get cast with the per-key map
        if key in self.key_to_cast:
            cast = self.key_to_cast.get(key)
            cast = copy.copy(cast)
            cast.settings.customize({'from_': mm.from_, 'to': mm.to})
        elif self.value_cast:
            cast = self.value_cast
            cast = copy.copy(cast)
            cast.settings.customize({'from_': mm.from_, 'to': mm.to})
        # otherwise try to get it by getting item's `mm` and calling `cast_for`.
        else:
            cast = self.cast_for(mm)
        cast._depth = self._depth + 1
        return cast

    def cast_key(self, key):
        """
        Takes a key as input, casts it with :class:`key_cast`, and returns it.
        """
        return self._get_key_cast()(key)

    def _get_key_cast(self):
        if not hasattr(self, '_custom_key_cast'):
            self._custom_key_cast = copy.copy(self.key_cast)
            self._custom_key_cast.settings.customize({
                'from_': self.from_,
                'to': self.to
            })
        return self._custom_key_cast
            

    def strip_item(self, key, value):
        """
        Args:
            key (object). Item's key
            value (object). Item's value, before casting.

        Returns:
            bool. True to strip the item, False to keep it.
        """
        return False

class FromDict(ContainerCast):
    
    def iter_input(self, inpt):
        return inpt.iteritems()

    def get_from_class(self, key):
        return self.from_.value_type if isinstance(self.from_, ContainerType) else NotImplemented

class ToDict(ContainerCast):
    
    def build_output(self, items_iter):
        return dict(items_iter)

    def get_to_class(self, key):
        return self.to.value_type if isinstance(self.to, ContainerType) else NotImplemented

class FromList(ContainerCast):
    
    def iter_input(self, inpt):
        return enumerate(inpt) 

    def get_from_class(self, key):
        return self.from_.value_type if isinstance(self.from_, ContainerType) else NotImplemented

class ToList(ContainerCast):
    
    def build_output(self, items_iter):
        return [value for key, value in items_iter]

    def get_to_class(self, key):
        return self.to.value_type if isinstance(self.to, ContainerType) else NotImplemented

class FromObject(ContainerCast):
    
    defaults = dict(
        class_to_getter = {object: getattr,},
        attrname_to_getter = {},
        include = None,
        exclude = None,
        include_extra = [],
    )

    def get_from_class(self, key):
        return NotImplemented

    @abc.abstractmethod
    def attr_names(self):
        """
        Returns:
            list. The list of attribute names included by default.
    
        .. warning:: This method will only be called if :attr:`include` is None.
        """
        return

    def calculate_include(self):
        """
        Returns:
            set. The set of attributes to include for the cast. Take into account *include* or :meth:`FromObject.attr_names` and *exclude*.
        """
        include = self.include if self.include != None else self.attr_names()
        include += self.include_extra
        exclude = self.exclude if self.exclude != None else []
        return set(include) - set(exclude)

    def iter_input(self, inpt):
        for name in self.calculate_include():
            yield name, self.get_getter(name)(inpt, name)

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

class ToObject(ContainerCast):
    
    defaults = dict(
        class_to_setter = {object: setattr,},
        attrname_to_setter = {}
    )

    def get_to_class(self, key):
        return NotImplemented

    @abc.abstractmethod
    def new_object(self, items):
        """
        Args:
            items(dict). A dictionary containing all the casted items. You must delete the item from the dictionary once you have handled it, or leave it if you don't want to handle it. 

        Returns:
            object. An object created with the bare minimum from *items*. The rest will be automatically set by the cast, using the defined setters.
        """
        return

    def build_output(self, items_iter):
        items = dict(items_iter)
        new_object = self.new_object(items)
        for name, value in items.items():
            self.get_setter(name)(new_object, name, value)
        return new_object

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

class RouteToOperands(ContainerCast):

    defaults = dict(
        operands = []
    )

    def iter_output(self, items_iter):
        for key, value in items_iter:            
            yield key, self.operands[key](value)

class ConcatDict(ContainerCast):

    def build_output(self, items_iter):
        concat_dict = {}
        for key, value in items_iter:
            concat_dict.update(value)
        return concat_dict

class SplitDict(ContainerCast):
    
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
