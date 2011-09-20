# -*- coding: utf-8 -*-
import datetime

from simple import (IterableToIterable, MappingToMapping, Identity, ObjectToMapping,
MappingToObject, ContainerType, MappingToDate, MappingToDateTime)
from base import register#, cast_map
from utils import Mm, Spz
from daccasts import ObjectType

register(Identity(), Mm(from_any=object, to_any=object))

# TODO: rewrite when there'll be a MmSet object
register(
    IterableToIterable(to=list),
    Mm(from_any=list),
)
register(
    IterableToIterable(to=tuple),
    Mm(from_any=tuple),
)
register(
    MappingToMapping(to=dict),
    Mm(from_any=dict),
)
register(ObjectToMapping(), Mm(to=dict))
register(MappingToObject(), Mm(from_=dict))

datetime_type = ObjectType(datetime.datetime, extra_schema={
    'year': Spz(int, float),
    'month': Spz(int, float),
    'day': Spz(int, float),
    'hour': Spz(int, float),
    'minute': Spz(int, float),
    'second': Spz(int, float),
    'microsecond': Spz(int, float),
})
date_type = ObjectType(datetime.date, extra_schema={
    'year': Spz(int, float),
    'month': Spz(int, float),
    'day': Spz(int, float),
})
register(ObjectToMapping(from_=date_type, to=dict), Mm(from_any=datetime.date))
register(ObjectToMapping(from_=datetime_type, to=dict), Mm(from_any=datetime.datetime))
register(MappingToDate(to=date_type), Mm(to_any=datetime.date))
register(MappingToDateTime(to=datetime_type), Mm(to_any=datetime.datetime))
# TODO:
"""
def any2any(obj, klass):
    mm = (type(obj), klass)
    choice = closest_mm(mm, cast_map.keys())
    cast = cast_map[choice]
    return cast.copy(settings={'mm': mm})(obj)
"""
