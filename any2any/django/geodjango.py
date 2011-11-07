from django.contrib.gis.db.models import (GeometryField, PointField, LineStringField, 
PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField, GeometryCollectionField)
from django.contrib.gis.geos import (GEOSGeometry, Point, LineString,
LinearRing, Polygon, MultiPoint, MultiLineString, MultiPolygon)

GEODJANGO_FIELDS = (GeometryField, PointField, LineStringField, 
    PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField,
    GeometryCollectionField)


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


class ModelBundle(ObjectBundle):

    @classmethod
    def _build_schema(cls, fields_dict):
        schema = super(ModelBundle, cls)._build_schema(fields_dict)
        for name, f in fields_dict.items():
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
            v = ValueInfo(geom_type, lookup_with=(ftype, geom_type))



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
