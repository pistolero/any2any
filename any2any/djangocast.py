# -*- coding: utf-8 -*-
import copy
import datetime

from django.db import models as djmodels
from django.db.models.fields.related import ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

from any2any.containercast import CastItems, FromList, ToList, FromObject, ToDict, FromDict, ToObject, ContainerType
from any2any.base import Cast, register
from any2any.utils import Mm

ListOfDicts = ContainerType(list, value_type=dict)

class ManagerToList(FromList, CastItems, ToList):
    """
    Casts a manager to a list of casted elements.
    """

    defaults = dict(
        to = ListOfDicts
    )

    def iter_input(self, inpt):
        return enumerate(inpt.all())


class IntrospectMixin(Cast):
    """
    Mixin for introspecting a model.
    """

    defaults = dict(
        key_schema = ('id',),
    )

    def get_model(self):
        raise NotImplementedError()

    @property
    def pk_field_name(self):
        # We get pk's field name from the "super" parent (i.e. the "eldest").
        # This allows to handle MTI nicely (and transparently).
        mod_opts = self.get_model()._meta
        if mod_opts.parents:
            super_parent = filter(lambda p: issubclass(p, djmodels.Model), mod_opts.get_parent_list())[0]
            return super_parent._meta.pk.name
        else:
            return mod_opts.pk.name

    def extract_pk(self, data):
        # Extracts and returns the primary key from the dictionary *data*, or None
        key_tuple = []
        for field_name in self.key_schema:
            try:
                if field_name == 'pk':
                    value = data.get('pk') or data[self.pk_field_name]
                else:
                    value = data[field_name]
            except KeyError:
                return None
            else:
                key_tuple.append(value)
        return tuple(key_tuple)

    @property
    def fields(self):
        # Returns a dictionary {<field_name>: <field>}, with all the fields,
        # but excluding the pointers used for MTI
        if self._context and 'fields' in self._context:
            return self._context['fields']
        mod_opts = self.get_model()._meta
        ptr_fields = self.collect_ptrs(self.get_model())
        all_fields = mod_opts.fields + mod_opts.many_to_many
        fields = list(set(all_fields) - set(ptr_fields))
        fields_dict = dict(((f.name, f) for f in fields))
        # We cache the fields so that next time, no need to search them again
        if self._context:
            self._context['fields'] = fields_dict
        return fields_dict

    def collect_ptrs(self, model):
        # Recursively collects all the fields pointing to parents of *model*
        ptr_fields = []
        for parent_model, ptr_field in model._meta.parents.iteritems():
            ptr_fields.append(ptr_field)
            ptr_fields += self.collect_ptrs(parent_model)
        return ptr_fields


class ModelToDict(FromObject, CastItems, ToDict, IntrospectMixin):
    """
    This casts serializes an instance of :class:`Model` to a dictionary.
    """

    def get_model(self):
        return self.from_

    def get_to_class(self, field_name):
        model = self.get_model()
        field = self.fields.get(field_name, None)
        model_attr = getattr(model, field_name, None)
        if field:
            # If fk, we return the right model
            if isinstance(field, djmodels.ForeignKey):
                return dict
            # If m2m, we want a list of the right model
            elif isinstance(field, djmodels.ManyToManyField):
                return ListOfDicts
            # If "complex" Python object, we want a dict
            elif isinstance(field, (djmodels.DateTimeField, djmodels.DateField)):
                return dict
            # Identity on the rest
            else:
                return object
        elif model_attr:
            # If related manager
            if isinstance(model_attr, (ManyRelatedObjectsDescriptor,
            ForeignRelatedObjectsDescriptor)):
                return ListOfDicts
        else:
            pass
        return NotImplemented

    def attr_names(self):
        return self.fields.keys()


def set_related(instance, name, value):
    """
    Setter for related managers.
    """
    instance.save()# Because otherwise we cannot handle manytomany
    manager = getattr(instance, name)
    # clear() only provided if the ForeignKey can have a value of null:
    if hasattr(manager, 'clear'):
        manager.clear()
        for element in value:
            manager.add(element)
    else:
        raise TypeError("cannot update if the related ForeignKey cannot be null")


class DictToModel(FromDict, CastItems, ToObject, IntrospectMixin):
    """
    This casts deserializes a dictionary to an instance of :class:`Model`. You need to set the appropriate metamorphosis in order to specify what model to cast to :

        >>> cast = DictToModel(to=MyModel)

    :class:`DictToModel` defines the following settings :

        - create(bool). If True, and if the object doesn't exist yet in the database, or no primary key is provided, it will be created.
    """

    defaults = dict(
        class_to_setter = {ContainerType(list, value_type=djmodels.Model): set_related},
        create = True,
        _schema = {'class_to_setter': {'override': 'copy_and_update'}}
    )

    def get_model(self):
        return self.to

    def get_to_class(self, field_name):
        model = self.get_model()
        field = self.fields.get(field_name, None)
        model_attr = getattr(model, field_name, None)
        if field:
            # If fk, we return the right model
            if isinstance(field, djmodels.ForeignKey):
                #import pdb ; pdb.set_trace()
                return field.rel.to
            # If m2m, we want a list of the right model
            elif isinstance(field, djmodels.ManyToManyField):
                return ContainerType(list, value_type=field.rel.to)
            # "Complex" Python types to the right type 
            elif isinstance(field, (djmodels.DateTimeField, djmodels.DateField)):
                return {
                    djmodels.DateTimeField: datetime.datetime,
                    djmodels.DateField: datetime.date,
                }[type(field)]
            # Identity on the rest
            else:
                return object
        elif model_attr:
            # If related manager
            if isinstance(model_attr, (ManyRelatedObjectsDescriptor,
            ForeignRelatedObjectsDescriptor)):
                return ContainerType(list, value_type=model_attr.related.model)
        else:
            pass
        return NotImplemented

    def new_object(self, items):
        """
        Returns:
            django.db.models.Model. An instance of the model associated with the serializer (see :attr:`model`). Only the primary key is handled from *data*, if it is provided. It can be provided as *pk* property name, or as an explicit field name (e.g. *id*).
        """
        key_tuple = self.extract_pk(items) or ()
        key_dict = dict(zip(self.key_schema, key_tuple)) or {'pk': None}
        model = self.get_model()
        try:
            return model.objects.get(**key_dict)
        except model.DoesNotExist:
            if self.create:
                return model(**key_dict)
            else:
                raise
        except model.MultipleObjectReturned:
            raise ValueError("'%s' is not a valid natural key for '%s', because there are duplicates." %
            (self.key_schema, model))

    def call(self, inpt):
        obj = super(DictToModel, self).call(inpt)
        obj.save()
        return obj


register(ManagerToList(), Mm(from_any=djmodels.Manager, to=ListOfDicts))
register(ModelToDict(), Mm(from_any=djmodels.Model, to=dict))
register(DictToModel(), Mm(dict, to_any=djmodels.Model))
