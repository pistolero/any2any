# -*- coding: utf-8 -*-
import datetime

from base import Cast
from daccasts import (FromMapping, ToMapping, FromIterable, ToIterable, FromObject, ToObject,
ContainerWrap, CastItems)
from types import FunctionType

class Identity(Cast):
    """
    Identity operation :

        >>> Identity()('1')
        '1'
    """

    def call(self, obj):
        return obj


class ToType(Cast):
    """
    Dumb cast :

        >>> to_int = ToType(to=int) # equivalent to >>> int('1')
        >>> to_int('1')
        1
    """

    def call(self, obj):
        return self.to(obj)


class MappingToMapping(FromMapping, CastItems, ToMapping):
    """
    Dictionaries to dictionaries :

        >>> MappingToMapping()({'1': anObject1, 2: anObject2})
        {'1': 'its casted version 1', 2: 'its casted version 2'}
    """
    pass


class IterableToIterable(FromIterable, CastItems, ToIterable):
    """
    List to list :

        >>> IterableToIterable()([anObject1, anObject2])
        ['its casted version 1', 'its casted version 2']
    """
    pass


class ObjectToMapping(FromObject, CastItems, ToMapping):
    """
    Object to dictionary :

        >>> ObjectToMapping()(anObject)
        {'attr1': 'its casted value', 'attr2': 'its casted value'}
    """
    pass


class MappingToObject(FromMapping, CastItems, ToObject):
    """
    Dictionary to object :

        >>> cast = MappingToObject(to=SomeObject)
        >>> cast({'attr1': 'its casted value 1', 'attr2': 'its casted value 2'})
        <SomeObject>
    """
    pass
