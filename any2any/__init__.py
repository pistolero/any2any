# -*- coding: utf-8 -*-
import datetime

from simple import (IterableToIterable, MappingToMapping, Identity, ObjectToMapping,
MappingToObject, DateToMapping, DateTimeToMapping, MappingToDate, MappingToDateTime, ContainerType)
from base import register#, cast_map
from utils import Mm

register(Identity(), Mm(from_any=object, to_any=object))

# TODO: rewrite when there'll be a MmSet object
register(
    IterableToIterable(),
    Mm(from_any=list, to_any=list),
)
register(
    IterableToIterable(),
    Mm(from_any=tuple, to_any=tuple),
)
register(
    MappingToMapping(),
    Mm(from_any=dict, to_any=dict),
)
register(ObjectToMapping(), Mm(to=dict))
register(MappingToObject(), Mm(from_=dict))
register(DateToMapping(), Mm(datetime.date, dict))
register(DateTimeToMapping(), Mm(datetime.datetime, dict))
register(MappingToDate(), Mm(dict, datetime.date))
register(MappingToDateTime(), Mm(dict, datetime.datetime))

# TODO:
"""
def any2any(obj, klass):
    mm = (type(obj), klass)
    choice = closest_mm(mm, cast_map.keys())
    cast = cast_map[choice]
    return cast.copy(settings={'mm': mm})(obj)
"""
