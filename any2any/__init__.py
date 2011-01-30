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
"""
"""
from base import SequenceCast, MappingCast, register, Identity
from utils import specialize

register(Identity(), conversions=[(object, object)])

list_conversion = (specialize(list, object), specialize(list, object))
register(SequenceCast(conversion=list_conversion), conversions=[(list, list)])

tuple_conversion = (specialize(tuple, object), specialize(tuple, object))
register(SequenceCast(conversion=tuple_conversion), conversions=[(tuple, tuple)])

mapping_conversion = (specialize(dict, object), specialize(dict, object))
register(MappingCast(), conversions=[(dict, dict)])
