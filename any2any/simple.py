# -*- coding: utf-8 -*-
from base import Cast, CastSettings, Mm, Spz
from containercast import ContainerCast, FromDict, ToDict, FromList, ToList, FromObject, ToObject
from types import FunctionType


class Identity(Cast):
    """
    Identity operation :

        >>> Identity()('1')
        '1'
    """
    defaults = CastSettings(
        mm = Mm(object, object)
    )

    def call(self, obj):
        return obj


class DictToDict(FromDict, ToDict, ContainerCast):
    """
    Dictionaries to dictionaries :

        >>> DictToDict()({'1': anObject1, 2: anObject2})
        {'1': 'its casted version 1', 2: 'its casted version 2'}
    """
    defaults = CastSettings(
        mm = Mm(dict, Spz(dict, object))
    )


class ListToList(FromList, ToList, ContainerCast):
    """
    List to list :

        >>> ListToList()([anObject1, anObject2])
        ['its casted version 1', 'its casted version 2']
    """
    defaults = CastSettings(
        mm = Mm(list, Spz(list, object))
    )


class ObjectToDict(FromObject, ToDict, ContainerCast):
    """
    Object to dictionary :

        >>> ObjectToDict()(anObject)
        {'attr1': 'its casted value', 'attr2': 'its casted value'}
    """

    def attr_names(self):
        inpt = self._context['input']
        names = filter(lambda name: name[0] != '_', list(inpt.__dict__))
        return filter(lambda name: not isinstance(getattr(inpt, name), FunctionType), names)


class DictToObject(FromDict, ToObject, ContainerCast):
    """
    Dictionary to object :

        >>> cast = ObjectToDict(mm=Mm(from=dict, to=SomeObject))
        >>> cast({'attr1': 'its casted value 1', 'attr2': 'its casted value 2'})
        <SomeObject>
    """

    def new_object(self, kwargs):
        return self.mm.to()

