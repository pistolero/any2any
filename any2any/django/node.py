# -*- coding: utf-8 -*-
import copy
import datetime
import types

from django.db import models
from django.http import QueryDict
from django.db.models.fields.related import ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey, GenericRelation
from django.db.models.query import QuerySet
from django.core.files.base import ContentFile
from django.core.files import File

QUERYSET_FIELDS = (ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor,
    models.ManyToManyField, GenericRelation)
RELATED_FIELDS = (ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor)
SIMPLE_FIELDS = (models.CharField, models.TextField, models.IntegerField, models.DateTimeField,
    models.DateField, models.AutoField, models.FileField, models.BooleanField)

from any2any import *
from any2any.node import NodeInfo
from any2any.utils import classproperty, SmartDict, ClassSet, ClassSetDict
from any2any.stdlib.node import DateTimeNode, DateNode
from any2any.django.utils import ModelIntrospector


class QuerySetNode(IterableNode):

    klass = QuerySet
    value_type = models.Model

    def dump(self):
        if hasattr(self.obj, 'all'):
            return enumerate(self.obj.all())
        else:
            return enumerate(self.obj)

    @classmethod
    def load(cls, items_iter):
        obj = list((v for k, v in items_iter))
        return cls(obj)
        

def wrap_simple_field(f):
    if isinstance(f, models.AutoField):
        klass = int
    elif isinstance(f, (models.TextField, models.CharField)):
        klass = unicode
    elif isinstance(f, models.IntegerField):
        klass = int
    elif isinstance(f, models.DateTimeField):
        klass = datetime.datetime
    elif isinstance(f, models.DateField):
        klass = datetime.date
    elif isinstance(f, models.FileField):
        klass = File
    elif isinstance(f, models.BooleanField):
        klass = bool
    return NodeInfo([type(f), klass, types.NoneType, klass])


def wrap_foreign_key(f):
    # TODO: not great, because then we can have a node that doesn't know
    # what kind of FK it represents
    return NodeInfo([type(f), f.rel.to, types.NoneType, f.rel.to])


def wrap_queryset_field(f):
    if isinstance(f, RELATED_FIELDS):
        to = f.related.model
    else:
        to = f.rel.to
    return NodeInfo([type(f), QuerySet], value_type=to)


class ModelMixin(ModelIntrospector):

    key_schema = ('pk',)
    """tuple. ``(<field_name>)``. Tuple of field names used to fetch the object from the database."""

    include_related = False
    """bool. If True, the schema will also include related ForeignKeys and related ManyToMany."""

    # This is a trick to allow dynamically branching custom wrapping
    # for non-standard field types like geodjango fields or mongoDB fields.  
    _field_wrapping_functions = ClassSetDict({
        ClassSet(*SIMPLE_FIELDS): wrap_simple_field,
        AllSubSetsOf(models.ForeignKey): wrap_foreign_key,
        ClassSet(*QUERYSET_FIELDS): wrap_queryset_field,
    })

    @classmethod
    def load(cls, items_iter):
        raise NotImplementedError

    @classmethod
    def common_schema(cls):
        if not hasattr(cls, '_common_schema'):
            schema = {}
            # collecting all the fields
            schema['pk'] = cls._wrap(cls.pk_field)
            for name, field in cls.fields_dict.items():                
                schema[name] = cls._wrap(field)
            for name, field in cls.related_dict.items():                
                schema[name] = cls._wrap(field)
            related_keys = cls.related_dict.keys()
            # removing related if specified
            if not cls.include_related:
                for k in related_keys:
                    schema.pop(k, None)
            cls._common_schema = schema
        return cls._common_schema

    @classproperty
    def model(cls):
        return cls.klass

    @classproperty
    def queryset(cls):
        return cls.model.objects

    @classmethod
    def schema_load(cls):
        return cls.common_schema()

    @classmethod
    def schema_dump(cls):
        return cls.common_schema()

    @classmethod
    def extract_key(cls, data):
        # Extracts and returns the object key from the dictionary `data`, or None
        key_dict = {}
        for field_name in cls.key_schema:
            try:
                if field_name == 'pk':
                    value = data.get('pk') or data[cls.pk_field_name]
                else:
                    value = data[field_name]
            except KeyError:
                return None
            else:
                key_dict[field_name] = value
        return key_dict

    @classmethod
    def create(cls, **items):
        key_dict = cls.extract_key(items)
        return cls(cls.model(**(key_dict or {'pk': None})))

    @classmethod
    def retrieve(cls, **items):
        key_dict = cls.extract_key(items)
        if not key_dict:
            raise cls.model.DoesNotExist("no key could be extracted from the data")
        return cls(cls.queryset.get(**key_dict))

    def update(self, **items):
        deferred = {}
        for name, value in items.items():
            if self._is_qs(name):
                deferred[name] = value
            else:
                self.setattr(name, value)
        self.obj.save()# Because otherwise we cannot handle manytomany
        for name, value in deferred.items():
            self.setattr(name, value)
        return self

    def setattr(self, name, value):
        if hasattr(self, 'set_%s' % name):
            getattr(self, 'set_%s' % name)(value)
        elif self._is_qs(name):
            manager = getattr(self.obj, name)
            # clear() only provided if the ForeignKey can have a value of null:
            if hasattr(manager, 'clear'):
                manager.clear()
                for element in value:
                    manager.add(element)
            else:
                raise TypeError("cannot update if the related ForeignKey cannot be null")
        #elif self.get_class(name), models.FileField):# TODO
        #    file_field = getattr(self.obj, name)
        #    file_field.save(value.name, value)
        else:
            setattr(self.obj, name, value)

    @classmethod
    def _is_qs(cls, name):
        klass = getattr(cls.common_schema()[name], 'klass', object)
        return issubclass(klass, QuerySet)

    @classmethod
    def _wrap(cls, f):
        func = cls._field_wrapping_functions.subsetget(type(f))
        if func is not None:
            return func(f)
        else:
            return SmartDict.ValueUnknown # TODO: Not sure about that ...


class ReadOnlyModelNode(ModelMixin, ObjectNode):
    """
    A subclass of :class:`daccasts.ObjectNode` for django models. Only allows to retrieve objects that exist in the database, e.g. :

        >>> obj = ReadOnlyModelNode({'pk': 12, 'a_field': 'new_value'})
        >>> obj.a_field != 'new_value'
        True
    """

    @classmethod
    def load(cls, items_iter):
        items = dict(items_iter)
        try:
            return cls.retrieve(**items)
        except cls.model.DoesNotExist as e:
            raise cls.model.DoesNotExist('The ModelNode is read only and %s' % e)
        except cls.model.MultipleObjectsReturned:
            raise ValueError("'%s' is not unique for '%s'" %
            (cls.key_schema, cls.model))


class UpdateOnlyModelNode(ModelMixin, ObjectNode):
    """
    A subclass of :class:`daccasts.ObjectNode` for django models. Only allows to retrieve and update objects that exist in the database, e.g. :

        >>> obj = UpdateOnlyModelNode({'pk': 12, 'a_field': 'new_value'})
        >>> obj.a_field == 'new_value'
        True
    """

    @classmethod
    def load(cls, items_iter):
        items = dict(items_iter)
        try:
            node = cls.retrieve(**items)
        except cls.model.DoesNotExist as e:
            raise cls.model.DoesNotExist('The ModelNode is update only and %s' % e)
        except cls.model.MultipleObjectsReturned:
            raise ValueError("'%s' is not unique for '%s'" %
            (cls.key_schema, cls.model))
        return node.update(**items)


class CRUModelNode(ModelMixin, ObjectNode):
    """
    A subclass of :class:`daccasts.ObjectNode` for django models. Allows to retrieve/create and update objects.
    """

    @classmethod
    def load(cls, items_iter):
        items = dict(items_iter)
        try:
            node = cls.retrieve(**items)
        except cls.model.MultipleObjectsReturned:
            raise ValueError("'%s' is not unique for '%s'" %
            (cls.key_schema, cls.model))
        except cls.model.DoesNotExist:
            node = cls.create(**items)
        return node.update(**items)


serialize = Cast({
    AllSubSetsOf(dict): MappingNode,
    AllSubSetsOf(list): IterableNode,
    AllSubSetsOf(int): IdentityNode,
    AllSubSetsOf(float): IdentityNode,
    AllSubSetsOf(bool): IdentityNode,
    AllSubSetsOf(basestring): IdentityNode,
    AllSubSetsOf(types.NoneType): IdentityNode,
    AllSubSetsOf(datetime.datetime): DateTimeNode,
    AllSubSetsOf(datetime.date): DateNode,

    AllSubSetsOf(models.Model): ReadOnlyModelNode,
    AllSubSetsOf(QuerySet): QuerySetNode,
    AllSubSetsOf(File): IdentityNode,
}, {
    AllSubSetsOf(dict): MappingNode,
    AllSubSetsOf(list): IterableNode,
    AllSubSetsOf(object): MappingNode,
    AllSubSetsOf(QuerySet): IterableNode,
})


deserialize = Cast({
    AllSubSetsOf(dict): MappingNode,
    AllSubSetsOf(list): IterableNode,
    AllSubSetsOf(int): IdentityNode,
    AllSubSetsOf(float): IdentityNode,
    AllSubSetsOf(bool): IdentityNode,
    AllSubSetsOf(basestring): IdentityNode,
    AllSubSetsOf(types.NoneType): IdentityNode,
    AllSubSetsOf(datetime.datetime): DateTimeNode,
    AllSubSetsOf(datetime.date): DateNode,

    AllSubSetsOf(models.Model): ReadOnlyModelNode,
    AllSubSetsOf(QuerySet): QuerySetNode,
    AllSubSetsOf(File): IdentityNode,
})
