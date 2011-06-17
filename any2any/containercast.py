# -*- coding: utf-8 -*-
try:
    import abc
except ImportError:
    from compat import abc
from base import Cast
from utils import closest_parent, SpecializedType, Mm


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
    Base cast for metamorphosing `from` and `to` containers-like objects.
    By "container", we mean any object that holds other objects.
    This basically means : any Python object (because an object contains attributes),
    any kind of sequence, any kind of mapping, ...

    Let's use the same terms as for Python dictionaries and call :

        - `key` a contained object identifier
        - `value` the contained object itself
        - `item` a contained object along with its identifier 

    In order to cast containers, this class uses the following flow :

        #. Iterating on input's items, see :meth:`ContainerCast.iter_input`.
        #. Casting all values, see :meth:`ContainerCast.iter_output`.
        #. Building output with casted items, see :meth:`ContainerCast.build_output`.

    :class:`ContainerCast` defines the following settings :

        - key_to_cast(dict). ``{<key>: <cast>}``. Maps a key with the cast to use.
        - value_cast(Cast). The cast to use on all values.
        - key_to_mm(dict). ``{<key>: <mm>}``. Maps a key with the metamorphosis to realize.
    """
    #TODO: document key_cast + item_strip
    #TODO: key_cast is ugly ...

    defaults = dict(
        key_to_cast = {},
        key_to_mm = {},
        value_cast = None,
        key_cast = None,
        _schema = {
            'key_cast': {'customize': 'do_nothing'},
        },
    )

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
    def get_from_class(self, key):
        """
        Returns:
            type or NotImplemented. The type of the value associated with *key* if it is known `a priori` (without knowing the input), or `NotImplemented` to let the cast guess.
        """
        return NotImplemented

    @abc.abstractmethod
    def get_to_class(self, key):
        """
        Returns:
            type or NotImplemented. Type the value associated with *key* must be casted to, if it is known `a priori` (without knowing the input), or NotImplemented.
        """
        return NotImplemented

    def get_item_mm(self, key, value):
        """
        Returns:
            Mm. The metamorphosis to apply on item *key*, *value*.
        """
        from_ = self.get_from_class(key)
        to = self.get_to_class(key)
        # If NotImplemented, we make guesses
        if from_ == NotImplemented:
            from_ = type(value)
        if to == NotImplemented:
            to = object
        return Mm(from_, to)

    @abc.abstractmethod
    def build_output(self, items_iter):
        """
        Args:
            items_iter(iterator). ``(<key>, <casted_value>)``. Iterator on casted items.

        Returns:
            object. The casted object in its final shape.
        """
        return

    def cast_for_item(self, key, value):
        """
        This method allows to select the cast to use for a given item. The lookup order is the following :

            #. setting :attr:`key_to_cast`
            #. setting :attr:`value_cast`
            #. finally, the method gets the metamorphosis to apply on the item and a suitable cast by calling :meth:`Cast.cast_for`.  
        """
        self.log('Item %s' % key)
        #try to get serializer with the per-attribute map
        if key in self.key_to_cast:
            cast = self.key_to_cast.get(key)
            cast = cast.copy()
        elif self.value_cast:
            return self.value_cast
        #otherwise try to build it by getting attribute's class
        else:
            if key in self.key_to_mm:
                mm = self.key_to_mm[key]
            else:
                mm = self.get_item_mm(key, value)
            cast = self.cast_for(mm)
        cast._context = self._context.copy()# TODO: USELESS ?
        return cast

    def cast_key(self, key):
        """
        Takes a key as input, casts it with :class:`key_cast`, and returns it.
        """
        return self._get_key_cast()(key)

    def _get_key_cast(self):
        if not hasattr(self, '_custom_key_cast'):
            self._custom_key_cast = self.key_cast.copy({
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

    def iter_output(self, items_iter):
        """
        Args:
            items_iter(iterator). An iterator on input's items.

        Returns:
            iterator. An iterator on casted items.
        """
        for key, value in items_iter:
            if self.strip_item(key, value): continue
            if self.key_cast: key = self.cast_key(key)
            cast = self.cast_for_item(key, value)
            yield key, cast(value)

    def call(self, inpt):
        iter_input = self.iter_input(inpt)
        iter_ouput = self.iter_output(iter_input)
        return self.build_output(iter_ouput)


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
            return self.class_to_getter[parent]


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
            return self.class_to_setter[parent]

