# -*- coding: utf-8 -*-
import copy
import datetime

from django.db import models
from django.http import QueryDict
from django.db.models.fields.related import ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey, GenericRelation
from django.db.models.query import QuerySet

from any2any import (Cast, Mm, Wrap, CastItems, FromIterable, ToIterable, FromObject, ToMapping,
FromMapping, ToObject, ContainerWrap, ObjectWrap, Setting, DivideAndConquerCast, WrappedObject)
from any2any.daccasts import DeclarativeObjectWrap
from any2any.stacks.basicstack import BasicStack, IterableToIterable, Identity
from any2any.base import MmToCastSetting


# Model instrospector
#======================================
class ModelIntrospector(object):
    """
    Mixin for adding introspection capabilities to Wraps.
    """

    @property
    def fields(self):
        # Returns a set with all the fields,
        # but excluding the pointers used for MTI
        mod_opts = self.model._meta
        ptr_fields = self.collect_ptrs(self.model)
        all_fields = mod_opts.fields + mod_opts.many_to_many
        return set(all_fields) - set(ptr_fields)

    @property
    def fields_dict(self):
        # Returns a dictionary `{<field_name>, <field>}`
        return dict(((f.name, f) for f in self.fields))

    @property
    def related_dict(self):
        # Returns a dictionary {<attr_name>: <descriptor>} with all the related descriptors,
        def retrieve_desc((k, v)):
            return isinstance(v, (ManyRelatedObjectsDescriptor,
            ForeignRelatedObjectsDescriptor))
        return dict(filter(retrieve_desc, self.model.__dict__.items()))

    @property
    def pk_field_name(self):
        # We get pk's field name from the "super" parent (i.e. the "eldest").
        # This allows to handle MTI nicely (and transparently).
        all_pks = set([p._meta.pk for p in self.model._meta.get_parent_list()])
        all_pks.add(self.model._meta.pk)
        all_ptrs = set(self.collect_ptrs(self.model))
        return list(all_pks - all_ptrs)[0].name

    @property
    def pk_field(self):
        return self.fields_dict[self.pk_field_name]

    def collect_ptrs(self, model):
        # Recursively collects all the fields pointing to parents of `model`
        ptr_fields = []
        for parent_model, ptr_field in model._meta.parents.iteritems():
            ptr_fields.append(ptr_field)
            ptr_fields += self.collect_ptrs(parent_model)
        return ptr_fields


# Model Wrap
#======================================
class ModelWrap(ModelIntrospector, ObjectWrap):
    """
    Wrap for django models.

    Kwargs:
        
        create_allowed(bool). If True, and if the object doesn't exist yet in the database, or no primary key is provided, it will be created.
        key_schema(tuple). ``(<field_name>)``. Tuple of field names used to fetch the object from the database.
    """

    defaults = {
        'key_schema': ('pk',),
        'include_related': False,
        'create_allowed': True,
    }

    def default_schema(self):
        schema = {}
        schema.update(self._wrap_fields({'pk': self.pk_field}))
        schema.update(self._wrap_fields(self.fields_dict))
        schema.update(self._wrap_fields(self.related_dict))
        return schema

    def _wrap_fields(self, fields_dict):
        # Takes a dict ``{<field_name>: <fields>}``, and returns a dict
        # ``{<field_name>: <wrapped_field>}``.
        wrapped_fields = {}
        for name, field in fields_dict.items():
            field_type = type(field)
            # If fk, we return the right model
            if isinstance(field, models.ForeignKey):
                wrapped_type = ModelWrap(
                    klass=field.rel.to,
                    superclasses=(field_type,)
                )
            # If m2m, we want a list of the right model
            elif isinstance(field, (models.ManyToManyField, GenericRelation)):
                wrapped_type = ContainerWrap(
                    klass=field_type,
                    superclasses=(models.Manager,),
                    factory=list,
                    value_type=field.rel.to
                )
            # related FK or related m2m, same as m2m 
            elif isinstance(field, (ManyRelatedObjectsDescriptor,
            ForeignRelatedObjectsDescriptor)):
                wrapped_type = ContainerWrap(
                    klass=field_type,
                    superclasses=(models.Manager,),
                    factory=list,
                    value_type=field.related.model
                )
            # "Complex" Python types to the right type 
            elif isinstance(field, (models.DateTimeField, models.DateField)):
                actual_type = {
                    models.DateTimeField: datetime.datetime,
                    models.DateField: datetime.date,
                }[field_type]
                wrapped_type = Wrap(klass=field_type, superclasses=(actual_type,))
            else:
                wrapped_type = field_type
            wrapped_fields[name] = wrapped_type
        return wrapped_fields

    def get_schema(self):
        schema = super(ModelWrap, self).get_schema()
        related_keys = self.related_dict.keys()
        if not self.include_related:
            for k in related_keys:
                if not k in self.include and not k in self.extra_schema:
                    schema.pop(k, None)
        return schema

    def new(self, *args, **kwargs):
        try:
            instance = self.retrieve(*args, **kwargs)
        except self.model.MultipleObjectsReturned:
            raise ValueError("'%s' is not unique for '%s'" %
            (self.key_schema, self.model))
        except self.model.DoesNotExist:
            if not self.create_allowed:
                raise
            instance = self.create(*args, **kwargs)
        return self.update(instance, *args, **kwargs)

    def retrieve(self, *args, **kwargs):
        key_dict = self.extract_key(kwargs)
        if not key_dict:
            raise self.model.DoesNotExist("no key could be extracted from the data")
        return self.model.objects.get(**key_dict)

    def create(self, *args, **kwargs):
        key_dict = self.extract_key(kwargs)
        return self.model(**(key_dict or {'pk': None}))

    def update(self, instance, *args, **kwargs):
        for name, value in kwargs.iteritems():
            klass = self.get_class(name)
            if Wrap.issubclass(klass, models.Manager):
                instance.save()# Because otherwise we cannot handle manytomany
                manager = getattr(instance, name)
                # clear() only provided if the ForeignKey can have a value of null:
                if hasattr(manager, 'clear'):
                    manager.clear()
                    for element in value:
                        manager.add(element)
                else:
                    raise TypeError("cannot update if the related ForeignKey cannot be null")
            else:
                setattr(instance, name, value)
        return instance

    @property
    def model(self):
        return self.factory or self.klass

    def extract_key(self, data):
        # Extracts and returns the object key from the dictionary `data`, or None
        key_dict = {}
        for field_name in self.key_schema:
            try:
                if field_name == 'pk':
                    value = data.get('pk') or data[self.pk_field_name]
                else:
                    value = data[field_name]
            except KeyError:
                return None
            else:
                key_dict[field_name] = value
        return key_dict


class DeclarativeModelWrap(ModelWrap, DeclarativeObjectWrap): pass
class WrappedModel(WrappedObject):

    __metaclass__ = DeclarativeModelWrap

    klass = models.Model


# Mixins
#======================================
class FromModel(FromObject):

    from_wrap = Setting(default=ModelWrap)


class ToModel(ToObject):

    to_wrap = Setting(default=ModelWrap)

    def call(self, inpt):
        instance = super(ToModel, self).call(inpt)
        instance.save() # TODO: why save ?
        return instance


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

    empty_value = Setting(default='_empty')
    
    class Meta:
        defaults = {
            'to': list,
        }
    
    def strip_item(self, key, value):
        if value == self.empty_value:
            return True


class FromQueryDict(FromMapping):
    
    def iter_input(self, qd):
        return qd.iterlists()


class QueryDictWrap(Wrap, ModelIntrospector):

    defaults = {
        'list_keys': [],
        'klass': dict,
        'model': None,
    }

    def get_class(self, key):
        if (key in self.list_keys) or self.is_list(key):
            return list
        else:
            return NotImplemented

    def is_list(self, key):
        if self.model:
            try:
                field = filter(lambda f: f.name == key, self.fields)[0]
            except IndexError:
                pass
            else:
                field_type = type(field)
                if isinstance(field, models.ManyToManyField): # TODO: not only m2m
                    return True
        return False


class LockedMmToCastSetting(MmToCastSetting):

    def customize(self, instance, value):
        pass


class QueryDictFlatener(FromQueryDict, CastItems, ToMapping, DivideAndConquerCast):
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

    to_wrap = Setting(default=QueryDictWrap)
    mm_to_cast = LockedMmToCastSetting(default={
        Mm(from_=list): ListToFirstElem(),
        Mm(to=list): OneElemToList(),
        Mm(list, list): Identity(),
        Mm(): Identity(),
    })

    def get_item_to(self, key):
        return self.to.get_class(key)


# Building stack for Django
#======================================
class ModelToMapping(FromModel, ToMapping, CastItems, DivideAndConquerCast): pass
class MappingToModel(ToModel, FromMapping, CastItems, DivideAndConquerCast): pass
class QuerySetToIterable(FromQuerySet, CastItems, ToIterable, DivideAndConquerCast): pass
class IterableToQueryset(FromIterable, CastItems, ToIterable, DivideAndConquerCast): pass


class DjangoSerializeStack(BasicStack):
    """
    Subclass of :class:`base.CastStack`, for serializing Django objects
    """

    class Meta:
        defaults = {
            'mm_to_cast': {
                Mm(from_any=models.Manager): QuerySetToIterable(to=list),
                Mm(from_any=QuerySet): QuerySetToIterable(to=list),
                Mm(from_any=models.Model): ModelToMapping(to=dict),
                Mm(from_any=QueryDict): QueryDictFlatener(),
            }
        }


class DjangoDeserializeStack(BasicStack):
    """
    Subclass of :class:`base.CastStack`, for deserializing Django objects
    """

    class Meta:
        defaults = {
            'mm_to_cast': {
                Mm(to_any=models.Manager): IterableToQueryset(),
                Mm(to_any=QuerySet): IterableToQueryset(),
                Mm(from_any=dict, to_any=models.Model): MappingToModel(),
            }
        }
