# -*- coding: utf-8 -*-
import copy
import datetime

from django.db import models as djmodels
from django.db.models.fields.related import ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

from any2any import (Cast, Mm, Wrap, CastItems, FromIterable, ToIterable, FromObject, ToMapping,
FromMapping, ToObject, ContainerWrap, ObjectWrap)
from any2any.stacks.basicstack import BasicStack, IterableToIterable, Identity

# Model Wrap
#======================================
class DjModelWrap(ObjectWrap):
    """
        - create(bool). If True, and if the object doesn't exist yet in the database, or no primary key is provided, it will be created.
    """

    defaults = dict(
        key_schema = ('id',),
        extra_schema = {},
        exclude = [],
        include = [],
        create = True,
        factory = None,
    )

    def default_schema(self):
        # Returns a dictionary {<field_name>: <field>}, with all the fields,
        # but excluding the pointers used for MTI
        mod_opts = self.base._meta
        ptr_fields = self.collect_ptrs(self.base)
        all_fields = mod_opts.fields + mod_opts.many_to_many
        fields = list(set(all_fields) - set(ptr_fields))
        fields_dict = {}
        for field in fields:
            field_type = type(field)
            # If fk, we return the right model
            if isinstance(field, djmodels.ForeignKey):
                wrapped_type = DjModelWrap(
                    field.rel.to, field_type
                )
            # If m2m, we want a list of the right model
            elif isinstance(field, djmodels.ManyToManyField):
                wrapped_type = ContainerWrap(
                    field_type, djmodels.Manager, factory=list,
                    value_type=DjModelWrap(field.rel.to)
                )
            # "Complex" Python types to the right type 
            elif isinstance(field, (djmodels.DateTimeField, djmodels.DateField)):
                #TODO: doesn't work
                actual_type = {
                    djmodels.DateTimeField: datetime.datetime,
                    djmodels.DateField: datetime.date,
                }[field_type]
                wrapped_type = Wrap(field_type, actual_type)
            # NotImplemented on the rest
            else:
                wrapped_type = Wrap(field_type)
            fields_dict[field.name] = wrapped_type
        return fields_dict

    def guess_class(self, key):
        model_attr = getattr(self.base, key, None)
        if model_attr:
            # If related manager
            if isinstance(model_attr, (ManyRelatedObjectsDescriptor,
            ForeignRelatedObjectsDescriptor)):
                return ContainerWrap(
                    type(model_attr), djmodels.Manager, factory=list,
                    value_type=model_attr.related.model
                )
        return NotImplemented

    def new_object(self, *args, **kwargs):
        model = self.factory
        key_tuple = self.extract_pk(kwargs) or ()
        key_dict = dict(zip(self.key_schema, key_tuple))
        if not key_dict:
            if self.create:
                key_dict = {'pk': None}
            else:
                raise ValueError("Input doesn't contain key for getting object")
        try:
            return model.objects.get(**key_dict), key_dict.keys()
        except model.DoesNotExist:
            if self.create:
                return model(**key_dict), key_dict.keys()
            else:
                raise
        except model.MultipleObjectsReturned:
            raise ValueError("'%s' is not unique for '%s'" %
            (self.key_schema, model))

    @property
    def pk_field_name(self):
        # We get pk's field name from the "super" parent (i.e. the "eldest").
        # This allows to handle MTI nicely (and transparently).
        mod_opts = self.base._meta
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

    def collect_ptrs(self, model):
        # Recursively collects all the fields pointing to parents of *model*
        ptr_fields = []
        for parent_model, ptr_field in model._meta.parents.iteritems():
            ptr_fields.append(ptr_field)
            ptr_fields += self.collect_ptrs(parent_model)
        return ptr_fields

# Mixins
#======================================
class FromModel(FromObject):

    defaults = dict(
        from_wrap = DjModelWrap
    )

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

class ToModel(ToObject):
    """
    This casts deserializes a dictionary to an instance of :class:`Model`. You need to set the appropriate metamorphosis in order to specify what model to cast to.
    """

    defaults = dict(
        class_to_setter = {ContainerWrap(djmodels.Manager, value_type=djmodels.Model): set_related},
        to_wrap = DjModelWrap,
        _meta = {'class_to_setter': {'override': 'copy_and_update'}}
    )

    def call(self, inpt):
        obj = super(ToModel, self).call(inpt)
        obj.save()
        return obj

class FromQuerySet(FromIterable):

    def iter_input(self, inpt):
        return enumerate(inpt.all())

# Casts for QueryDict
#======================================
class ListToFirstElem(Cast):

    def call(self, inpt):
        try:
            return inpt[0]
        except IndexError:
            return self.no_elem_error()

    def no_elem_error(self):
        pass

class OneElemToList(Cast):

    def call(self, inpt):
        return [inpt]

class StripEmptyValues(IterableToIterable):

    defaults = dict(
        empty_value = '_empty',
        to = list
    )
    
    def strip_item(self, key, value):
        if value == self.empty_value:
            return True

class FromQueryDict(FromMapping):
    
    def iter_input(self, qd):
        return qd.iterlists()

class QueryDictFlatener(FromQueryDict, CastItems, ToMapping):
    """
    Cast for flatening a querydict.

        >>> cast = QueryDictFlatener(list_keys=['a_list', 'another_list'])
        >>> cast({'a_list': [1, 2], 'a_normal_key': [1, 2, 3], 'another_list': []}) == {
        ...     'a_list': [1, 2],
        ...     'a_normal_key': 1,
        ...     'another_list': []
        ... }
        True
    """

    defaults = dict(
        to = dict,
        mm_to_cast = {
            Mm(from_=list): ListToFirstElem(),
            Mm(to=list): OneElemToList(),
            Mm(list, list): Identity(),
        },
        list_keys = [],
    )

    def get_item_to(self, key):
        if (key in self.list_keys) or self.value_is_list(key):
            return list
        else:
            return object

    def value_is_list(self, key):
        return False

# Building stack for Django
#======================================
class ModelToMapping(FromModel, ToMapping, CastItems): pass
class MappingToModel(ToModel, FromMapping, CastItems): pass
class QuerySetToIterable(FromQuerySet, CastItems, ToIterable): pass
class IterableToQueryset(FromIterable, CastItems, ToIterable): pass

class DjangoStack(BasicStack):

    defaults = dict(
        mm_to_cast = {
            Mm(from_any=djmodels.Manager): QuerySetToIterable(to=list),
            Mm(from_any=list, to_any=djmodels.Manager): IterableToQueryset(),
            Mm(from_any=djmodels.Model): ModelToMapping(to=dict),
            Mm(to_any=djmodels.Model): MappingToModel(),
        }
    )
