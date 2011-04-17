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

from django.db import models as django_models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

from any2any.simple import GuessMmMixin, FromListMixin, ToListMixin, ContainerCast, FromObjectMixin, ToDictMixin, FromDictMixin, ToObjectMixin
from any2any.base import CastSettings, Mm, Spz, register


class ManagerToList(GuessMmMixin, FromListMixin, ToListMixin, ContainerCast):

    defaults = CastSettings(
        mm = Mm(list, Spz(list, dict))
    )

    def iter_input(self, inpt):
        return enumerate(inpt.all())


class IntrospectMixin(object):

    @property
    def model(self):
        raise NotImplementedError()

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
                    return None
        return tuple(obj_key)

    def fields(self, model):
        # TODO: caching
        mod_opts = model._meta
    
        #MTI : We exclude the fields (OneToOne) pointing to the parents.
        exclude_ptr = []
        parents = mod_opts.parents
        while parents:
            oto_field = parents.values()[0]
            exclude_ptr.append(oto_field.name)
            parents = oto_field.related.parent_model._meta.parents

        all_fields = mod_opts.fields + mod_opts.many_to_many
        included_fields = filter(lambda field: field.name not in exclude_ptr, all_fields)
        return dict(zip([f.name for f in included_fields], included_fields))


class ModelToDict(GuessMmMixin, FromObjectMixin, ToDictMixin, IntrospectMixin, ContainerCast):

    defaults = CastSettings(
        mm = Mm(django_models.Model, dict),
        key_schema = ('id',),
    )

    @property
    def model(self):
        return type(self._context['input'])

    def get_to(self, field_name):
        try:
            # Managers to list, and Models to dict
            return {
                django_models.ForeignKey: dict,
                django_models.ManyToManyField: Spz(list, dict),
            }[type(self.fields(self.model)[field_name])]
        except KeyError:
            # Identity on the rest
            return object

    def attr_names(self):
        return self.fields(self.model).keys()


def set_m2m_attr(self, instance, name, value):
    instance.save()# Because otherwise we cannot handle manytomany
    manager = getattr(instance, name)
    manager.clear()
    for element in value:
        manager.add(element)


class DictToModel(GuessMmMixin, FromDictMixin, ToObjectMixin, IntrospectMixin, ContainerCast):

    defaults = CastSettings(
        mm = Mm(dict, django_models.Model),
        key_schema = ('id',),
        class_to_setter = {Spz(list, django_models.Model): set_m2m_attr},
        _schema = {'class_to_setter': {'override': 'update_item'}}
    )

    @property
    def model(self):
        return self.mm.to

    def get_to(self, field_name):
        field = self.fields(self.model)[field_name]
        # If fk, we return the right model
        if isinstance(field, django_models.ForeignKey):
            return field.rel.to
        # If m2m, we want a list of the right model
        elif isinstance(field, django_models.ManyToManyField):
            return Spz(list, field.rel.to)
        # Identity on the rest
        else:
            return object
            
    def new_object(self, items):
        """
        Returns:
            django.db.models.Model. An instance of the model associated with the serializer (see :attr:`model`). Only the primary key is handled from *data*, if it is provided. It can be provided as *pk* property name, or as an explicit field name (e.g. *id*).
        """
        key_tuple = self.get_obj_key(items)
        key_dict = dict(zip(self.key_schema, key_tuple)) if key_tuple else {'pk': None}
        try:
            return self.model.objects.get(**key_dict)
        except self.model.DoesNotExist:
            if key_dict:
                new_object = self.model(**key_dict)
            else:
                new_object = self.model()
            new_object.save()
            return new_object
        except self.model.MultipleObjectReturned:
            raise ValueError("'%s' is not a valid natural key for '%s', because there are duplicates." %
            (self.key_schema, self.model))

'''
class ModelSrz(BaseModelSrz):


ModelSrz.defaults.get('class_srz_map')[django_models.Model] = ModelSrz()

class NCModelSrz(BaseModelSrz):

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
'''
'''
ModelToDict.defaults['mm_to_cast'] = {
    (GenericForeignKey, object): GenericForeignKeySrz(),
},


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


     
'''
register(ManagerToList(), [Mm(django_models.Manager, Spz(list, dict))])
register(ModelToDict(), [Mm(django_models.Model, dict)])
register(DictToModel(), [Mm(dict, to_any=django_models.Model)])
