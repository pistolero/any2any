# -*- coding: utf-8 -*-
import copy
import datetime

from django.db import models
from django.http import QueryDict
from django.db.models.fields.related import ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey, GenericRelation
from django.db.models.query import QuerySet

from django.contrib.gis.db.models import (GeometryField, PointField, LineStringField, 
PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField, GeometryCollectionField)
from django.contrib.gis.geos import (Point, LineString,
LinearRing, Polygon, MultiPoint, MultiLineString, MultiPolygon)

from any2any import (Cast, Mm, CastItems, FromIterable, ToIterable, FromObject, ToMapping,
FromMapping, ToObject, WrappedContainer, WrappedObject, Setting, DivideAndConquerCast)
from any2any.stacks.basicstack import BasicStack, ListToList, Identity, WrappedDateTime, WrappedDate
from any2any.base import MmToCastSetting
from any2any.utils import classproperty


# Model instrospector
#======================================
class ModelIntrospector(object):
    """
    Mixin for adding introspection capabilities to any class.
    """

    @classproperty
    def fields(cls):
        # Returns a set with all the fields,
        # but excluding the pointers used for MTI
        mod_opts = cls.model._meta
        ptr_fields = cls.collect_ptrs(cls.model)
        all_fields = mod_opts.fields + mod_opts.many_to_many
        return set(all_fields) - set(ptr_fields)

    @classproperty
    def fields_dict(cls):
        # Returns a dictionary `{<field_name>, <field>}`
        return dict(((f.name, f) for f in cls.fields))

    @classproperty
    def related_dict(cls):
        # Returns a dictionary {<attr_name>: <descriptor>} with all the related descriptors,
        def retrieve_desc((k, v)):
            return isinstance(v, (ManyRelatedObjectsDescriptor,
            ForeignRelatedObjectsDescriptor))
        return dict(filter(retrieve_desc, cls.model.__dict__.items()))

    @classproperty
    def pk_field_name(cls):
        # We get pk's field name from the "super" parent (i.e. the "eldest").
        # This allows to handle MTI nicely (and transparently).
        all_pks = set([p._meta.pk for p in cls.model._meta.get_parent_list()])
        all_pks.add(cls.model._meta.pk)
        all_ptrs = set(cls.collect_ptrs(cls.model))
        return list(all_pks - all_ptrs)[0].name

    @classproperty
    def pk_field(cls):
        return cls.fields_dict[cls.pk_field_name]

    @classmethod
    def collect_ptrs(cls, model):
        # Recursively collects all the fields pointing to parents of `model`
        ptr_fields = []
        for parent_model, ptr_field in model._meta.parents.iteritems():
            ptr_fields.append(ptr_field)
            ptr_fields += cls.collect_ptrs(parent_model)
        return ptr_fields


# GeoDjango
#======================================
class WrappedGeo(WrappedContainer):

    @classmethod
    def new(cls, elem_list):
        # Necessary because some constructor don't take lists
        return super(WrappedGeo, cls).new(*elem_list)


class WrappedPoint(WrappedGeo):

    klass = Point
    value_type = float


class WrappedLineString(WrappedGeo):

    klass = LineString
    value_type = Point


class WrappedLinearRing(WrappedGeo):

    klass = LinearRing
    value_type = Point


class WrappedPolygon(WrappedGeo):

    klass = Polygon
    value_type = LinearRing


class WrappedMultiPoint(WrappedGeo):

    klass = MultiPoint
    value_type = Point
    

class WrappedMultiLineString(WrappedGeo):

    klass = MultiLineString
    value_type = LineString


class WrappedMultiPolygon(WrappedGeo):

    klass = MultiPolygon
    value_type = Polygon


# WrappedModel
#======================================
class WrappedQuerySet(WrappedContainer):
    """
    A subclass of :class:`daccasts.WrappedContainer` for querysets.
    """

    klass = QuerySet
    superclasses = (QuerySet, models.Manager)
    factory = list


class ModelMixin(ModelIntrospector):
    """
    A subclass of :class:`daccasts.WrappedObject` for django models.

    .. note::
        :class:`FileField`s won't appear in the default schema.
    """

    key_schema = ('pk',)
    """tuple. ``(<field_name>)``. Tuple of field names used to fetch the object from the database."""

    include_related = False
    """bool. If True, the schema will also include related ForeignKeys and related ManyToMany."""

    @classproperty
    def model(cls):
        return cls.klass

    @classmethod
    def new(cls, **items):
        raise NotImplementedError

    @classmethod
    def default_schema(cls):
        if not hasattr(cls, '_default_schema'):
            schema = {}
            schema.update(cls._wrap_fields({'pk': cls.pk_field}))
            schema.update(cls._wrap_fields(cls.fields_dict))
            schema.update(cls._wrap_fields(cls.related_dict))
            cls._default_schema = schema
        return cls._default_schema

    @classmethod
    def get_schema(cls):
        schema = super(ModelMixin, cls).get_schema()
        related_keys = cls.related_dict.keys()
        if not cls.include_related:
            for k in related_keys:
                if not k in cls.include and not k in cls.extra_schema:
                    schema.pop(k, None)
        return schema

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
        return cls.model(**(key_dict or {'pk': None}))

    @classmethod
    def retrieve(cls, **items):
        key_dict = cls.extract_key(items)
        if not key_dict:
            raise cls.model.DoesNotExist("no key could be extracted from the data")
        return cls.model.objects.get(**key_dict)

    @classmethod
    def update(cls, instance, **items):
        deferred = {}
        for name, value in items.items():
            if cls._is_qs(name):
                deferred[name] = value
            else:
                cls.setattr(instance, name, value)
        instance.save()# Because otherwise we cannot handle manytomany
        for name, value in deferred.items():
            cls.setattr(instance, name, value)
        return instance

    @classmethod
    def setattr(cls, instance, name, value):
        if hasattr(cls, 'set_%s' % name):
            getattr(cls, 'set_%s' % name)(instance, value)
        elif cls._is_qs(name):
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

    @classmethod
    def _is_qs(cls, name):
        klass = cls.get_class(name)
        return WrappedObject.issubclass(klass, QuerySet)

    @classmethod
    def _wrap_fields(cls, fields_dict):
        # Takes a dict ``{<field_name>: <fields>}``, and returns a dict
        # ``{<field_name>: <wrapped_field>}``.
        wrapped_fields = {}
        for name, field in fields_dict.items():
            field_type = type(field)

            if isinstance(field, models.ForeignKey):
                class WrappedField(ReadOnlyWrappedModel):
                    klass = field.rel.to
                    superclasses = (field_type,)
            elif isinstance(field, (models.ManyToManyField, GenericRelation)):
                class WrappedField(WrappedQuerySet):
                    klass = field_type
                    value_type = field.rel.to
            elif isinstance(field, (ManyRelatedObjectsDescriptor,
            ForeignRelatedObjectsDescriptor)):
                class WrappedField(WrappedQuerySet):
                    klass = field_type
                    value_type = field.related.model
            elif isinstance(field, models.DateTimeField):
                class WrappedField(WrappedDateTime):
                    klass = field_type
                    superclasses = (datetime.datetime,)
                    factory = datetime.datetime
            elif isinstance(field, models.DateField):
                class WrappedField(WrappedDate):
                    klass = field_type
                    superclasses = (datetime.date,)
                    factory = datetime.date
            elif isinstance(field, models.FileField):
                continue
            # geodjango
            elif isinstance(field, (GeometryField, PointField, LineStringField, 
            PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField,
            GeometryCollectionField)):
                if isinstance(field, PointField):
                    WrappedGeo = WrappedPoint
                elif isinstance(field, LineStringField):
                    WrappedGeo = WrappedLineString
                elif isinstance(field, PolygonField):
                    WrappedGeo = WrappedPolygon
                elif isinstance(field, MultiPointField):
                    WrappedGeo = WrappedMultiPoint
                elif isinstance(field, MultiLineStringField):
                    WrappedGeo = WrappedMultiLineString
                elif isinstance(field, MultiPolygonField):
                    WrappedGeo = WrappedMultiPolygon
                class WrappedField(WrappedGeo):
                    klass = field_type
                    superclasses = (WrappedGeo.klass,)
                    factory = WrappedGeo.klass
            else:
                class WrappedField(WrappedObject):
                    klass = field_type

            wrapped_fields[name] = WrappedField
        return wrapped_fields


class ReadOnlyWrappedModel(ModelMixin, WrappedObject):
    """
    A subclass of :class:`daccasts.WrappedObject` for django models. Only allows to retrieve objects that exist in the database, e.g. :

        >>> obj = ReadOnlyWrappedModel({'pk': 12, 'a_field': 'new_value'})
        >>> obj.a_field != 'new_value'
        True
    """

    @classmethod
    def new(cls, **items):
        try:
            return cls.retrieve(**items)
        except cls.model.DoesNotExist as e:
            raise cls.model.DoesNotExist('The WrappedModel is read only and %s' % e)
        except cls.model.MultipleObjectsReturned:
            raise ValueError("'%s' is not unique for '%s'" %
            (cls.key_schema, cls.model))


class UpdateOnlyWrappedModel(ModelMixin, WrappedObject):
    """
    A subclass of :class:`daccasts.WrappedObject` for django models. Only allows to retrieve and update objects that exist in the database, e.g. :

        >>> obj = UpdateOnlyWrappedModel({'pk': 12, 'a_field': 'new_value'})
        >>> obj.a_field == 'new_value'
        True
    """

    @classmethod
    def new(cls, **items):
        try:
            instance = cls.retrieve(**items)
        except cls.model.DoesNotExist as e:
            raise cls.model.DoesNotExist('The WrappedModel is update only and %s' % e)
        except cls.model.MultipleObjectsReturned:
            raise ValueError("'%s' is not unique for '%s'" %
            (cls.key_schema, cls.model))
        return cls.update(instance, **items)


class WrappedModel(ModelMixin, WrappedObject):
    """
    A subclass of :class:`daccasts.WrappedObject` for django models. Allows to retrieve/create and update objects.
    """

    @classmethod
    def new(cls, **items):
        try:
            instance = cls.retrieve(**items)
        except cls.model.MultipleObjectsReturned:
            raise ValueError("'%s' is not unique for '%s'" %
            (cls.key_schema, cls.model))
        except cls.model.DoesNotExist:
            instance = cls.create(**items)
        return cls.update(instance, **items)


# Mixins
#======================================
class FromModel(FromObject):

    from_wrapped = Setting(default=ReadOnlyWrappedModel)


class ToModel(ToObject):

    to_wrapped = Setting(default=ReadOnlyWrappedModel)

    def call(self, inpt):
        instance = super(ToModel, self).call(inpt)
        # It is necessary to save here for handling FKs. 
        instance.save()
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


class StripEmptyValues(ListToList):

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


class WrappedQueryDict(WrappedObject, ModelIntrospector):

    list_keys = []
    klass = dict
    model = None

    @classmethod
    def get_class(cls, key):
        if (key in cls.list_keys) or cls.is_list(key):
            return list
        else:
            return NotImplemented

    @classmethod
    def is_list(cls, key):
        if cls.model:
            try:
                field = filter(lambda f: f.name == key, cls.fields)[0]
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

    to_wrapped = Setting(default=WrappedQueryDict)
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
class ModelToDict(FromModel, ToMapping, CastItems, DivideAndConquerCast):

    class Meta:
        defaults = {'to': dict}    


class DictToModel(ToModel, FromMapping, CastItems, DivideAndConquerCast):

    class Meta:
        defaults = {'from_': dict}


class QuerySetToList(FromQuerySet, CastItems, ToIterable, DivideAndConquerCast):

    class Meta:
        defaults = {'to': list}


class ListToQuerySet(FromIterable, CastItems, ToIterable, DivideAndConquerCast):

    class Meta:
        defaults = {'from_': list}


class DjangoSerializer(BasicStack):
    """
    Subclass of :class:`base.CastStack`, for serializing Django objects
    """

    class Meta:
        defaults = {
            'mm_to_cast': {
                Mm(from_any=models.Manager): QuerySetToList(),
                Mm(from_any=QuerySet): QuerySetToList(),
                Mm(from_any=models.Model): ModelToDict(),
                Mm(from_any=QueryDict): QueryDictFlatener(),
                # geodjango
                Mm(from_any=Point): ListToList(from_wrapped=WrappedPoint),
                Mm(from_any=LineString): ListToList(from_wrapped=WrappedLineString),
                Mm(from_any=LinearRing): ListToList(from_wrapped=WrappedLinearRing),
                Mm(from_any=Polygon): ListToList(from_wrapped=WrappedPolygon),
                Mm(from_any=MultiPoint): ListToList(from_wrapped=WrappedMultiPoint),
                Mm(from_any=MultiLineString): ListToList(from_wrapped=WrappedMultiLineString),
                Mm(from_any=MultiPolygon): ListToList(from_wrapped=WrappedMultiPolygon),
            }
        }


class DjangoDeserializer(BasicStack):
    """
    Subclass of :class:`base.CastStack`, for deserializing Django objects
    """

    class Meta:
        defaults = {
            'mm_to_cast': {
                Mm(to_any=models.Manager): ListToQuerySet(),
                Mm(to_any=QuerySet): ListToQuerySet(),
                Mm(from_any=dict, to_any=models.Model): DictToModel(),
                # geodjango
                Mm(to_any=Point): ListToList(to_wrapped=WrappedPoint),
                Mm(to_any=LineString): ListToList(to_wrapped=WrappedLineString),
                Mm(to_any=LinearRing): ListToList(to_wrapped=WrappedLinearRing),
                Mm(to_any=Polygon): ListToList(to_wrapped=WrappedPolygon),
                Mm(to_any=MultiPoint): ListToList(to_wrapped=WrappedMultiPoint),
                Mm(to_any=MultiLineString): ListToList(to_wrapped=WrappedMultiLineString),
                Mm(to_any=MultiPolygon): ListToList(to_wrapped=WrappedMultiPolygon),
            }
        }
