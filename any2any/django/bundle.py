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

try:
    from django.contrib.gis.db.models import (GeometryField, PointField, LineStringField, 
    PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField, GeometryCollectionField)
    from django.contrib.gis.geos import (GEOSGeometry, Point, LineString,
    LinearRing, Polygon, MultiPoint, MultiLineString, MultiPolygon)

    GEODJANGO_FIELDS = (GeometryField, PointField, LineStringField, 
        PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField,
        GeometryCollectionField)
except ImportError:
    USES_GEODJANGO = False
else:
    USES_GEODJANGO = True

QUERYSET_FIELDS = (ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor,
    models.ManyToManyField, GenericRelation)
RELATED_FIELDS = (ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor)
SIMPLE_FIELDS = (models.CharField, models.TextField, models.IntegerField, models.DateTimeField,
    models.DateField, models.AutoField, models.FileField, models.BooleanField)


from any2any import *
from any2any.bundle import ValueInfo
from any2any.utils import classproperty, SmartDict
from any2any.stdlib.bundle import DateTimeBundle, DateBundle
from any2any.django.utils import ModelIntrospector


# GeoDjango
#======================================
if USES_GEODJANGO:
    class GEOSGeometryBundle(IterableBundle):

        @classmethod
        def factory(cls, items_iter):
            # Necessary, because constructor of some GEOSGeometry objects don't 
            # accept a list as argument.
            # TODO: needs ordered dict to pass data between bundles
            items_iter = sorted(items_iter, key=lambda i: i[0])
            obj = cls.klass(*(v for k, v in items_iter))
            return cls(obj)


    class PointBundle(GEOSGeometryBundle):

        klass = Point
        value_type = float


    class LineStringBundle(GEOSGeometryBundle):

        klass = LineString
        value_type = Point


    class LinearRingBundle(GEOSGeometryBundle):

        klass = LinearRing
        value_type = Point


    class PolygonBundle(GEOSGeometryBundle):

        klass = Polygon
        value_type = LinearRing


    class MultiPointBundle(GEOSGeometryBundle):

        klass = MultiPoint
        value_type = Point
        

    class MultiLineStringBundle(GEOSGeometryBundle):

        klass = MultiLineString
        value_type = LineString


    class MultiPolygonBundle(GEOSGeometryBundle):

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
                if not k in cls.include and (cls.schema is None or not k in cls.schema):
                    schema.pop(k, None)
        return schema

    @classproperty
    def model(cls):
        return cls.klass

    @classproperty
    def queryset(cls):
        return cls.model.objects

    @classmethod
    def default_schema(cls):
        if not hasattr(cls, '_default_schema'):
            schema = {}
            schema['pk'] = cls._wrap(cls.pk_field)
            for name, field in cls.fields_dict.items():                
                schema[name] = cls._wrap(field)
            for name, field in cls.related_dict.items():                
                schema[name] = cls._wrap(field)
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
        klass = getattr(cls.get_schema()[name], 'klass', object)
        return issubclass(klass, QuerySet)

    @classmethod
    def _wrap(cls, f):
        ftype = type(f)
        if isinstance(f, SIMPLE_FIELDS):
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
            return ValueInfo(klass, lookup_with={
                AllSubSetsOf(object): (ftype, klass),
                Singleton(types.NoneType): types.NoneType
            })
        elif isinstance(f, models.ForeignKey):
            return ValueInfo(f.rel.to, lookup_with={
                AllSubSetsOf(object): (ftype, f.rel.to),
                Singleton(types.NoneType): types.NoneType
            })
        elif isinstance(f, QUERYSET_FIELDS):
            if isinstance(f, RELATED_FIELDS):
                to = f.related.model
            else:
                to = f.rel.to
            return ValueInfo(QuerySet, schema={SmartDict.KeyAny: to}, lookup_with={
                AllSubSetsOf(object): (ftype, QuerySet)
            })
        elif USES_GEODJANGO and isinstance(f, GEODJANGO_FIELDS):
            if isinstance(f, PointField):
                geom_type = Point
            elif isinstance(f, LineStringField):
                geom_type = LineStringBundle
            elif isinstance(f, PolygonField):
                geom_type = PolygonBundle
            elif isinstance(f, MultiPointField):
                geom_type = MultiPointBundle
            elif isinstance(f, MultiLineStringField):
                geom_type = MultiLineBundle
            elif isinstance(f, MultiPolygonField):
                geom_type = MultiPolygonBundle
            return ValueInfo(geom_type, lookup_with={
                AllSubSetsOf(object): (ftype, geom_type)
            })
        else:
            return ValueInfo(str, lookup_with={
                AllSubSetsOf(object): (ftype, str)
            }) # TODO: Not sure about that ...


class ReadOnlyModelBundle(ModelMixin, ObjectBundle):
    """
    A subclass of :class:`daccasts.ObjectBundle` for django models. Only allows to retrieve objects that exist in the database, e.g. :

        >>> obj = ReadOnlyModelBundle({'pk': 12, 'a_field': 'new_value'})
        >>> obj.a_field != 'new_value'
        True
    """

    def iter(self):
        if not self.obj is None: # TODO: quick fix for the fact that FK can be null
            return super(ReadOnlyModelBundle, self).iter()
        else:
            raise StopIteration

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

    def iter(self):
        if not self.obj is None: # TODO: quick fix for the fact that FK can be null
            return super(UpdateOnlyModelBundle, self).iter()
        else:
            raise StopIteration

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

    def iter(self):
        if not self.obj is None: # TODO: quick fix for the fact that FK can be null
            return super(CRUModelBundle, self).iter()
        else:
            raise StopIteration

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
    AllSubSetsOf(int): IdentityBundle,
    AllSubSetsOf(float): IdentityBundle,
    AllSubSetsOf(bool): IdentityBundle,
    AllSubSetsOf(basestring): IdentityBundle,
    AllSubSetsOf(datetime.datetime): DateTimeBundle,
    AllSubSetsOf(datetime.date): DateBundle,

    AllSubSetsOf(models.Model): ReadOnlyModelBundle,
    AllSubSetsOf(QuerySet): QuerySetBundle,
    AllSubSetsOf(File): IdentityBundle,
}, {
    AllSubSetsOf(dict): MappingBundle,
    AllSubSetsOf(list): IterableBundle,
    AllSubSetsOf(object): MappingBundle,
    AllSubSetsOf(QuerySet): IterableBundle,
})

if USES_GEODJANGO:
    serialize.bundle_class_map.update({
        Singleton(Point): PointBundle,
        Singleton(LineString): LineStringBundle,
        Singleton(LinearRing): LinearRingBundle,
        Singleton(Polygon): PolygonBundle,
        Singleton(MultiPoint): MultiPointBundle,
        Singleton(MultiLineString): MultiLineStringBundle,
        Singleton(MultiPolygon): MultiPolygonBundle
    })
    serialize.fallback_map.update({
        AllSubSetsOf(GEOSGeometry): IterableBundle,
    })

deserialize = Cast({
    AllSubSetsOf(dict): MappingBundle,
    AllSubSetsOf(list): IterableBundle,
    AllSubSetsOf(int): IdentityBundle,
    AllSubSetsOf(float): IdentityBundle,
    AllSubSetsOf(bool): IdentityBundle,
    AllSubSetsOf(basestring): IdentityBundle,
    AllSubSetsOf(datetime.datetime): DateTimeBundle,
    AllSubSetsOf(datetime.date): DateBundle,

    AllSubSetsOf(models.Model): ReadOnlyModelBundle,
    AllSubSetsOf(QuerySet): QuerySetBundle,
    AllSubSetsOf(File): IdentityBundle,
})

if USES_GEODJANGO:
    deserialize.bundle_class_map.update({
        Singleton(Point): PointBundle,
        Singleton(LineString): LineStringBundle,
        Singleton(LinearRing): LinearRingBundle,
        Singleton(Polygon): PolygonBundle,
        Singleton(MultiPoint): MultiPointBundle,
        Singleton(MultiLineString): MultiLineStringBundle,
        Singleton(MultiPolygon): MultiPolygonBundle,
    })
