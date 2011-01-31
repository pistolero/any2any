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
.. todo:: describe (de)serialization process for objects.
.. todo:: guide for overriding ObjectCast
.. todo:: better testing for _default_include/include/exclude
.. todo:: better names
"""
from base import *
from utils import closest_parent

class Accessor(object):
    """
    Accessors allow to customize the way attributes are get/set for an object. 
    """

    def get_attr(self, instance, name):
        """
        This methods specification is exactly the same as :func:`getattr`.
        """
        return getattr(instance, name)
        
    def set_attr(self, instance, name, value):
        """
        This methods specification is exactly the same as :func:`setattr`.
        """
        return setattr(instance, name, value)
        

class ObjectCast(Cast):
    """
    Base cast class for complex objects. This class is virtual and provides facilities for decomposing a cast from (or to) an object, in the cast of its attributes.
    """

    class Settings:
        """
        Settings available for instances of :class:`ObjectCast` :
        """
        _schema = {
            'class_accessor_map': {
                'inheritance': 'update',
            }
        }

        include = []
        """
        list. Example :
            
            >>> cast = SomeObjectCast(include=['a', 'b']) #Attributes 'a' and 'b' are handled by the cast operation.
        """

        exclude = []
        """
        list. Names of attributes to exclude from the cast.
        """

        attr_conversion_map = {}
        """
        dict. Maps attribute name to the conversion to apply to them.
        """

        attr_cast_map = {}
        """dict. Maps attribute name to a cast."""

        class_accessor_map = {object: Accessor()}
        """dict. Define which accessor is used for all attributes of a given class."""

        attr_accessor_map = {}
        """dict. Define which accessor is used for a given attribute name."""

    #------------------------- methods to override -------------------------#
    def default_include(self, obj):
        """
        Returns:
            list. The list of attribute names included by default.
    
        .. warning:: This method will only be called if :attr:`include` is empty.

        .. note:: Override this method if you want to build dynamically the list of attributes to include by default.
        """
        return []

    def default_attr_conversion(self, obj, name):
        """
        Returns:
            (type, type). The conversion to realize on the attribute *name*. 

        .. warning:: This method will only be called if the conversion is not specified by :attr:`attr_conversion_map`.

        .. note:: Override this method to specify what is the conversion to realize on each attribute. This helps the calling cast to select an appropriate cast for each attribute.
        """
        return (object, object)

    #------------------------------ BASE ------------------------------#
    def get_attr_class(self, name, obj):
        raise NotImplementedError('This class is virtual')

    def get_attr_conversion(self, name, obj):
        """
        Returns:
            type. Attribute *name*'s conversion.
        """
        if name in self.attr_conversion_map:
            return self.attr_conversion_map.get(name)
        else:
            return self.default_attr_conversion(name, obj)

    def cast_for_attr(self, name, obj):
        """
        Returns:
            Cast. The type conversion to use for attribute *name*. It is built from :attr:`attr_cast_map` if defined, otherwise we try to build it according to the conversion defined for this attribute.
        """
        self.log('Attribute ' + name)
        #try to get cast with the per-attribute map
        if name in self.attr_cast_map:
            cast = self.attr_cast_map.get(name)
            return cast.copy({}, self)
        #otherwise try to build it by getting attribute's class
        else:
            conversion = self.get_attr_conversion(name, obj)
            return self.cast_for(conversion, {})

    def calculate_include(self, obj):
        """
        Returns:
            set. Calculates the set of attributes to take into account for the cast, considering :attr:`include`, :attr:`exclude` and :meth:`default_include`.
        """
        include = getattr(self, 'include') or self.default_include(obj)
        exclude = getattr(self, 'exclude')
        return set(include) - set(exclude)

    def get_attr_accessor(self, name, obj):
        """
        Returns:
            Accessor. The accessor to use for attribute *name*.
        """
        #try to get accessor on a per-attribute basis
        if self.attr_accessor_map and name in self.attr_accessor_map:
            return self.attr_accessor_map[name]

        #otherwise try to get it on a per-class basis
        else:
            attr_class = self.get_attr_class(name, obj)
            choice = closest_parent(attr_class, self.class_accessor_map.keys())
            return self.class_accessor_map[choice]

class ObjectToDict(ObjectCast):

    class Settings:
        conversion = (object, dict)

    def default_include(self, obj):
        return filter(lambda n: n[0] != '_', list(obj.__dict__))

    def default_attr_conversion(self, name, obj):
        return (type(getattr(obj, name)), object)

    def get_attr_class(self, name, obj):
        return self.get_attr_conversion(name, obj)[FROM]

    def __call__(self, obj):
        """
        Returns:
            dict. **{<attribute_name>: <converted_value>}**
        """
        dct = {}
        for attr_name in self.calculate_include(obj):
            accessor = self.get_attr_accessor(attr_name, obj)
            cast = self.cast_for_attr(attr_name, obj)
            attr_value = accessor.get_attr(obj, attr_name)
            try:
                dct[attr_name] = cast(attr_value)
            except ValidationError as e:
                pass
        return dct

class DictToObject(ObjectCast):


    class Settings:
        conversion = (dict, object)

    def new_object(self, converted_data=None):
        """
        Returns:
            object. A new object. *converted_data* can be used to create it.
        
        Args:
            converted_data(dict). **{<attribute_name>: <converted_value>}**.

        .. note:: Override this method to customize creation of new objects.
        """
        return self.conversion[TO]()

    def default_include(self, dct):
        return dct.keys()

    def default_attr_conversion(self, name, dct):
        return (type(dct[name]), object)

    def get_attr_class(self, name, dct):
        return self.get_attr_conversion(name, dct)[TO]

    def __call__(self, dct):
        """
        Args:
            data(dict). **{<attribute_name>: <raw_value>}**

        Returns:
            object.
        """
        converted_attrs = {}
        include = self.calculate_include(dct)
        for attr_name in (set(dct) & include):
            cast = self.cast_for_attr(attr_name, dct)
            converted_attrs[attr_name] = cast(dct[attr_name])
        obj = self.new_object(converted_attrs)
        for attr_name in (set(converted_attrs) & include):
            accessor = self.get_attr_accessor(attr_name, dct)
            accessor.set_attr(obj, attr_name, converted_attrs[attr_name])
        return obj
