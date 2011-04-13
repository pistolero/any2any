from base import Cast, CastSettings, Mm, Spz
from containercast import ContainerCast, FromDictMixin, ToDictMixin, FromObjectMixin, ToObjectMixin


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


class MappingCast(FromDictMixin, ToDictMixin, ContainerCast):
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
    def get_mm(self, index, value):
        return Mm(type(value), object)


class SequenceCast(ContainerCast):
    """
    Cast for lists and tuples.

        >>> SequenceCast()([anObject1, anObject2])
        ['its converted version 1', 'its converted version 2']
    """
    def iter_input(self, inpt):
        return enumerate(inpt)

    def get_mm(self, index, value):
        return Mm(type(value), object)

    def build_output(self, items_iter):
        return [value for index, value in items_iter]


class ObjectToDict(FromObjectMixin, ToDictMixin, ContainerCast):

    def attr_names(self, obj):
        return filter(lambda n: n[0] != '_', list(obj.__dict__))


class DictToObject(FromDictMixin, ToObjectMixin, ContainerCast):

    def attr_names(self, obj):
        return filter(lambda n: n[0] != '_', list(obj.__dict__))

