from django.contrib.gis.db.models import (GeometryField, PointField, LineStringField, 
PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField, GeometryCollectionField)
from django.contrib.gis.geos import (GEOSGeometry, Point, LineString,
LinearRing, Polygon, MultiPoint, MultiLineString, MultiPolygon)

GEODJANGO_FIELDS = (GeometryField, PointField, LineStringField, 
    PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField,
    GeometryCollectionField)

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
from bundle import *
from any2any import *
from any2any.bundle import ValueInfo
from any2any.utils import classproperty
from any2any.stdlib.bundle import DateTimeBundle, DateBundle


# GeoDjango
#======================================
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
class GeoModelMixin(ModelMixin):

    @classmethod
    def _wrap(cls, f):
        ftype = type(f)
        if isinstance(f, GEODJANGO_FIELDS):
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
            return ValueInfo(geom_type, lookup_with=(ftype, geom_type))
        else:
            return super(GeoModelMixin, cls)._wrap(f)



class ReadOnlyModelBundle(GeoModelMixin, ObjectBundle):
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


class UpdateOnlyModelBundle(GeoModelMixin, ObjectBundle):
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


class CRUModelBundle(GeoModelMixin, ObjectBundle):
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

import datetime
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

    Singleton(Point): PointBundle,
    Singleton(LineString): LineStringBundle,
    Singleton(LinearRing): LinearRingBundle,
    Singleton(Polygon): PolygonBundle,
    Singleton(MultiPoint): MultiPointBundle,
    Singleton(MultiLineString): MultiLineStringBundle,
    Singleton(MultiPolygon): MultiPolygonBundle,
}, {
    AllSubSetsOf(dict): MappingBundle,
    AllSubSetsOf(list): IterableBundle,
    AllSubSetsOf(object): MappingBundle,
    AllSubSetsOf(QuerySet): IterableBundle,

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

    Singleton(Point): PointBundle,
    Singleton(LineString): LineStringBundle,
    Singleton(LinearRing): LinearRingBundle,
    Singleton(Polygon): PolygonBundle,
    Singleton(MultiPoint): MultiPointBundle,
    Singleton(MultiLineString): MultiLineStringBundle,
    Singleton(MultiPolygon): MultiPolygonBundle,
})
