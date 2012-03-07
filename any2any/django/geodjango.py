from django.contrib.gis.db.models import (GeometryField, PointField, LineStringField, 
PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField, GeometryCollectionField)
from django.contrib.gis.geos import (GEOSGeometry, Point, LineString,
LinearRing, Polygon, MultiPoint, MultiLineString, MultiPolygon)

GEODJANGO_FIELDS = (GeometryField, PointField, LineStringField, 
    PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField,
    GeometryCollectionField)

from any2any.django.bundle import ModelMixin, serialize, deserialize
from any2any.utils import ClassSet


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


def wrap_geodjango_field(f):
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
    return BundleInfo([type(f), geom_type])


# Plugging-in our function for wrapping GeoDjango fields
ModelMixin._field_wrapping_functions[ClassSet(GEODJANGO_FIELDS)] = wrap_geodjango_field


# Plugging-in our bundles for GeoDjango geometry objects
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

deserialize.bundle_class_map.update({
    Singleton(Point): PointBundle,
    Singleton(LineString): LineStringBundle,
    Singleton(LinearRing): LinearRingBundle,
    Singleton(Polygon): PolygonBundle,
    Singleton(MultiPoint): MultiPointBundle,
    Singleton(MultiLineString): MultiLineStringBundle,
    Singleton(MultiPolygon): MultiPolygonBundle,
})
