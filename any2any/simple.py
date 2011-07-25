# -*- coding: utf-8 -*-
import datetime

from base import Cast
from containercast import FromDict, ToDict, FromList, ToList, FromObject, ToObject, ContainerType, CastItems
from types import FunctionType
from combine import ConcatDict, SplitDict, RouteToOperands

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


class DictToDict(FromDict, CastItems, ToDict):
    """
    Dictionaries to dictionaries :

        >>> DictToDict()({'1': anObject1, 2: anObject2})
        {'1': 'its casted version 1', 2: 'its casted version 2'}
    """
    pass


class ListToList(FromList, CastItems, ToList):
    """
    List to list :

        >>> ListToList()([anObject1, anObject2])
        ['its casted version 1', 'its casted version 2']
    """
    pass


class ObjectToDict(FromObject, CastItems, ToDict):
    """
    Object to dictionary :

        >>> ObjectToDict()(anObject)
        {'attr1': 'its casted value', 'attr2': 'its casted value'}
    """

    def attr_names(self):
        inpt = self._context['input']
        names = filter(lambda name: name[0] != '_', list(inpt.__dict__))
        return filter(lambda name: not isinstance(getattr(inpt, name), FunctionType), names)


class DictToObject(FromDict, CastItems, ToObject):
    """
    Dictionary to object :

        >>> cast = DictToObject(to=SomeObject)
        >>> cast({'attr1': 'its casted value 1', 'attr2': 'its casted value 2'})
        <SomeObject>
    """

    def new_object(self, kwargs):
        return self.to()


class DateTimeToDict(FromObject, CastItems, ToDict):
    """
    Datetime to dict:

        >>> cast = DateTimeToDict()
        >>> cast(datetime(year=1986, month=12, day=8)) == {
        ...     'year': 1986,
        ...     'month': 12,
        ...     'day': 8,
        ...     'hour': 0,
        ...     'minute': 0,
        ...     'second': 0,
        ...     'microsecond': 0,
        ... }
        True
    """
    
    def attr_names(self):
        return ['year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond']


class DateToDict(FromObject, CastItems, ToDict):
    """
    date to dict:

        >>> cast = DateToDict()
        >>> cast(date(year=1984, month=1, day=18)) == {
        ...     'year': 1984,
        ...     'month': 1,
        ...     'day': 18,
        ... }
        True
    """
    
    def attr_names(self):
        return ['year', 'month', 'day']


class DateTimeToDict(FromObject, CastItems, ToDict):
    """
    datetime to dict:

        >>> cast = DateTimeToDict()
        >>> cast(datetime(year=1986, month=12, day=8)) == {
        ...     'year': 1986,
        ...     'month': 12,
        ...     'day': 8,
        ...     'hour': 0,
        ...     'minute': 0,
        ...     'second': 0,
        ...     'microsecond': 0,
        ... }
        True
    """
    
    def attr_names(self):
        return ['year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond']


class DictToDate(FromDict, CastItems, ToObject):
    """
    dict to date:

        >>> cast = DictToDate()
        >>> cast(dict(year=1984, month=1, day=18)) == date(year=1984, month=1, day=18)
        True
    """
    
    def new_object(self, items):
        new_date = datetime.date(**items)
        items.clear()
        return new_date


class DictToDateTime(FromDict, CastItems, ToObject):
    """
    dict to datetime:

        >>> cast = DictToDateTime()
        >>> cast(dict(year=2012, month=4, day=26, second=54)) == datetime(year=2012, month=4, day=26, second=54)
        True
    """
    
    def new_object(self, items):
        new_datetime = datetime.datetime(**items)
        items.clear()
        return new_datetime


class ConcatDict(SplitDict, RouteToOperands, ConcatDict):
    """
    """
    def get_route(self, key, value):
        return 0
