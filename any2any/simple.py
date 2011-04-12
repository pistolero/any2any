from base import Cast, CastSettings, Mm, Spz
from objectcast import ObjectCast
from utils import closest_parent


class Identity(Cast):
    """
    Identity operation. Default cast for the conversion **(object, object)**.

        >>> Identity()('1')
        '1'
    """
    defaults = CastSettings(
        mm = Mm(object, object)
    )

    def call(self, obj):
        return obj


class ObjectCast(Cast):

    def iter_input(self, inpt):
        raise NotImplementedError()

    def cast_for_item(self, name, value):
        raise NotImplementedError()

    def iter_output(self, items):
        for name, value in items:
            cast = self.cast_for_item(name, value)
            yield name, cast(value)

    def build_output(self, items_iter):
        raise NotImplementedError()

    def call(self, inpt):
        iter_input = self.iter_input(inpt)
        iter_ouput = self.iter_output(iter_input)
        return self.build_output(iter_ouput)


class FromDict(object):
    
    def iter_input(self, inpt):
        return inpt.iteritems()


class ToDict(object):
    
    def build_output(self, items_iter):
        return dict(items_iter)


class ObjectSchemaMixin(object):
    """
        include(list). Example :
            
            >>> cast = SomeObjectCast(include=['a', 'b']) #Attributes 'a' and 'b' are handled by the cast operation.

        include(list). Names of attributes to exclude from the cast.
    """
    defaults = CastSettings(
        include = [],
        exclude = [],
        input_class_to_output_class = {object: object},
        index_to_cast = {},
    )

    def attr_names(self):
        """
        Returns:
            list. The list of attribute names included by default.
    
        .. warning:: This method will only be called if :attr:`include` is empty.

        .. note:: Override this method if you want to build dynamically the list of attributes to include by default.
        """
        return []

    def calculate_include(self):
        """
        Returns:
            set. The set of attributes to include for the current operation. Take into account *include* or :meth:`attr_names` and *exclude*.
        """
        include = self.include if self.include != None else self.attr_names()
        exclude = self.exclude if self.exclude != None else []
        return set(include) - set(exclude)

    def cast_for_item(self, name, value)
        self.log('Attribute ' + name)
        #try to get serializer with the per-attribute map
        if name in self.index_to_cast:
            cast = self.index_to_cast.get(name)
            cast = cast.copy({}, self)
        #otherwise try to build it by getting attribute's class
        else:
            attr_class = self.get_output_class(name, inpt) # TODO
            cast = self.cast_for(Mm(type(value), attr_class), {})
        cast._context = self._context.copy()
        return cast

    def get_output_class(self, name, inpt):
        fittest = closest_parent(type(inpt), self.input_class_to_output_class.keys())
        return self.input_class_to_output_class[fittest]


class FromObject(object):
    
    defaults = CastSettings(
        attr_class_to_getter = {object: getattr,},
        attr_name_to_getter = {}
    )

    def iter_input(self, inpt):
        for name in self.calculate_include():
            yield name, self._get_attr_accessor(name)(inpt, name)

    def _get_attr_accessor(self, name):
        # try to get accessor on a per-attribute basis
        if self.attr_name_to_getter and name in self.attr_name_to_getter:
            return self.attr_name_to_getter[name]
        # otherwise try to get it on a per-class basis
        else:
            attr_class = self._get_attr_class(name)# TODO
            closer_parent = closest_parent(attr_class, self.attr_class_to_getter.keys())
            return self.attr_class_to_getter[closer_parent]


class ToObject(object):
    
    defaults = CastSettings(
        attr_class_to_setter = {object: setattr,},
        attr_name_to_setter = {}
    )

    def build_output(self, items_iter):
        new_object = self.mm.to()
        for name, value in items_iter:
            self._get_attr_accessor(name)(new_object, name, value)

    def _get_attr_accessor(self, name):
        # try to get accessor on a per-attribute basis
        if self.attr_name_to_setter and name in self.attr_name_to_setter:
            return self.attr_name_to_setter[name]
        # otherwise try to get it on a per-class basis
        else:
            attr_class = self._get_attr_class(name)# TODO
            closer_parent = closest_parent(attr_class, self.attr_class_to_setter.keys())
            return self.attr_class_to_setter[closer_parent]

class ContainerCast(ObjectCast):
    defaults = CastSettings(
        mm = Mm(Spz(dict, object), Spz(dict, object)),
        element_cast = None,
        output_type = list,
    )

    def cast_for_item(self, index):
        return self.element_cast or self.cast_for(self.elem_mm, {'mm': self.elem_mm})

    @property
    def elem_mm(self):
        return Mm(self.mm.from_any.feature, self.mm.to.feature)


class MappingCast(FromDict, ToDict, ContainerCast):
    """
    Cast for dictionaries.

        >>> MappingCast()({'1': anObject1, '2': anObject2})
        {'1': 'its converted version 1', '2': 'its converted version 2'}
    """
    """
    Cast for lists and tuples.

        >>> SequenceCast()([anObject1, anObject2])
        ['its converted version 1', 'its converted version 2']
    """
    pass


class SequenceCast(ContainerCast):
    """
    Cast for lists and tuples.

        >>> SequenceCast()([anObject1, anObject2])
        ['its converted version 1', 'its converted version 2']
    """
    def iter_input(self, inpt):
        return enumerate(inpt)

    def build_output(self, items_iter):
        return self.mm.to.base([value for name, value in items_iter])


class ObjectToDict(FromObject, ToDict, ObjectCast):

    def cast_for_item(self, index):# TODO : REDO
        return self.element_cast or self.cast_for(self.elem_mm, {'mm': self.elem_mm})

    def attr_names(self, obj):
        return filter(lambda n: n[0] != '_', list(obj.__dict__))


class DictToObject(FromDict, ToObject, ObjectCast):

    def cast_for_item(self, index):# TODO : REDO
        return self.element_cast or self.cast_for(self.elem_mm, {'mm': self.elem_mm})

    def attr_names(self, obj):
        return filter(lambda n: n[0] != '_', list(obj.__dict__))
