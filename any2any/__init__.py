# -*- coding: utf-8 -*-
#'SpitEat'
#Copyright (C) 2011 Sébastien Piquemal @ futurice
#contact : sebastien.piquemal@futurice.com
#futurice's website : www.futurice.com

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

from simple import ListToList, DictToDict, Identity
from base import register#, cast_map
#from simple import ObjectToDict, DictToObject
from utils import Spz, Mm

register(Identity(), [Mm(from_any=object, to_any=object)])

list_mm = Mm(Spz(list, object), Spz(list, object))
register(ListToList(mm=list_mm), [Mm(from_any=list, to_any=list)])

tuple_mm = Mm(Spz(tuple, object), Spz(tuple, object))
register(ListToList(mm=tuple_mm), [Mm(from_any=tuple, to_any=tuple)])

mapping_mm = Mm(Spz(dict, object), Spz(dict, object))
register(DictToDict(), [Mm(from_any=dict, to_any=dict)])

#register(ObjectToDict(), [Mm(object, dict)])

#register(DictToObject(), [Mm(dict, object)])
"""
def any2any(obj, klass):
    mm = (type(obj), klass)
    choice = closest_mm(mm, cast_map.keys())
    cast = cast_map[choice]
    return cast.copy(settings={'mm': mm})(obj)
"""
