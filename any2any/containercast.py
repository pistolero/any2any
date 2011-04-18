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
import abc
from base import Cast, CastSettings, Mm, Spz
from utils import closest_parent

class ContainerCast(Cast):

    defaults = CastSettings(
        index_to_cast = {},
        index_to_mm = {},
        element_cast = None,
    )

    @abc.abstractmethod
    def iter_input(self, inpt):
        """
        Returns:
            iterator. (<index>, <value>)
        """
        return

    @abc.abstractmethod
    def get_item_from(self, index):
        return

    @abc.abstractmethod
    def get_item_to(self, index):
        return

    def get_item_mm(self, index, value):
        """
        Returns:
            Mm. The metamorphosis to apply on item <index>.
        """
        from_ = self.get_item_from(index) or type(value)
        to = self.get_item_to(index) or object
        return Mm(from_, to)

    @abc.abstractmethod
    def build_output(self, items_iter):
        """
        Returns:
            object. The casted object in its final shape.
        """
        return

    def cast_for_item(self, index, value):
        self.log('Item %s' % index)
        #try to get serializer with the per-attribute map
        if index in self.index_to_cast:
            cast = self.index_to_cast.get(index)
            cast = cast.copy({}, self)
        elif self.element_cast:
            return self.element_cast
        #otherwise try to build it by getting attribute's class
        else:
            if index in self.index_to_mm:
                mm = self.index_to_mm[index]
            else:
                mm = self.get_item_mm(index, value)
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


class FromDict(ContainerCast):
    
    def iter_input(self, inpt):
        return inpt.iteritems()

    def get_item_from(self, index):
        return self.mm.to.feature if isinstance(self.mm.from_, Spz) else None


class ToDict(ContainerCast):
    
    def build_output(self, items_iter):
        return dict(items_iter)

    def get_item_to(self, index):
        return self.mm.to.feature if isinstance(self.mm.to, Spz) else None


class FromList(ContainerCast):
    
    def iter_input(self, inpt):
        return enumerate(inpt) 

    def get_item_from(self, index):
        return self.mm.to.feature if isinstance(self.mm.from_, Spz) else None


class ToList(ContainerCast):
    
    def build_output(self, items_iter):
        return [value for index, value in items_iter]

    def get_item_to(self, index):
        return self.mm.to.feature if isinstance(self.mm.to, Spz) else None


class FromObject(ContainerCast):
    
    defaults = CastSettings(
        class_to_getter = {object: getattr,},
        attrname_to_getter = {},
        include = None,
        exclude = None,
    )

    def get_item_from(self, index):
        return None

    @abc.abstractmethod
    def attr_names(self):
        """
        Returns:
            list. The list of attribute names included by default.
    
        .. warning:: This method will only be called if :attr:`include` is empty.

        .. note:: Override this method if you want to build dynamically the list of attributes to include by default.
        """
        return

    def calculate_include(self):
        """
        Returns:
            set. The set of attributes to include for the current operation. Take into account *include* or :meth:`attr_names` and *exclude*.
        """
        include = self.include if self.include != None else self.attr_names()
        exclude = self.exclude if self.exclude != None else []
        return set(include) - set(exclude)

    def iter_input(self, inpt):
        for name in self.calculate_include():
            yield name, self.get_getter(name)(inpt, name)

    def get_getter(self, name):
        # try to get accessor on a per-attribute basis
        if name in self.attrname_to_getter:
            return self.attrname_to_getter[name]
        # otherwise try to get it on a per-class basis
        else:
            attr_class = self.get_item_from(name) or object
            parent = closest_parent(attr_class, self.class_to_getter.keys())
            return self.class_to_getter[parent]


class ToObject(ContainerCast):
    
    defaults = CastSettings(
        class_to_setter = {object: setattr,},
        attrname_to_setter = {}
    )

    def get_item_to(self, index):
        return None

    @abc.abstractmethod
    def new_object(self, items):
        return

    def build_output(self, items_iter):
        items = dict(items_iter)
        new_object = self.new_object(items)
        for name, value in items.items():
            self.get_setter(name)(new_object, name, value)
        return new_object

    def get_setter(self, name):
        # try to get accessor on a per-attribute basis
        if name in self.attrname_to_setter:
            return self.attrname_to_setter[name]
        # otherwise try to get it on a per-class basis
        else:
            attr_class = self.get_item_to(name) or object
            parent = closest_parent(attr_class, self.class_to_setter.keys())
            return self.class_to_setter[parent]

