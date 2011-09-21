# -*- coding: utf-8 -*-
import datetime

from simple import (IterableToIterable, MappingToMapping, Identity, ObjectToMapping,
MappingToObject, ContainerWrap)
from base import register#, cast_map
from utils import Mm, Wrap
from daccasts import ObjectWrap

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

WrappedDateTime = ObjectWrap(datetime.datetime, extra_schema={
    'year': Wrap(int, float),
    'month': Wrap(int, float),
    'day': Wrap(int, float),
    'hour': Wrap(int, float),
    'minute': Wrap(int, float),
    'second': Wrap(int, float),
    'microsecond': Wrap(int, float),
})
WrappedDate = ObjectWrap(datetime.date, extra_schema={
    'year': Wrap(int, float),
    'month': Wrap(int, float),
    'day': Wrap(int, float),
})
register(ObjectToMapping(from_=WrappedDate, to=dict), Mm(from_any=datetime.date))
register(ObjectToMapping(from_=WrappedDateTime, to=dict), Mm(from_any=datetime.datetime))
register(MappingToObject(to=WrappedDate), Mm(to_any=datetime.date))
register(MappingToObject(to=WrappedDateTime), Mm(to_any=datetime.datetime))
# TODO:
"""
def any2any(obj, klass):
    mm = (type(obj), klass)
    choice = closest_mm(mm, cast_map.keys())
    cast = cast_map[choice]
    return cast.copy(settings={'mm': mm})(obj)
"""
