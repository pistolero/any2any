# -*- coding: utf-8 -*-

from simple import ListToList, DictToDict, Identity, ObjectToDict, DictToObject
from base import register#, cast_map
from utils import Spz, Mm

register(Identity(), Mm(from_any=object, to_any=object))
register(
    ListToList(mm=Mm(Spz(list, object), Spz(list, object))),
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
    DictToDict(mm=Mm(Spz(dict, object), Spz(dict, object))),
    Mm(from_any=dict, to_any=dict),
)
register(ObjectToDict(), Mm(from_any=object, to=dict))
register(DictToObject(), Mm(from_=dict, to_any=object))

# TODO:
"""
def any2any(obj, klass):
    mm = (type(obj), klass)
    choice = closest_mm(mm, cast_map.keys())
    cast = cast_map[choice]
    return cast.copy(settings={'mm': mm})(obj)
"""
