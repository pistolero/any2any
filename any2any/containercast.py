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
from base import Cast, CastSettings, Mm, Spz

class ContainerCast(Cast):

    defaults = CastSettings(
        index_to_cast = {},
        index_to_mm = {},
    )

    def iter_input(self, inpt):
        """
        Returns:
            iterator. (<index>, <value>)
        """
        raise NotImplementedError()

    def get_mm(self, index, value):
        """
        Returns:
            Mm. The metamorphosis to apply on item <index>.
        """
        raise NotImplementedError()

    def build_output(self, items_iter):
        """
        Returns:
            object. The casted object in its final shape.
        """
        raise NotImplementedError()

    def cast_for_item(self, index, value):
        self.log('Item %s' % index)
        #try to get serializer with the per-attribute map
        if index in self.index_to_cast:
            cast = self.index_to_cast.get(index)
            cast = cast.copy({}, self)
        #otherwise try to build it by getting attribute's class
        else:
            if index in self.index_to_mm:
                mm = self.index_to_mm[index]
            else:
                mm = self.get_mm(index, value)
            cast = self.cast_for(mm, {})
        cast._context = self._context.copy()# TODO: USELESS ?
        return cast

    def iter_output(self, items):
        for index, value in items:
            cast = self.cast_for_item(index, value)
            yield index, cast(value)

    def call(self, inpt):
        iter_input = self.iter_input(inpt)
        iter_ouput = self.iter_output(iter_input)
        return self.build_output(iter_ouput)


class FromDictMixin(object):
    
    def iter_input(self, inpt):
        return inpt.iteritems()


class ToDictMixin(object):
    
    def build_output(self, items_iter):
        return dict(items_iter)


class FromObjectMixin(object):
    
    defaults = CastSettings(
        class_to_getter = {object: getattr,},
        index_to_getter = {},
    )

    def iter_input(self, inpt):
        for index in self.calculate_include():
            yield index, self.get_attr_accessor(index)(inpt, index)

    def get_attr_accessor(self, index):
        # try to get accessor on a per-attribute basis
        if self.index_to_getter and index in self.index_to_getter:
            return self.index_to_getter[index]
        # otherwise try to get it on a per-class basis
        else:
            attr_class = self._get_attr_class(index)# TODO
            closer_parent = closest_parent(attr_class, self.class_to_getter.keys())
            return self.class_to_getter[closer_parent]


class ToObjectMixin(object):
    
    defaults = CastSettings(
        attr_class_to_setter = {object: setattr,},
        attr_name_to_setter = {}
    )

    def build_output(self, items_iter):
        new_object = self.mm.to()
        for name, value in items_iter:
            self.get_attr_accessor(name)(new_object, name, value)

    def get_attr_accessor(self, name):
        # try to get accessor on a per-attribute basis
        if self.attr_name_to_setter and name in self.attr_name_to_setter:
            return self.attr_name_to_setter[name]
        # otherwise try to get it on a per-class basis
        else:
            attr_class = self._get_attr_class(name)# TODO
            closer_parent = closest_parent(attr_class, self.attr_class_to_setter.keys())
            return self.attr_class_to_setter[closer_parent]

