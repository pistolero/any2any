# -*- coding: utf-8 -*-
import copy
try:
    import abc
except ImportError:
    from compat import abc
from base import Cast
from utils import closest_parent, SpecializedType, Mm, memoize

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

    def get_item_from(self, key):
        """
        Returns:
            type or NotImplemented. The type of the value associated with *key* if it is known `a priori` (without knowing the input), or *NotImplemented* to let the cast guess.
        """
        return NotImplemented

    def get_item_to(self, key):
        """
        Returns:
            type or NotImplemented. Type the value associated with *key* must be casted to, if it is known `a priori` (without knowing the input), or NotImplemented.
        """
        return NotImplemented

    def call(self, inpt):
        iter_input = self.iter_input(inpt)
        iter_ouput = self.iter_output(iter_input)
        return self.build_output(iter_ouput)

# Specialized types
#======================================
class ObjectType(SpecializedType):
    #TODO: for looking-up best mm, when several superclasses in ObjectType, when several Mm match, choose the best one.
    # ex : Journal, ForeignKey
    #TODO: Spz(atype) doesn't match to Mm(atype), but Mm(from_any=atype) -> change Spz.__eq__
    #TODO: if Mm(aspztype) matches Mm(atype): cast, then cast's from_ will be overriden, along with its schema.  
    #TODO: rename to 'wrapped' instead of 'specialized'
    #TODO: document

    defaults = dict(
        extra_schema = {},
        include = [],
        exclude = [],
        factory = None,
    )

    def get_class(self, key):
        schema = self.get_schema()
        if key in schema:
            return schema[key]
        else:
            raise KeyError("'%s' not in schema" % key)

    def get_schema(self):
        schema = self.default_schema()
        schema.update(self.extra_schema)
        if self.include:
            [schema.setdefault(k, NotImplemented) for k in self.include]
            [schema.pop(k) for k in schema.keys() if k not in self.include]
        if self.exclude:
            [schema.pop(k, None) for k in self.exclude]
        for key, cls in schema.iteritems():
            # If NotImplemented, we make a guess.
            if cls == NotImplemented:
                cls = self.guess_class(key)
            schema[key] = cls
        return schema

    def guess_class(self, key):
        """
        """
        return NotImplemented

    def default_schema(self):
        """
        """
        return {}

class ContainerType(SpecializedType):

    defaults = dict(
        value_type = NotImplemented,
        factory = None,
    )

    def __superclasshook__(self, C):
        if super(ContainerType, self).__superclasshook__(C):
            if isinstance(C, ContainerType):
                return SpecializedType.issubclass(self.value_type, C.value_type)
            else:
                return True
        else:
            return False

    def __repr__(self):
        return 'Spz%s%s' % (self.base.__name__.capitalize(),
        '' if self.value_type == NotImplemented else 'Of%s' % self.value_type)

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
        from_ = self.get_item_from(key)
        to = self.get_item_to(key)
        # If NotImplemented, we make guesses
        if from_ == NotImplemented:
            from_ = type(value)
        if to == NotImplemented:
            return Mm(from_=from_, to_any=object)
        return Mm(from_, to)

    # TODO: PB ! That's not always optimal ... e.g. with a (big) list
    @memoize(key=lambda args, kwargs: (args[0], type(args[1])))
    def cast_for_item(self, key, value):
        # Returns the cast to use for item *key*, *value*.
        # The lookup order is the following :
        #   1. setting *key_to_cast*
        #   2. setting *value_cast*
        #   3. finally, the method gets the metamorphosis to apply on the item
        #       and a suitable cast by calling *Cast.cast_for*.
        self.log('Item %s' % key)
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
    @memoize()
    def key_cast(self):
        key_cast = copy.copy(self.settings['key_cast'])
        key_cast.settings.update({
            'from_': self.from_,
            'to': self.to
        })
        return key_cast
            
    @property
    @memoize()
    def value_cast(self):
        return copy.copy(self.settings['value_cast'])

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

class FromMapping(DivideAndConquerCast):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.

    :meth:`get_item_from` can guess the type of values if *from_* is a :class:`ContainerType`.    
    """

    defaults = dict(from_spz = ContainerType)

    def get_item_from(self, key):
        return self.from_.value_type

    def iter_input(self, inpt):
        return inpt.iteritems()

class ToMapping(DivideAndConquerCast):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.build_output`.

    :meth:`get_item_to` can guess the type of values if *to* is a :class:`ContainerType`.    
    """

    defaults = dict(to_spz = ContainerType)

    def get_item_to(self, key):
        return self.to.value_type

    def build_output(self, items_iter):
        return self.to(items_iter)

class FromIterable(DivideAndConquerCast):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.

    :meth:`get_item_from` can guess the type of values if *from_* is a :class:`ContainerType`.    
    """

    defaults = dict(from_spz = ContainerType)

    def get_item_from(self, key):
        return self.from_.value_type

    def iter_input(self, inpt):
        return enumerate(inpt)

class ToIterable(DivideAndConquerCast):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.build_output`.

    :meth:`get_item_to` can guess the type of values if *to* is a :class:`ContainerType`.    
    """

    defaults = dict(to_spz = ContainerType)

    def get_item_to(self, key):
        return self.to.value_type

    def build_output(self, items_iter):
        return self.to((value for key, value in items_iter))

class FromObject(DivideAndConquerCast):
    """
    Mixin for :class:`DivideAndConquerCast`. Implements :meth:`DivideAndConquerCast.iter_input`.
    """
    # TODO: document settings
    # TODO: refactor with object SpecializedType
    defaults = dict(
        from_spz = ObjectType,
        class_to_getter = {object: getattr,},
        attrname_to_getter = {},
    )

    def get_item_from(self, key):
        return self.from_.get_class(key)

    def iter_input(self, inpt):
        for name in self.from_.get_schema().keys():
            yield name, self.get_getter(name)(inpt, name)

    def get_getter(self, name):
        # try to get accessor on a per-attribute basis
        if name in self.attrname_to_getter:
            return self.attrname_to_getter[name]
        # otherwise try to get it on a per-class basis
        else:
            attr_class = self.get_item_from(name)
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
        to_spz = ObjectType,
        class_to_setter = {object: setattr,},
        attrname_to_setter = {}
    )

    def get_item_to(self, key):
        return self.to.get_class(key)

    def build_output(self, items_iter):
        # TODO: bad because it breaks the laziness of generators
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
            attr_class = self.get_item_to(name)
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
