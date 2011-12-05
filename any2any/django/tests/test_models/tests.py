# -*- coding: utf-8 -*-

from django.db.models import AutoField, CharField, ForeignKey, Model
from django.db.models.fields.related import ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor
from django.db.models.manager import Manager
from django.http import QueryDict

from any2any import *
from any2any.django.bundle import *
from models import *

from nose.tools import assert_raises, ok_


class AuthorBundle(CRUModelBundle):
    klass = Author

class BookBundle(CRUModelBundle):
    klass = Book
    schema = {'author': AuthorBundle}

class UpdateOnlyGourmand(UpdateOnlyModelBundle):
    klass = Gourmand

class UpdateOnlyGourmandQuerySet(QuerySetBundle):
    value_type = UpdateOnlyGourmand

class UpdateOnlyDish(UpdateOnlyModelBundle):
    klass = Dish
    schema = {'gourmand_set': UpdateOnlyGourmandQuerySet}

class DishBundle(CRUModelBundle):
    klass = Dish

class UpdateOnlyDishQuerySet(QuerySetBundle):
    value_type = UpdateOnlyDish

class DishQuerySet(QuerySetBundle):
    value_type = DishBundle

class GourmandBundle(CRUModelBundle):
    klass = Gourmand
    schema = {'favourite_dishes': DishQuerySet}

class UpdateOnlyGourmand(UpdateOnlyModelBundle):
    klass = Gourmand
    schema = {'favourite_dishes': UpdateOnlyDishQuerySet}

class UpdateOnlyAuthor(UpdateOnlyModelBundle):
    klass = Author

class UpdateOnlyBook(UpdateOnlyModelBundle):
    klass = Book
    schema = {'author': UpdateOnlyAuthor}

class UpdateOnlyJournalist(UpdateOnlyModelBundle):
    klass = Journalist

class UpdateOnlyJournalistQuerySet(QuerySetBundle):
    value_type = UpdateOnlyJournalist

class UpdateOnlyJournal(UpdateOnlyModelBundle):
    klass = Journal
    schema = {'journalist_set': UpdateOnlyJournalistQuerySet}

class UpdateOnlyColumnist(UpdateOnlyModelBundle):
    klass = Columnist
    key_schema = ('firstname', 'lastname')

class ColumnistBundle(CRUModelBundle):
    klass = Columnist
    key_schema = ('firstname', 'lastname')

class UpdateOnlyIssue(UpdateOnlyModelBundle):
    klass = Issue


class ModelMixin_Test(object):
    """
    Test ModelMixin, base of all ModelBundles
    """

    def fields_test(self):
        """
        Test ModelMixin.default_schema
        """
        class ColumnistBundle(ReadOnlyModelBundle):
            klass = Columnist
        class GourmandBundle(ReadOnlyModelBundle):
            klass = Gourmand
        class WritingSausageBundle(ReadOnlyModelBundle):
            klass = WritingSausage
        class JournalBundle(ReadOnlyModelBundle):
            klass = Journal
        class DishBundle(ReadOnlyModelBundle):
            klass = Dish
        columnist_fields = ColumnistBundle.default_schema()
        gourmand_fields = GourmandBundle.default_schema()
        wsausage_fields = WritingSausageBundle.default_schema()
        journal_fields = JournalBundle.default_schema()
        dish_fields = DishBundle.default_schema()
        ok_(set(columnist_fields) == set(['id', 'pk', 'lastname', 'firstname', 'journal', 'column', 'nickname']))
        ok_(columnist_fields['pk'].lookup_with[0] is AutoField)
        ok_(columnist_fields['id'].lookup_with[0] is AutoField)
        ok_(columnist_fields['lastname'].lookup_with[0] is CharField)
        ok_(columnist_fields['nickname'].lookup_with[0] is CharField)
        ok_(columnist_fields['journal'].lookup_with == (ForeignKey, Journal))
        ok_(set(gourmand_fields) == set(['id', 'pk', 'lastname', 'firstname', 'favourite_dishes', 'pseudo']))
        ok_(gourmand_fields['firstname'].lookup_with[0] is CharField)
        ok_(gourmand_fields['favourite_dishes'].lookup_with[0] is ManyToManyField)
        ok_(gourmand_fields['favourite_dishes']._schema == {Bundle.KeyAny: Dish})
        ok_(gourmand_fields['pseudo'].lookup_with[0] is CharField)
        ok_(set(wsausage_fields) == set(['id', 'pk', 'lastname', 'firstname', 'nickname', 'name', 'greasiness']))
        ok_(journal_fields['name'].lookup_with[0] is CharField)
        ok_(journal_fields['journalist_set'].lookup_with[0] is ForeignRelatedObjectsDescriptor)
        ok_(journal_fields['journalist_set']._schema == {Bundle.KeyAny: Journalist})
        ok_(journal_fields['issue_set'].lookup_with[0] is ForeignRelatedObjectsDescriptor)
        ok_(journal_fields['issue_set']._schema == {Bundle.KeyAny: Issue})
        ok_(set(journal_fields) == set(['id', 'pk', 'name', 'journalist_set', 'issue_set']))
        ok_(dish_fields['name'].lookup_with[0] is CharField)
        ok_(dish_fields['gourmand_set'].lookup_with[0] is ManyRelatedObjectsDescriptor)
        ok_(dish_fields['gourmand_set']._schema == {Bundle.KeyAny: Gourmand})
        ok_(set(dish_fields) == set(['id', 'pk', 'name', 'gourmand_set']))

    def nk_test(self):
        """
        Test ModelMixin.extract_key
        """
        class ColumnistBundle(ReadOnlyModelBundle):
            klass = Columnist
            key_schema = ('firstname', 'lastname')
        ok_(ColumnistBundle.extract_key({
            'firstname': 'Jamy',
            'lastname': 'Gourmaud',
            'journal': {'id': 806, 'name': "C'est pas sorcier"},
            'id': 7763,
            'column': 'truck',
        }) == {'firstname': 'Jamy', 'lastname': 'Gourmaud'})


class BaseModel(object):
    
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
        ok_(self.serialize(self.author) == {
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
        class JournalistBundle(CRUModelBundle):
            klass = Journalist
            include = ['firstname', 'lastname']
        class JournalBundle(CRUModelBundle):
            klass = Journal
            include = ['name', 'journalist_set']
            schema = {
                'journalist_set': QuerySetBundle.get_subclass(value_type=JournalistBundle)
            }
        ok_(serialize(self.journal, in_class=JournalBundle) == {
            'journalist_set': [
                {'lastname': u'Courant', 'firstname': u'Fred'},
                {'lastname': u'Gourmaud', 'firstname': u'Jamy'}
            ],
            'name': "C'est pas sorcier"
        })
        # reverse m2m
        self.gourmand.favourite_dishes.add(self.salmon)
        self.gourmand.save()
        class GourmandBundle(CRUModelBundle):
            klass = Gourmand
            include = ['pseudo']
        class DishBundle(CRUModelBundle):
            klass = Dish
            exclude = ['id', 'pk']
            include_related = True
            schema = {'gourmand_set': QuerySetBundle.get_subclass(value_type=GourmandBundle)}
        ok_(serialize(self.salmon, in_class=DishBundle) == {
            'gourmand_set': [
                {'pseudo': u'Taz'},
            ],
            'name': 'salmon'
        })

    def date_and_datetime_test(self):
        """
        Test ModelToDict.call serializing date and datetime
        """
        class JournalBundle(CRUModelBundle):
            klass = Journal
            include = ['name']
        class IssueBundle(CRUModelBundle):
            klass = Issue
            include = ['journal', 'issue_date', 'last_char_datetime']
            schema = {
                'journal': JournalBundle
            }
        ok_(self.serialize(self.issue, in_class=IssueBundle) == {
            'journal': {'name': "C'est pas sorcier"},
            'issue_date': {'year': 1979, 'month': 11, 'day': 1},
            'last_char_datetime': {'year': 1979, 'month': 10, 'day': 29, 'hour': 0, 'minute': 12, 'second': 0, 'microsecond': 0},
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
        james = self.deserialize({'firstname': 'James Graham', 'lastname': 'Ballard', 'nickname': 'JG Ballard'}, out_class=AuthorBundle)
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
        }, out_class=BookBundle)
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
        }, out_class=BookBundle)
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
        }, out_class=GourmandBundle)
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
        }, out_class=ColumnistBundle)
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

    class GeoDjango_Test(object):
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
            def build_point(pdict):
                return Point(pdict['x'], pdict['y'], pdict.get('z'))
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
