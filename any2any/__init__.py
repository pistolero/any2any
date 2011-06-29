# -*- coding: utf-8 -*-
import datetime

from simple import (ListToList, DictToDict, Identity, ObjectToDict,
DictToObject, DateToDict, DateTimeToDict, DictToDate, DictToDateTime, ContainerType)
from base import register#, cast_map
from utils import Mm

register(Identity(), Mm(from_any=object, to_any=object))

register(
    ListToList(),
    Mm(from_any=list, to_any=list),
)
#TODO:
"""
register(
    ListToList(mm=Mm(Spz(tuple, object), Spz(tuple, object))),
    Mm(from_any=tuple, to_any=tuple),
)
"""
register(
    DictToDict(),
    Mm(from_any=dict, to_any=dict),
)
register(ObjectToDict(), Mm(to=dict))
register(DictToObject(), Mm(from_=dict))
register(DateToDict(), Mm(datetime.date, dict))
register(DateTimeToDict(), Mm(datetime.datetime, dict))
register(DictToDate(), Mm(dict, datetime.date))
register(DictToDateTime(), Mm(dict, datetime.datetime))

# TODO:
"""
def any2any(obj, klass):
    mm = (type(obj), klass)
    choice = closest_mm(mm, cast_map.keys())
    cast = cast_map[choice]
    return cast.copy(settings={'mm': mm})(obj)
"""
