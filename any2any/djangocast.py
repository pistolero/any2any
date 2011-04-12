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
import copy

import logging
from spiteat.base import logger
logger.setLevel(logging.DEBUG)

from django.db import models as django_models
from django.db.models import Manager
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

from spiteat.objectsrz import ObjectSrz, Accessor
from spiteat.base import Srz
from spiteat.simple import SequenceSrz
from spiteat.utils import specialize

class NCManyToManyAccessor(Accessor):
    def set_attr(self, instance, name, value):
        manager = getattr(instance, name)
        manager.clear()
        for element in value:
            manager.add(element)

    def get_attr(self, instance, name):
        return list(getattr(instance, name).all())

class ManyToManyAccessor(NCManyToManyAccessor):
    def set_attr(self, instance, name, value):
        instance.save()#because otherwise we cannot handle manytomany
        super(ManyToManyAccessor, self).set_attr(instance, name, value)

class GenericForeignKeySrz(Srz):
    def spit(self, obj):
        mod_opts = obj._meta
        return (mod_opts.app_label, mod_opts.module_name, obj.pk)

    def eat(self, data, instance=None):
        ct = ContentType.objects.get(app_label=data[0], model=data[1])
        return ct.get_object_for_this_type(pk=data[2])


class BaseModelCast(ToDict, ObjectCast):

    defaults = settings(
        mm = Mm(django_models.Model, dict),
        mm_to_cast = {
            Manager: SequenceCast(),
            GenericForeignKey: GenericForeignKeySrz(),
        },
        key_schema = ('pk',),

    def iter_input(self, inpt):
        for name in self.calculate_include():
            yield name, getattr(inpt, name)

    def cast_for_item(self, name):
        self.cast_for()

    def iter_output(self, items):
        for name, value in items:
            cast = self.cast_for_item(name)
            yield name, cast(value)

    def attr_names(self):
        mod_opts = self._context['input']._meta
        include = [field.name for field in mod_opts.fields] + ['pk'] + [field.name for field in mod_opts.many_to_many]
    
        #MTI : We exclude the fields (OneToOne) pointing to the parents.
        exclude_ptr = []
        parents = mod_opts.parents
        while parents:
            otofield = parents.values()[0]
            exclude_ptr.append(otofield.name)
            parents = otofield.related.parent_model._meta.parents
        return list(set(include) - set(exclude_ptr))

    @property
    def pk_field_name(self):
        #We get pk's field name from the "super" parent (i.e. the "eldest")
        mod_opts = self.custom_for._meta
        if mod_opts.parents:
            super_parent = filter(lambda p: issubclass(p, django_models.Model), mod_opts.get_parent_list())[0]
            return super_parent._meta.pk.name
        else:
            return mod_opts.pk.name

    def get_obj_key(self, data):
        """
        """
        obj_key = []
        for field_name in self.key_schema:
            if field_name == 'pk':
                pk = data.get('pk') or data.get(self.pk_field_name)
                if not pk:
                    break
                else:
                    obj_key.append(pk)
            else:
                try:
                    obj_key.append(data[field_name])
                except KeyError:
                    break
        else:
            return tuple(obj_key)
        return None
    
    def default_attr_schema(self, name):
        mod_opts = self.custom_for._meta
        #the attribute is a field
        if name in [field.name for field in mod_opts.fields]:
            field = mod_opts.get_field(name) 
            if type(field) == django_models.ForeignKey:
                return field.rel.to, {'custom_for': field.rel.to}
            return type(field), {'custom_for': object}#because that's annoying to map fields with types accepted
        #important to put manytomany after normal fields, because manytomany requires to save the instance
        elif name in [field.name for field in mod_opts.many_to_many]:
            field = mod_opts.get_field(name)
            return Manager, {'custom_for': specialize(list, field.related.parent_model)}
        else:
            #Handles GenericForeignKeys
            class_attr = getattr(self.custom_for, name, None)
            if class_attr and type(class_attr) == GenericForeignKey:
                return GenericForeignKey, {'custom_for': django_models.Model}
            return object, {}

    def eat(self, data, instance=None):
        obj = super(BaseModelSrz, self).eat(data, instance)
        obj.save() #because otherwise we cannot handle the foreign keys
        return obj


class ModelSrz(BaseModelSrz):

    class Settings:

        class_accessor_map = {
            Manager: ManyToManyAccessor(),
        }

    def new_object(self, data=None):
        """
        Returns:
            django.db.models.Model. An instance of the model associated with the serializer (see :attr:`model`). Only the primary key is handled from *data*, if it is provided. It can be provided as *pk* property name, or as an explicit field name (e.g. *id*).
        """
        key_tuple = self.get_obj_key(data)
        key_dict = dict(zip(self.key_schema, key_tuple)) if key_tuple else {'pk': None}
        try:
            return self.custom_for.objects.get(**key_dict)
        except self.custom_for.DoesNotExist:
            if key_dict:
                new_object = self.custom_for(**key_dict)
            else:
                new_object = self.custom_for()
            return new_object
        except self.custom_for.MultipleObjectReturned:
            raise
        else:
            raise ValueError("Object with key '%s' already exist" % key_dict)
ModelSrz.defaults.get('class_srz_map')[django_models.Model] = ModelSrz()

class NCModelSrz(BaseModelSrz):

    class Settings:

        class_accessor_map = {
            Manager: NCManyToManyAccessor(),
        }

    def new_object(self, data=None):
        """
        Returns:
            django.db.models.Model. An instance of the model associated with the serializer (see :attr:`model`). Only the primary key is handled from *data*, if it is provided. It can be provided as *pk* property name, or as an explicit field name (e.g. *id*).
        """
        key_tuple = self.get_obj_key(data)
        key_dict = dict(zip(self.key_schema, key_tuple)) if key_tuple else {'pk': None}
        try:
            return self.custom_for.objects.get(**key_dict)
        except self.custom_for.DoesNotExist:
            raise
        except self.custom_for.MultipleObjectReturned:
            raise
NCModelSrz.defaults.get('class_srz_map')[django_models.Model] = NCModelSrz()        

