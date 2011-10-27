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

from django.contrib.gis.db.models import (GeometryField, PointField, LineStringField, 
PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField, GeometryCollectionField)
from django.contrib.gis.geos import (Point, LineString,
LinearRing, Polygon, MultiPoint, MultiLineString, MultiPolygon)

GEODJANGO_FIELDS = (GeometryField, PointField, LineStringField, 
    PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField,
    GeometryCollectionField)

QUERYSET_FIELDS = (ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor,
    models.ManyToManyField, GenericRelation)

from any2any import *
from any2any.utils import classproperty
from any2any.stdlib.bundle import DateTimeBundle, DateBundle
from any2any.django.utils import ModelIntrospector

# GeoDjango
#======================================
class PointBundle(IterableBundle):

    klass = Point
    value_type = float


class LineStringBundle(IterableBundle):

    klass = LineString
    value_type = Point


class LinearRingBundle(IterableBundle):

    klass = LinearRing
    value_type = Point


class PolygonBundle(IterableBundle):

    klass = Polygon
    value_type = LinearRing


class MultiPointBundle(IterableBundle):

    klass = MultiPoint
    value_type = Point
    

class MultiLineStringBundle(IterableBundle):

    klass = MultiLineString
    value_type = LineString


class MultiPolygonBundle(IterableBundle):

    klass = MultiPolygon
    value_type = Polygon


# ModelBundle
#======================================
class QuerySetBundle(IterableBundle):

    klass = QuerySet
    value_type = models.Model

    def iter(self):
        if hasattr(self.obj, 'all'):
            return enumerate(self.obj.all())
        else:
            return enumerate(self.obj)

    @classmethod
    def factory(cls, items_iter):
        obj = list((v for k, v in items_iter))
        return cls(obj)
        

class ModelMixin(ModelIntrospector):

    key_schema = ('pk',)
    """tuple. ``(<field_name>)``. Tuple of field names used to fetch the object from the database."""

    include_related = False
    """bool. If True, the schema will also include related ForeignKeys and related ManyToMany."""

    @classmethod
    def factory(cls, items_iter):
        raise NotImplementedError

    @classmethod
    def get_schema(cls):
        schema = super(ModelMixin, cls).get_schema()
        related_keys = cls.related_dict.keys()
        if not cls.include_related:
            for k in related_keys:
                if not k in cls.include and not k in cls.extra_schema:
                    schema.pop(k, None)
        return schema

    @classproperty
    def model(cls):
        return cls.klass

    @classmethod
    def default_schema(cls):
        if not hasattr(cls, '_default_schema'):
            schema = {}
            schema.update(cls._build_schema({'pk': cls.pk_field}))
            schema.update(cls._build_schema(cls.fields_dict))
            schema.update(cls._build_schema(cls.related_dict))
            cls._default_schema = schema
        return cls._default_schema

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
        return cls(cls.model.objects.get(**key_dict))

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
        klass = getattr(cls.get_schema()[name], 'klass', object)
        return issubclass(klass, QuerySet)

    @classmethod
    def _build_schema(cls, fields_dict):
        # Takes a dict ``{<field_name>: <fields>}``, and returns a dict
        # ``{<field_name>: <class>}``.
        schema = {}
        for name, field in fields_dict.items():
            field_type = type(field)

            if isinstance(field, models.ForeignKey):
                bc = ReadOnlyModelBundle.get_subclass(klass=field.rel.to)
            elif isinstance(field, (models.ManyToManyField, GenericRelation)):
                bc = QuerySetBundle.get_subclass(value_type=field.rel.to)
            elif isinstance(field, (ManyRelatedObjectsDescriptor,
            ForeignRelatedObjectsDescriptor)):
                bc = QuerySetBundle.get_subclass(value_type=field.related.model)
            elif isinstance(field, models.DateTimeField):
                bc = DateTimeBundle
            elif isinstance(field, models.DateField):
                bc = DateBundle
            # geodjango
            elif isinstance(field, GEODJANGO_FIELDS):
                if isinstance(field, PointField):
                    bc = PointBundle
                elif isinstance(field, LineStringField):
                    bc = LineStringBundle
                elif isinstance(field, PolygonField):
                    bc = PolygonBundle
                elif isinstance(field, MultiPointField):
                    bc = MultiPointBundle
                elif isinstance(field, MultiLineStringField):
                    bc = MultiLineBundle
                elif isinstance(field, MultiPolygonField):
                    bc = MultiPolygonBundle
            else:
                bc = field_type

            schema[name] = bc
        return schema


class ReadOnlyModelBundle(ModelMixin, ObjectBundle):
    """
    A subclass of :class:`daccasts.ObjectBundle` for django models. Only allows to retrieve objects that exist in the database, e.g. :

        >>> obj = ReadOnlyModelBundle({'pk': 12, 'a_field': 'new_value'})
        >>> obj.a_field != 'new_value'
        True
    """

    @classmethod
    def factory(cls, items_iter):
        items = dict(items_iter)
        try:
            return cls.retrieve(**items)
        except cls.model.DoesNotExist as e:
            raise cls.model.DoesNotExist('The ModelBundle is read only and %s' % e)
        except cls.model.MultipleObjectsReturned:
            raise ValueError("'%s' is not unique for '%s'" %
            (cls.key_schema, cls.model))


class UpdateOnlyModelBundle(ModelMixin, ObjectBundle):
    """
    A subclass of :class:`daccasts.ObjectBundle` for django models. Only allows to retrieve and update objects that exist in the database, e.g. :

        >>> obj = UpdateOnlyModelBundle({'pk': 12, 'a_field': 'new_value'})
        >>> obj.a_field == 'new_value'
        True
    """

    @classmethod
    def factory(cls, items_iter):
        items = dict(items_iter)
        try:
            bundle = cls.retrieve(**items)
        except cls.model.DoesNotExist as e:
            raise cls.model.DoesNotExist('The ModelBundle is update only and %s' % e)
        except cls.model.MultipleObjectsReturned:
            raise ValueError("'%s' is not unique for '%s'" %
            (cls.key_schema, cls.model))
        return bundle.update(**items)


class CRUModelBundle(ModelMixin, ObjectBundle):
    """
    A subclass of :class:`daccasts.ObjectBundle` for django models. Allows to retrieve/create and update objects.
    """

    @classmethod
    def factory(cls, items_iter):
        items = dict(items_iter)
        try:
            bundle = cls.retrieve(**items)
        except cls.model.MultipleObjectsReturned:
            raise ValueError("'%s' is not unique for '%s'" %
            (cls.key_schema, cls.model))
        except cls.model.DoesNotExist:
            bundle = cls.create(**items)
        return bundle.update(**items)


serialize = Cast({
    AllSubSetsOf(dict): MappingBundle,
    AllSubSetsOf(list): IterableBundle,
    AllSubSetsOf(object): IdentityBundle,
    AllSubSetsOf(models.Model): ReadOnlyModelBundle,
}, {
    AllSubSetsOf(dict): MappingBundle,
    AllSubSetsOf(list): IterableBundle,
    AllSubSetsOf(object): MappingBundle,
    AllSubSetsOf(QuerySet): IterableBundle,
})


deserialize = Cast({
    AllSubSetsOf(dict): MappingBundle,
    AllSubSetsOf(list): IterableBundle,
    AllSubSetsOf(object): IdentityBundle,
    AllSubSetsOf(models.Model): ReadOnlyModelBundle,
})
