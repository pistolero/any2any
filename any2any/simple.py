from base import Cast, CastSettings, Mm, Spz
from containercast import ContainerCast, FromDictMixin, ToDictMixin, FromListMixin, ToListMixin, FromObjectMixin, ToObjectMixin, GuessMmMixin
from types import FunctionType


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


class DictToDict(GuessMmMixin, FromDictMixin, ToDictMixin, ContainerCast):
    """
    Cast for dictionaries.

        >>> DictToDict()({'1': anObject1, '2': anObject2})
        {'1': 'its converted version 1', '2': 'its converted version 2'}
    """
    defaults = CastSettings(
        mm = Mm(dict, Spz(dict, object))
    )


class ListToList(GuessMmMixin, FromListMixin, ToListMixin, ContainerCast):
    """
    Cast for lists and tuples.

        >>> ListToList()([anObject1, anObject2])
        ['its converted version 1', 'its converted version 2']
    """
    defaults = CastSettings(
        mm = Mm(list, Spz(list, object))
    )


class ObjectToDict(GuessMmMixin, FromObjectMixin, ToDictMixin, ContainerCast):

    def attr_names(self):
        inpt = self._context['input']
        names = filter(lambda name: name[0] != '_', list(inpt.__dict__))
        return filter(lambda name: not isinstance(getattr(inpt, name), FunctionType), names)


class DictToObject(GuessMmMixin, FromDictMixin, ToObjectMixin, ContainerCast):

    def new_object(self, kwargs):
        return self.mm.to()

