# -*- coding: utf-8 -*-

from django.db.models import AutoField, CharField, ForeignKey, Model
from django.db.models.fields.related import ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor
from django.db.models.fields import Field
from django.db.models.manager import Manager
from django.http import QueryDict
from django.test import TestCase

from nose.tools import assert_raises, ok_

from any2any import *
from any2any.django.node import *
from models import *

try:
    from django.contrib.gis.db.models import (GeometryField, PointField, LineStringField, 
    PolygonField, MultiPointField, MultiLineStringField, MultiPolygonField, GeometryCollectionField)
    from django.contrib.gis.geos import (GEOSGeometry, Point, LineString,
    LinearRing, Polygon, MultiPoint, MultiLineString, MultiPolygon)
except ImportError:
    USES_GEODJANGO = False
else:
    from any2any.django.geodjango import *
    USES_GEODJANGO = True


class AuthorNode(CRUModelNode):
    klass = Author

class BookNode(CRUModelNode):
    klass = Book
    @classmethod
    def common_schema(cls):
        schema = super(BookNode, cls).common_schema()
        schema.update({'author': AuthorNode})
        return schema

class UpdateOnlyGourmand(UpdateOnlyModelNode):
    klass = Gourmand

class UpdateOnlyGourmandQuerySet(QuerySetNode):
    value_type = UpdateOnlyGourmand

class UpdateOnlyDish(UpdateOnlyModelNode):
    klass = Dish
    @classmethod
    def common_schema(cls):
        schema = super(UpdateOnlyDish, cls).common_schema()
        schema.update({'gourmand_set': UpdateOnlyGourmandQuerySet})
        return schema

class DishNode(CRUModelNode):
    klass = Dish

class UpdateOnlyDishQuerySet(QuerySetNode):
    value_type = UpdateOnlyDish

class DishQuerySet(QuerySetNode):
    value_type = DishNode

class GourmandNode(CRUModelNode):
    klass = Gourmand
    @classmethod
    def common_schema(cls):
        schema = super(GourmandNode, cls).common_schema()
        schema.update({'favourite_dishes': DishQuerySet})
        return schema

class UpdateOnlyGourmand(UpdateOnlyModelNode):
    klass = Gourmand
    @classmethod
    def common_schema(cls):
        schema = super(UpdateOnlyGourmand, cls).common_schema()
        schema.update({'favourite_dishes': UpdateOnlyDishQuerySet})
        return schema

class UpdateOnlyAuthor(UpdateOnlyModelNode):
    klass = Author

class UpdateOnlyBook(UpdateOnlyModelNode):
    klass = Book
    @classmethod
    def common_schema(cls):
        schema = super(UpdateOnlyBook, cls).common_schema()
        schema.update({'author': UpdateOnlyAuthor})
        return schema

class UpdateOnlyJournalist(UpdateOnlyModelNode):
    klass = Journalist

class UpdateOnlyJournalistQuerySet(QuerySetNode):
    value_type = UpdateOnlyJournalist

class UpdateOnlyJournal(UpdateOnlyModelNode):
    klass = Journal
    @classmethod
    def common_schema(cls):
        schema = super(UpdateOnlyJournal, cls).common_schema()
        schema.update({'journalist_set': UpdateOnlyJournalistQuerySet})
        return schema

class UpdateOnlyColumnist(UpdateOnlyModelNode):
    klass = Columnist
    key_schema = ('firstname', 'lastname')

class ColumnistNode(CRUModelNode):
    klass = Columnist
    key_schema = ('firstname', 'lastname')

class UpdateOnlyIssue(UpdateOnlyModelNode):
    klass = Issue


class ModelMixin_Test(TestCase):
    """
    Test ModelMixin, base of all ModelNodes
    """

    def common_schema_test(self):
        class ColumnistNode(ReadOnlyModelNode):
            klass = Columnist
            include_related = True
        class GourmandNode(ReadOnlyModelNode):
            klass = Gourmand
            include_related = True
        class WritingSausageNode(ReadOnlyModelNode):
            klass = WritingSausage
            include_related = True
        class JournalNode(ReadOnlyModelNode):
            klass = Journal
            include_related = True
        class DishNode(ReadOnlyModelNode):
            klass = Dish
            include_related = True
        columnist_fields = ColumnistNode.common_schema()
        gourmand_fields = GourmandNode.common_schema()
        wsausage_fields = WritingSausageNode.common_schema()
        journal_fields = JournalNode.common_schema()
        dish_fields = DishNode.common_schema()

        def get_field_type(vi):
            TYPES = (Field, ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor, ForeignKey)
            typ = filter(lambda v: issubclass(v, TYPES), vi._lookup_with.values())
            if typ: return typ[0]

        ok_(set(columnist_fields) == set(['id', 'pk', 'lastname', 'firstname', 'journal', 'column', 'nickname']))
        ok_(get_field_type(columnist_fields['pk']) is AutoField)
        ok_(get_field_type(columnist_fields['id']) is AutoField)
        ok_(get_field_type(columnist_fields['lastname']) is CharField)
        ok_(get_field_type(columnist_fields['nickname']) is CharField)
        ok_(get_field_type(columnist_fields['journal']) is ForeignKey)
        ok_(set(gourmand_fields) == set(['id', 'pk', 'lastname', 'firstname', 'favourite_dishes', 'pseudo']))
        ok_(get_field_type(gourmand_fields['firstname']) is CharField)
        ok_(get_field_type(gourmand_fields['favourite_dishes']) is ManyToManyField)
        ok_(gourmand_fields['favourite_dishes'].kwargs == {'value_type': Dish})
        ok_(get_field_type(gourmand_fields['pseudo']) is CharField)
        ok_(set(wsausage_fields) == set(['id', 'pk', 'lastname', 'firstname', 'nickname', 'name', 'greasiness']))
        ok_(get_field_type(journal_fields['name']) is CharField)
        ok_(get_field_type(journal_fields['journalist_set']) is ForeignRelatedObjectsDescriptor)
        ok_(journal_fields['journalist_set'].kwargs == {'value_type': Journalist})
        ok_(get_field_type(journal_fields['issue_set']) is ForeignRelatedObjectsDescriptor)
        ok_(journal_fields['issue_set'].kwargs == {'value_type': Issue})
        ok_(set(journal_fields) == set(['id', 'pk', 'name', 'journalist_set', 'issue_set']))
        ok_(get_field_type(dish_fields['name']) is CharField)
        ok_(get_field_type(dish_fields['gourmand_set']) is ManyRelatedObjectsDescriptor)
        ok_(dish_fields['gourmand_set'].kwargs == {'value_type': Gourmand})
        ok_(set(dish_fields) == set(['id', 'pk', 'name', 'gourmand_set']))

    def nk_test(self):
        """
        Test ModelMixin.extract_key
        """
        class ColumnistNode(ReadOnlyModelNode):
            klass = Columnist
            key_schema = ('firstname', 'lastname')
        ok_(ColumnistNode.extract_key({
            'firstname': 'Jamy',
            'lastname': 'Gourmaud',
            'journal': {'id': 806, 'name': "C'est pas sorcier"},
            'id': 7763,
            'column': 'truck',
        }) == {'firstname': 'Jamy', 'lastname': 'Gourmaud'})


class BaseModel(TestCase):
    
    def setUp(self):
        self.author = Author(firstname='John', lastname='Steinbeck', nickname='JS')
        self.book = Book(title='Grapes of Wrath', author=self.author, comments='great great great')
        self.foiegras = Dish(name='Foie gras')
        self.salmon = Dish(name='salmon')
        self.gourmand = Gourmand(pseudo='Taz', firstname='T', lastname='Aznicniev')
        self.journal = Journal(name="C'est pas sorcier") ; self.journal.save()
        self.issue = Issue(
            journal=self.journal,
            issue_date=datetime.date(year=1979, month=11, day=1),
            last_char_datetime=datetime.datetime(year=1979, month=10, day=29, hour=0, minute=12)) ; self.issue.save()
        self.journalist = Journalist(firstname='Fred', lastname='Courant', journal=self.journal)
        self.columnist = Columnist(firstname='Jamy', lastname='Gourmaud', journal=self.journal, column='truck')
        self.author.save()
        self.book.save()
        self.foiegras.save()
        self.salmon.save()
        self.gourmand.save()
        self.journal.save()
        self.journalist.save()
        self.columnist.save()

        self.serialize = serialize
        self.deserialize = deserialize

    def tearDown(self):
        self.author.delete()
        self.book.delete()
        self.foiegras.delete()
        self.salmon.delete()
        self.gourmand.delete()
        self.columnist.delete()
        self.journalist.delete()
        self.issue.delete()
        self.journal.delete()

class ModelToDict_Test(BaseModel):
    """
    Tests for ModelToDict
    """

    def call_test(self):
        """
        Simple test ModelToDict.call
        """
        self.assertEqual(self.serialize(self.author), {
            'id': self.author.pk,
            'pk': self.author.pk,
            'firstname': 'John',
            'lastname': 'Steinbeck',
            'nickname': 'JS'
        })

    def mti_test(self):
        """
        Test ModelToDict.call with a model with long inheritance chain.
        """
        ok_(self.serialize(self.columnist) == {
            'id': self.columnist.pk,
            'pk': self.columnist.pk,
            'firstname': 'Jamy',
            'lastname': 'Gourmaud',
            'journal': {'id': self.journal.pk, 'pk': self.journal.pk, 'name': "C'est pas sorcier"},
            'column': 'truck',
            'nickname': ''
        })

    def fk_test(self):
        """
        Test ModelToDict.call with foreignkeys
        """
        ok_(self.serialize(self.book) == {
            'id': self.book.pk,
            'pk': self.book.pk,
            'title': 'Grapes of Wrath',
            'author': {
                'id': self.author.pk,
                'pk': self.author.pk,
                'firstname': 'John',
                'lastname': 'Steinbeck',
                'nickname': 'JS'
            },
            'comments': 'great great great'
        })

    def many2many_test(self):
        """
        Test ModelToDict.call with many2many field.
        """
        ok_(self.serialize(self.gourmand) == {
            'id': self.gourmand.pk, 'pk': self.gourmand.pk, 
            'pseudo': 'Taz', 'favourite_dishes': [],
            'firstname': 'T', 'lastname': 'Aznicniev'
        })
        self.gourmand.favourite_dishes.add(self.salmon)
        self.gourmand.favourite_dishes.add(self.foiegras)
        self.gourmand.save()
        ok_(self.serialize(self.gourmand) == {
            'id': self.gourmand.pk, 'pk': self.gourmand.pk,
            'pseudo': 'Taz', 'firstname': 'T', 'lastname': 'Aznicniev',
            'favourite_dishes': [
                {'id': self.foiegras.pk, 'pk': self.foiegras.pk, 'name': 'Foie gras'},
                {'id': self.salmon.pk, 'pk': self.salmon.pk, 'name': 'salmon'},
            ]
        })

    def relatedmanager_test(self):
        """
        Test ModelToDict.call serializing a reverse relationship (fk, m2m).
        """
        # reverse ForeignKey
        class JournalistNode(CRUModelNode):
            klass = Journalist
            @classmethod
            def schema_dump(cls):
                return {
                    'firstname': str,
                    'lastname': str
                }
        class JournalNode(CRUModelNode):
            klass = Journal
            @classmethod
            def schema_dump(cls):
                schema = super(JournalNode, cls).schema_dump()
                return {
                    'name': schema['name'],
                    'journalist_set': QuerySetNode.get_subclass(value_type=JournalistNode)
                }
        ok_(serialize(self.journal, in_class=JournalNode) == {
            'journalist_set': [
                {'lastname': u'Courant', 'firstname': u'Fred'},
                {'lastname': u'Gourmaud', 'firstname': u'Jamy'}
            ],
            'name': "C'est pas sorcier"
        })
        # reverse m2m
        self.gourmand.favourite_dishes.add(self.salmon)
        self.gourmand.save()
        class GourmandNode(CRUModelNode):
            klass = Gourmand
            @classmethod
            def schema_dump(cls):
                return {'pseudo': str}
        class DishNode(CRUModelNode):
            klass = Dish
            include_related = True
            @classmethod
            def schema_dump(cls):
                schema = super(DishNode, cls).schema_dump()
                schema.pop('id', None)
                schema.pop('pk', None)
                schema['gourmand_set'] = QuerySetNode.get_subclass(value_type=GourmandNode)
                return schema
        ok_(serialize(self.salmon, in_class=DishNode) == {
            'gourmand_set': [
                {'pseudo': u'Taz'},
            ],
            'name': 'salmon'
        })

    def date_and_datetime_test(self):
        """
        Test ModelToDict.call serializing date and datetime
        """
        class JournalNode(CRUModelNode):
            klass = Journal
            @classmethod
            def schema_dump(cls):
                return {'name': str}

        class IssueNode(CRUModelNode):
            klass = Issue
            @classmethod
            def schema_dump(cls):
                schema = super(IssueNode, cls).schema_dump()
                return {
                    'journal': JournalNode,
                    'issue_date': schema['issue_date'],
                    'last_char_datetime': schema['last_char_datetime'],
                }

        ok_(self.serialize(self.issue, in_class=IssueNode) == {
            'journal': {'name': "C'est pas sorcier"},
            'issue_date': {'year': 1979, 'month': 11, 'day': 1},
            'last_char_datetime': {'year': 1979, 'month': 10, 'day': 29, 'hour': 0, 'minute': 12, 'second': 0, 'microsecond': 0},
        })

    def none_field_test(self):
        """
        Test serializing with a field that has a value of None instead of the expected
        """
        self.journalist.journal = None
        ok_(self.serialize(self.journalist) == {
            'pk': self.journalist.pk, 'id': self.journalist.id,
            'lastname': u'Courant', 'firstname': u'Fred', 'nickname': '',
            'journal': None
        })


class DictToModel_Test(BaseModel):
    """
    Tests for DictToModel
    """

    def call_test(self):
        """
        Simple test DictToModel.call
        """
        authors_before = Author.objects.count()
        james = self.deserialize({'firstname': 'James Graham', 'lastname': 'Ballard', 'nickname': 'JG Ballard'}, out_class=AuthorNode)
        james = Author.objects.get(pk=james.pk)
        # We check the fields
        ok_(james.firstname == 'James Graham')
        ok_(james.lastname == 'Ballard')
        ok_(james.nickname == 'JG Ballard')
        # We check that new author was created
        ok_(Author.objects.count() == authors_before + 1)
        james.delete()

    def update_object_with_fk_test(self):
        """
        Test deserialize already existing object with an already existing foreignkey 
        """
        authors_before = Author.objects.count()
        books_before = Book.objects.count()
        book = self.deserialize({
            'id': self.book.pk, 'title': 'In cold blood', 'comments': 'great great great',
            'author': {'id': self.author.pk, 'pk': self.author.pk, 'firstname': 'Truman', 'lastname': 'Capote'}, 
        }, out_class=UpdateOnlyBook)
        book = Book.objects.get(pk=book.pk)
        author = Author.objects.get(pk=book.author.pk)
        # We check the fields
        ok_(book.title == 'In cold blood')
        ok_(author.firstname == 'Truman')
        ok_(author.lastname == 'Capote')
        # We check that no item was created
        ok_(Book.objects.count() == books_before)
        ok_(Author.objects.count() == authors_before)

    def create_object_with_fk_auto_assign_pk_test(self):
        """
        Test deserialize new object with new foreignkey with automatically picked PK. 
        """
        authors_before = Author.objects.count()
        books_before = Book.objects.count()
        book = self.deserialize({
            'title': '1984', 'comments': 'great great great',
            'author': {'firstname': 'George', 'lastname': 'Orwell'}
        }, out_class=BookNode)
        book = Book.objects.get(pk=book.pk)
        author = Author.objects.get(firstname='George', lastname='Orwell')
        # We check the fields
        ok_(book.title == '1984')
        ok_(author.firstname == 'George')
        ok_(author.lastname == 'Orwell')
        # We check that items were created
        ok_(Book.objects.count() == books_before + 1)
        ok_(Author.objects.count() == authors_before + 1)
        # cleaning-up
        book.delete()
        author.delete()

    def create_object_with_fk_choose_pk_test(self):
        """
        Test deserialize new object with new foreignkey, PK provided. 
        """
        authors_before = Author.objects.count()
        books_before = Book.objects.count()
        book = self.deserialize({
            'id': 989, 'title': '1984', 'comments': 'great great great',
            'author': {'id': 76,'firstname': 'George', 'lastname': 'Orwell'}
        }, out_class=BookNode)
        book = Book.objects.get(pk=book.pk)
        author = Author.objects.get(firstname='George', lastname='Orwell')
        # We check the fields
        ok_(book.id == 989)
        ok_(book.title == '1984')
        ok_(author.id == 76)
        ok_(author.firstname == 'George')
        ok_(author.lastname == 'Orwell')
        # We check that items were created
        ok_(Book.objects.count() == books_before + 1)
        ok_(Author.objects.count() == authors_before + 1)
        # cleaning-up
        book.delete()
        author.delete()

    def update_object_with_m2m_already_existing_objects_test(self):
        """
        Test update object, update m2m field with existing FKs.
        """
        g_before = Gourmand.objects.count()
        d_before = Dish.objects.count()
        gourmand = self.deserialize({
            'id': self.gourmand.pk,
            'pseudo': 'Taaaaz',
            'favourite_dishes': [
                {'id': self.salmon.pk, 'name': 'Pretty much'},
                {'id': self.foiegras.pk, 'name': 'Anything'},
            ]
        }, out_class=UpdateOnlyGourmand)
        gourmand = Gourmand.objects.get(pk=gourmand.pk)
        salmon = Dish.objects.get(pk=self.salmon.pk)
        foiegras = Dish.objects.get(pk=self.foiegras.pk)
        # We check the fields
        ok_(set(gourmand.favourite_dishes.all()) == set([salmon, foiegras]))
        ok_(gourmand.pseudo == 'Taaaaz')
        ok_(salmon.name == u'Pretty much')
        ok_(foiegras.name == u'Anything')
        # We check that no item was created
        ok_(Gourmand.objects.count() == g_before)
        ok_(Dish.objects.count() == d_before)

    def update_object_with_m2m_new_objects_test(self):
        """
        Test update object, update m2m field with new FK.
        """
        g_before = Gourmand.objects.count()
        d_before = Dish.objects.count()
        gourmand = self.deserialize({
            'pseudo': 'Touz',
            'favourite_dishes': [
                {'id': 888, 'name': 'Vitamine O'},
                {'id': self.salmon.pk},
                {'id': self.foiegras.pk},
            ]
        }, out_class=GourmandNode)
        gourmand = Gourmand.objects.get(pk=gourmand.pk)
        vitamineo = Dish.objects.get(pk=888)
        # We check the fields
        ok_(set(gourmand.favourite_dishes.all()) == set([vitamineo, self.foiegras, self.salmon]))
        ok_(gourmand.pseudo == 'Touz')
        ok_(vitamineo.name == u'Vitamine O')
        # We check that items were created
        ok_(Gourmand.objects.count() == g_before + 1)
        ok_(Dish.objects.count() == d_before + 1)

    def update_relatedmanager_already_existing_objects_test(self):
        """
        Test DictToModel.call updating a reverse relationship (fk, m2m).
        """
        # reverse ForeignKey - only works if fk can be null
        journal = self.deserialize({
            'id': self.journal.id,
            'journalist_set': [],
        }, out_class=UpdateOnlyJournal)
        ok_(set(journal.journalist_set.all()) == set())
        journal = self.deserialize({
            'id': self.journal.id,
            'journalist_set': [
                {'id': self.journalist.id},
            ],
        }, out_class=UpdateOnlyJournal)
        ok_(set(journal.journalist_set.all()) == set([self.journalist]))
        # reverse m2m
        salmon = self.deserialize({
            'id': self.salmon.id,
            'gourmand_set': [
                {'id': self.gourmand.id},
            ]
        }, out_class=UpdateOnlyDish)
        ok_(set(salmon.gourmand_set.all()) == set([self.gourmand]))

    def update_object_with_nk_test(self):
        """
        Test update an object with its natural key, natural key already existing.
        """
        columnist_before = Columnist.objects.count()
        jamy = self.deserialize({
            'firstname': 'Jamy',
            'lastname': 'Gourmaud',
            'column': 'truck'
        }, out_class=UpdateOnlyColumnist)
        jamy = Columnist.objects.get(pk=jamy.pk)
        # We check the fields
        ok_(jamy.column == 'truck')
        # We check that no item was created
        ok_(columnist_before == Columnist.objects.count())

    def create_object_with_nk_test(self):
        """
        Test deserialize and create an object with its natural key.
        """
        columnist_before = Columnist.objects.count()
        fred = self.deserialize({
            'firstname': 'Frédéric',
            'lastname': 'Courant',
            'journal': {'id': self.journal.pk},
            'column': 'on the field',
        }, out_class=ColumnistNode)
        fred = Columnist.objects.get(pk=fred.pk)
        # We check the fields
        ok_(fred.column == 'on the field')
        # We check that items were created
        ok_(columnist_before + 1 == Columnist.objects.count())
        fred.delete()
    
    def update_date_and_datetime_test(self):
        """
        Test deserializing date and datetime
        """
        issue = self.deserialize({
            'id': self.issue.pk,
            'issue_date': {'year': 1865, 'month': 1, 'day': 1},
            'last_char_datetime': {'year': 1864, 'month': 12, 'day': 31, 'hour': 1},
        }, out_class=UpdateOnlyIssue)
        ok_(issue.issue_date == datetime.date(year=1865, month=1, day=1))
        ok_(issue.last_char_datetime == datetime.datetime(year=1864, month=12, day=31, hour=1))


if USES_GEODJANGO:
    from django.contrib.gis.geos import (Point, LineString,
    LinearRing, Polygon, MultiPoint, MultiLineString, MultiPolygon)

    class GeoDjango_Test(TestCase):
        """
        Test serialize and deserialize GeoDjango's geometry objects.
        """

        def setUp(self):
            self.serialize = serialize
            self.deserialize = deserialize

        def Point_serialize_test(self):
            """
            Test serialize Point
            """
            point = Point([1, 2, 3])
            ok_(self.serialize(point) == [1.0, 2.0, 3.0])
            point = Point([1, 2])
            ok_(self.serialize(point) == [1.0, 2.0])

        def Point_deserialize_test(self):
            """
            Test deserialize Point
            """
            point = self.deserialize([1, 2, 3], out_class=Point)
            ok_([point.x, point.y, point.z] == [1.0, 2.0, 3.0])
            point = self.deserialize([5.0, 2], out_class=Point)
            ok_([point.x, point.y, point.z] == [5.0, 2, None])

        def LineString_serialize_test(self):
            """
            Test serialize LineString
            """
            line = LineString([[1, 2, 3], [2, 7.0, 9.0], [3.0, 9.0, -6.8]])
            ok_(self.serialize(line) == [[1, 2, 3], [2, 7.0, 9.0], [3.0, 9.0, -6.8]])
            line = LineString(Point(-1, 7.9, 3), Point(3.0, 9.0, -77))
            ok_(self.serialize(line) == [[-1.0, 7.9, 3.0], [3.0, 9.0, -77.0]])

        def LineString_deserialize_test(self):
            """
            Test deserialize LineString
            """
            line = self.deserialize([[56.9, 2, 3], [2, 7.0, 8], [3.0, 9.0, -6.8], [156.9, 88, 0]], out_class=LineString)
            ok_(line == LineString(Point(56.9, 2, 3), Point(2, 7.0, 8), Point(3.0, 9.0, -6.8), Point(156.9, 88, 0)))
            line = deserialize([{'x': 5, 'y': -9.0}, {'x': 2, 'y': 7.0}], out_class=LineString)
            ok_(line == LineString(Point(5, -9.0), Point(2, 7.0)))

        def LinearRing_serialize_test(self):
            """
            Test serialize LinearRing
            """
            line = LinearRing([[99.7, 6, 4.7], [6.5, 0, 0], [55, 9, 0], [99.7, 6, 4.7]])
            ok_(self.serialize(line) == [[99.7, 6, 4.7], [6.5, 0, 0], [55, 9, 0], [99.7, 6, 4.7]])

        def LinearRing_deserialize_test(self):
            """
            Test deserialize LinearRing
            """
            line = self.deserialize([[8.9, 0], [8, 0], [8.6, 0], [8.9, 0]], out_class=LinearRing)
            ok_(line == LinearRing([[8.9, 0], [8, 0], [8.6, 0], [8.9, 0]]))

        def Polygon_serialize_test(self):
            """
            Test serialize Polygon
            """
            polygon = Polygon(LinearRing([[99.7, 6, 4.7], [6.5, 0, 0], [55, 9, 0], [99.7, 6, 4.7]]))
            ok_(self.serialize(polygon) == [[[99.7, 6, 4.7], [6.5, 0, 0], [55, 9, 0], [99.7, 6, 4.7]]])

        def Polygon_deserialize_test(self):
            """
            Test deserialize Polygon
            """
            line = self.deserialize([[[8.9, 0], [8, 0], [8.6, 0], [8.9, 0]]], out_class=Polygon)
            ok_(line == Polygon(LinearRing([[8.9, 0], [8, 0], [8.6, 0], [8.9, 0]])))

        def MultiPoint_serialize_test(self):
            """
            Test serialize MultiPoint
            """
            mpoint = MultiPoint(Point(1, 2), Point(2, 6, 8))
            ok_(self.serialize(mpoint) == [[1, 2], [2, 6, 8]])

        def MultiPoint_deserialize_test(self):
            """
            Test deserialize MultiPoint
            """
            line = self.deserialize([[0, 0], [1, 2, 8], [8.6, 0]], out_class=MultiPoint)
            ok_(line == MultiPoint(Point(0, 0), Point(1, 2, 8), Point(8.6, 0)))

        def MultiLineString_serialize_test(self):
            """
            Test serialize MultiLineString
            """
            mline = MultiLineString(
                LineString(Point(1, 2, 3), Point(2, 6, 8)),
                LineString(Point(0, 0), Point(6.9, 8))
            )
            ok_(self.serialize(mline) == [[[1, 2, 3], [2, 6, 8]], [[0, 0], [6.9, 8]]])

        def MultiLineString_deserialize_test(self):
            """
            Test deserialize MultiLineString
            """
            mline = self.deserialize([[[1, 2, 3], [2, 6, 8]], [[0, 0], [6.9, 8]]], out_class=MultiLineString)
            ok_(mline == MultiLineString(
                LineString(Point(1, 2, 3), Point(2, 6, 8)),
                LineString(Point(0, 0), Point(6.9, 8))
            ))

        def MultiPolygon_serialize_test(self):
            """
            Test serialize MultiPolygon
            """
            mpoly = MultiPolygon(
                Polygon(LinearRing(Point(1, 2, 3), Point(2, 6, 8), Point(2, 6, 10), Point(1, 2, 3))),
                Polygon(LinearRing(Point(0, 0), Point(2, 6), Point(2.5, 6), Point(0, 0)))
            )
            ok_(self.serialize(mpoly) == [
                [[[1, 2, 3], [2, 6, 8], [2, 6, 10], [1, 2, 3]]],
                [[[0, 0], [2, 6], [2.5, 6], [0, 0]]]
            ])

        def MultiPolygon_deserialize_test(self):
            """
            Test deserialize MultiPolygon
            """
            mpoly = self.deserialize([
                [[[1, 2, 3], [2, 6, 8], [2, 6, 10], [1, 2, 3]]],
                [[[0, 0], [2, 6], [2.5, 6], [0, 0]]]
            ], out_class=MultiPolygon)
            ok_(mpoly == MultiPolygon(
                Polygon(LinearRing(Point(1, 2, 3), Point(2, 6, 8), Point(2, 6, 10), Point(1, 2, 3))),
                Polygon(LinearRing(Point(0, 0), Point(2, 6), Point(2.5, 6), Point(0, 0)))
            ))
