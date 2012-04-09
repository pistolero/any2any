from django.contrib.gis.db.models import (GeometryField, PointField, LineStringField, 
PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField, GeometryCollectionField)
from django.contrib.gis.geos import (GEOSGeometry, Point, LineString,
LinearRing, Polygon, MultiPoint, MultiLineString, MultiPolygon)

GEODJANGO_FIELDS = (GeometryField, PointField, LineStringField, 
    PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField,
    GeometryCollectionField)

from any2any.django.node import ModelMixin, serialize, deserialize
from any2any.utils import ClassSet, AllSubSetsOf
from any2any.node import IterableNode


class GEOSGeometryNode(IterableNode):

    @classmethod
    def load(cls, items_iter):
        # Necessary, because constructor of some GEOSGeometry objects don't 
        # accept a list as argument.
        # TODO: needs ordered dict to pass data between nodes
        items_iter = sorted(items_iter, key=lambda i: i[0])
        obj = cls.klass(*(v for k, v in items_iter))
        return cls(obj)


class PointNode(GEOSGeometryNode):

    klass = Point
    value_type = float


class LineStringNode(GEOSGeometryNode):

    klass = LineString
    value_type = Point


class LinearRingNode(GEOSGeometryNode):

    klass = LinearRing
    value_type = Point


class PolygonNode(GEOSGeometryNode):

    klass = Polygon
    value_type = LinearRing


class MultiPointNode(GEOSGeometryNode):

    klass = MultiPoint
    value_type = Point
    

class MultiLineStringNode(GEOSGeometryNode):

    klass = MultiLineString
    value_type = LineString


class MultiPolygonNode(GEOSGeometryNode):

    klass = MultiPolygon
    value_type = Polygon


def wrap_geodjango_field(f):
    if isinstance(f, PointField):
        geom_type = Point
    elif isinstance(f, LineStringField):
        geom_type = LineStringNode
    elif isinstance(f, PolygonField):
        geom_type = PolygonNode
    elif isinstance(f, MultiPointField):
        geom_type = MultiPointNode
    elif isinstance(f, MultiLineStringField):
        geom_type = MultiLineNode
    elif isinstance(f, MultiPolygonField):
        geom_type = MultiPolygonNode
    return NodeInfo([type(f), geom_type])


# Plugging-in our function for wrapping GeoDjango fields
ModelMixin._field_wrapping_functions[ClassSet(GEODJANGO_FIELDS)] = wrap_geodjango_field


# Plugging-in our nodes for GeoDjango geometry objects
serialize.node_class_map.update({
    ClassSet(Point): PointNode,
    ClassSet(LineString): LineStringNode,
    ClassSet(LinearRing): LinearRingNode,
    ClassSet(Polygon): PolygonNode,
    ClassSet(MultiPoint): MultiPointNode,
    ClassSet(MultiLineString): MultiLineStringNode,
    ClassSet(MultiPolygon): MultiPolygonNode
})
serialize.fallback_map.update({
    AllSubSetsOf(GEOSGeometry): IterableNode,
})

deserialize.node_class_map.update({
    ClassSet(Point): PointNode,
    ClassSet(LineString): LineStringNode,
    ClassSet(LinearRing): LinearRingNode,
    ClassSet(Polygon): PolygonNode,
    ClassSet(MultiPoint): MultiPointNode,
    ClassSet(MultiLineString): MultiLineStringNode,
    ClassSet(MultiPolygon): MultiPolygonNode,
})
