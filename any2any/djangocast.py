# -*- coding: utf-8 -*-
import copy

from django.db import models as django_models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

from any2any.simple import FromList, ToList, ContainerCast, FromObject, ToDict, FromDict, ToObject
from any2any.base import Cast, CastSettings, Mm, Spz, register


class ManagerToList(FromList, ToList, ContainerCast):
    """
    Casts a manager to a list of casted elements.
    """

    defaults = CastSettings(
        mm = Mm(list, Spz(list, dict))
    )

    def iter_input(self, inpt):
        return enumerate(inpt.all())


class IntrospectMixin(Cast):
    """
    Mixin for introspecting a model.
    """

    defaults = CastSettings(
        key_schema = ('id',),
    )

    @property
    def model(self):
        raise NotImplementedError()

    @property
    def pk_field_name(self):
        # We get pk's field name from the "super" parent (i.e. the "eldest").
        # This allows to handle MTI nicely (and transparently).
        mod_opts = self.model._meta
        if mod_opts.parents:
            super_parent = filter(lambda p: issubclass(p, django_models.Model), mod_opts.get_parent_list())[0]
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
        mod_opts = self.model._meta
        ptr_fields = self.collect_ptrs(self.model)
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

class ModelToDict(FromObject, ToDict, IntrospectMixin, ContainerCast):
    """
    This casts serializes an instance of :class:`Model` to a dictionary.
    """

    @property
    def model(self):
        return type(self._context['input'])

    def get_to_class(self, field_name):
        field = self.fields.get(field_name, None)
        # Managers to list
        if isinstance(field, django_models.ForeignKey):
            return dict
        # Models to dict
        if isinstance(field, django_models.ManyToManyField):
            return Spz(list, dict)
        # Identity on the rest
        else:
            return object

    def attr_names(self):
        return self.fields.keys()


def set_m2m_field(instance, name, value):
    """
    Setter for many-to-many fields.
    """
    instance.save()# Because otherwise we cannot handle manytomany
    manager = getattr(instance, name)
    manager.clear()
    for element in value:
        manager.add(element)


class DictToModel(FromDict, ToObject, IntrospectMixin, ContainerCast):
    """
    This casts deserializes a dictionary to an instance of :class:`Model`. You need to set the appropriate metamorphosis in order to specify what model to cast to :

        >>> cast = DictToModel(mm=Mm(dict, MyModel))

    :class:`DictToModel` defines the following settings :

        - create(bool). If True, and if the object doesn't exist yet in the database, or no primary key is provided, it will be created.
    """

    defaults = CastSettings(
        class_to_setter = {Spz(list, django_models.Model): set_m2m_field},
        create=True,
        _schema = {'class_to_setter': {'override': 'update_item'}}
    )

    @property
    def model(self):
        return self.mm.to

    def get_to_class(self, field_name):
        field = self.fields.get(field_name, None)
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
        key_tuple = self.extract_pk(items) or ()
        key_dict = dict(zip(self.key_schema, key_tuple)) or {'pk': None}
        try:
            return self.model.objects.get(**key_dict)
        except self.model.DoesNotExist:
            if self.create:
                return self.model(**key_dict)
            else:
                raise
        except self.model.MultipleObjectReturned:
            raise ValueError("'%s' is not a valid natural key for '%s', because there are duplicates." %
            (self.key_schema, self.model))

    def call(self, inpt):
        obj = ContainerCast.call(self, inpt)
        obj.save()
        return obj

register(ManagerToList(), Mm(from_any=django_models.Manager, to=Spz(list, dict)))
register(ModelToDict(), Mm(from_any=django_models.Model, to=dict))
register(DictToModel(), Mm(dict, to_any=django_models.Model))
