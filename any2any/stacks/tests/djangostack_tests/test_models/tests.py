# -*- coding: utf-8 -*-

from django.db.models import AutoField, CharField, ForeignKey, Model
from django.db.models.fields.related import ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor
from django.db.models.manager import Manager
from django.http import QueryDict

from any2any.stacks.djangostack import *
from any2any import Wrapped
from models import *

from nose.tools import assert_raises, ok_

class WrappedModel_Test(object):

    def fields_test(self):
        """
        Test WrappedModel.default_schema
        """
        class WrappedColumnist(WrappedModel):
            klass = Columnist
        class WrappedGourmand(WrappedModel):
            klass = Gourmand
        class WrappedWritingSausage(WrappedModel):
            klass = WritingSausage
        class WrappedJournal(WrappedModel):
            klass = Journal
        class WrappedDish(WrappedModel):
            klass = Dish
        columnist_fields = WrappedColumnist.default_schema()
        gourmand_fields = WrappedGourmand.default_schema()
        wsausage_fields = WrappedWritingSausage.default_schema()
        journal_fields = WrappedJournal.default_schema()
        dish_fields = WrappedDish.default_schema()
        ok_(set(columnist_fields) == set(['id', 'pk', 'lastname', 'firstname', 'journal', 'column', 'nickname']))
        ok_(Wrapped.issubclass(columnist_fields['pk'], AutoField))
        ok_(Wrapped.issubclass(columnist_fields['id'], AutoField))
        ok_(Wrapped.issubclass(columnist_fields['lastname'], CharField))
        ok_(Wrapped.issubclass(columnist_fields['nickname'], CharField))
        ok_(Wrapped.issubclass(columnist_fields['journal'], ForeignKey))
        ok_(set(gourmand_fields) == set(['id', 'pk', 'lastname', 'firstname', 'favourite_dishes', 'pseudo']))
        ok_(Wrapped.issubclass(gourmand_fields['firstname'], CharField))
        ok_(Wrapped.issubclass(gourmand_fields['favourite_dishes'], ManyToManyField))
        ok_(Wrapped.issubclass(gourmand_fields['pseudo'], CharField))
        ok_(set(wsausage_fields) == set(['id', 'pk', 'lastname', 'firstname', 'nickname', 'name', 'greasiness']))
        ok_(Wrapped.issubclass(journal_fields['name'], CharField))
        ok_(Wrapped.issubclass(journal_fields['journalist_set'], ForeignRelatedObjectsDescriptor))
        ok_(Wrapped.issubclass(journal_fields['issue_set'], ForeignRelatedObjectsDescriptor))
        ok_(set(journal_fields) == set(['id', 'pk', 'name', 'journalist_set', 'issue_set']))
        ok_(Wrapped.issubclass(dish_fields['name'], CharField))
        ok_(Wrapped.issubclass(dish_fields['gourmand_set'], ManyRelatedObjectsDescriptor))
        ok_(set(dish_fields) == set(['id', 'pk', 'name', 'gourmand_set']))

    def nk_test(self):
        """
        Test WrappedModel.extract_key
        """
        class WrappedColumnist(WrappedModel):
            klass = Columnist
            key_schema = ('firstname', 'lastname')
        ok_(WrappedColumnist.extract_key({
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

        self.serializer = DjangoSerializer()
        self.deserializer = DjangoDeserializer()

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
        ok_(self.serializer(self.author) == {
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
        ok_(self.serializer(self.columnist) == {
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
        ok_(self.serializer(self.book) == {
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
        ok_(self.serializer(self.gourmand) == {
            'id': self.gourmand.pk, 'pk': self.gourmand.pk, 
            'pseudo': 'Taz', 'favourite_dishes': [],
            'firstname': 'T', 'lastname': 'Aznicniev'
        })
        self.gourmand.favourite_dishes.add(self.salmon)
        self.gourmand.favourite_dishes.add(self.foiegras)
        self.gourmand.save()
        ok_(self.serializer(self.gourmand) == {
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
        class WrappedJournalist(WrappedModel):
            klass = Journalist
            include = ['firstname', 'lastname']
        class WrappedJournal(WrappedModel):
            klass = Journal
            include = ['name', 'journalist_set']
        journalist_cast = ModelToDict(from_=WrappedJournalist)
        journal_cast = ModelToDict(from_=WrappedJournal)
        cast = DjangoSerializer(extra_mm_to_cast={
            Mm(from_any=Journalist): journalist_cast,
            Mm(from_any=Journal): journal_cast,
        })
        ok_(cast(self.journal) == {
            'journalist_set': [
                {'lastname': u'Courant', 'firstname': u'Fred'},
                {'lastname': u'Gourmaud', 'firstname': u'Jamy'}
            ],
            'name': "C'est pas sorcier"
        })
        # reverse m2m
        self.gourmand.favourite_dishes.add(self.salmon)
        self.gourmand.save()
        class WrappedGourmand(WrappedModel):
            klass = Gourmand
            include = ['pseudo']
        class WrappedDish(WrappedModel):
            klass = Dish
            exclude = ['id', 'pk']
            include_related = True
        gourmand_cast = ModelToDict(from_=WrappedGourmand)
        dish_cast = ModelToDict(from_=WrappedDish)
        cast = DjangoSerializer(extra_mm_to_cast={
            Mm(from_any=Gourmand): gourmand_cast,
            Mm(from_any=Dish): dish_cast,
        })
        ok_(cast(self.salmon) == {
            'gourmand_set': [
                {'pseudo': u'Taz'},
            ],
            'name': 'salmon'
        })

    def date_and_datetime_test(self):
        """
        Test ModelToDict.call serializing date and datetime
        """
        class WrappedJournal(WrappedModel):
            klass = Journal
            include = ['name']
        class WrappedIssue(WrappedModel):
            klass = Issue
            include=['journal', 'issue_date', 'last_char_datetime']
        journal_cast = ModelToDict(from_=WrappedJournal)
        issue_cast = ModelToDict(from_=WrappedIssue, key_to_cast={'journal': journal_cast})
        cast = DjangoSerializer(extra_mm_to_cast={Mm(from_any=Issue): issue_cast})
        ok_(cast(self.issue) == {
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
        james = self.deserializer({'firstname': 'James Graham', 'lastname': 'Ballard', 'nickname': 'JG Ballard'}, to=Author)
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
        book = self.deserializer({
            'id': self.book.pk, 'title': 'In cold blood', 'comments': 'great great great',
            'author': {'id': self.author.pk, 'pk': self.author.pk, 'firstname': 'Truman', 'lastname': 'Capote'}, 
        }, to=Book)
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
        book = self.deserializer({
            'title': '1984', 'comments': 'great great great',
            'author': {'firstname': 'George', 'lastname': 'Orwell'}
        }, to=Book)
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
        book = self.deserializer({
            'id': 989, 'title': '1984', 'comments': 'great great great',
            'author': {'id': 76,'firstname': 'George', 'lastname': 'Orwell'}
        }, to=Book)
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
        gourmand = self.deserializer({
            'id': self.gourmand.pk,
            'pseudo': 'Taaaaz',
            'favourite_dishes': [
                {'id': self.salmon.pk, 'name': 'Pretty much'},
                {'id': self.foiegras.pk, 'name': 'Anything'},
            ]
        }, to=Gourmand)
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
        gourmand = self.deserializer({
            'pseudo': 'Touz',
            'favourite_dishes': [
                {'id': 888, 'name': 'Vitamine O'},
                {'id': self.salmon.pk},
                {'id': self.foiegras.pk},
            ]
        }, to=Gourmand)
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
        class WrappedJournal(WrappedModel):
            klass = Journal
            include_related = True
        journal = self.deserializer({
            'id': self.journal.id,
            'journalist_set': [],
        }, to=WrappedJournal)
        ok_(set(journal.journalist_set.all()) == set())
        journal = self.deserializer({
            'id': self.journal.id,
            'journalist_set': [
                {'id': self.journalist.id},
            ],
        }, to=WrappedJournal)
        ok_(set(journal.journalist_set.all()) == set([self.journalist]))
        # reverse m2m
        class WrappedDish(WrappedModel):
            klass = Dish
            include_related = True
        salmon = self.deserializer({
            'id': self.salmon.id,
            'gourmand_set': [
                {'id': self.gourmand.id},
            ]
        }, to=WrappedDish)
        ok_(set(salmon.gourmand_set.all()) == set([self.gourmand]))

    def update_object_with_nk_test(self):
        """
        Test update an object with its natural key, natural key already existing.
        """
        class WrappedColumnist(WrappedModel):
            klass = Columnist
            key_schema = ('firstname', 'lastname')
        columnist_before = Columnist.objects.count()
        jamy = self.deserializer({
            'firstname': 'Jamy',
            'lastname': 'Gourmaud',
            'column': 'truck'
        }, to=WrappedColumnist)
        jamy = Columnist.objects.get(pk=jamy.pk)
        # We check the fields
        ok_(jamy.column == 'truck')
        # We check that no item was created
        ok_(columnist_before == Columnist.objects.count())

    def create_object_with_nk_test(self):
        """
        Test deserialize and create an object with its natural key.
        """
        class WrappedColumnist(WrappedModel):
            klass = Columnist
            key_schema = ('firstname', 'lastname')
        columnist_before = Columnist.objects.count()
        fred = self.deserializer({
            'firstname': 'Frédéric',
            'lastname': 'Courant',
            'journal': {'id': self.journal.pk},
            'column': 'on the field',
        }, to=WrappedColumnist)
        fred = Columnist.objects.get(pk=fred.pk)
        # We check the fields
        ok_(fred.column == 'on the field')
        # We check that items were created
        ok_(columnist_before + 1 == Columnist.objects.count())
        fred.delete()
    
    def update_date_and_datetime_test(self):
        """
        Test ModelToDict.call serializing date and datetime
        """
        issue = self.deserializer({
            'id': self.issue.pk,
            'issue_date': {'year': 1865, 'month': 1, 'day': 1},
            'last_char_datetime': {'year': 1864, 'month': 12, 'day': 31, 'hour': 1},
        }, to=Issue)
        ok_(issue.issue_date == datetime.date(year=1865, month=1, day=1))
        ok_(issue.last_char_datetime == datetime.datetime(year=1864, month=12, day=31, hour=1))

class QueryDictFlatener_Test(object):
    """
    Tests for QueryDictFlatener
    """

    def setUp(self):
        self.serializer = DjangoSerializer()
        self.deserializer = DjangoDeserializer()

    def call_test(self):
        """
        Test QueryDictFlatener.call
        """
        class MyWrappedQueryDict(WrappedQueryDict):
            list_keys = ['a_list']
        ok_(self.serializer(QueryDict('a_list=1&a_list=2&a_normal_key=1&a_normal_key=2&a_normal_key=3'), to=MyWrappedQueryDict) == {
            'a_list': ['1', '2'],
            'a_normal_key': '1',
        })
        
    def call_with_model_test(self):
        """
        Test QueryDictFlatener.call configured for a model
        """
        class MyWrappedQueryDict(WrappedQueryDict):
            model = Gourmand
        ok_(self.serializer(QueryDict('favourite_dishes=1&favourite_dishes=2&pseudo=Taz&pseudo=Touz'), to=MyWrappedQueryDict) == {
            'favourite_dishes': ['1', '2'],
            'pseudo': 'Taz',
        })

    def call_with_model_and_empty_list_test(self):
        """
        Test QueryDictFlatener.call configured for a model
        """
        class MyWrappedQueryDict(WrappedQueryDict):
            model = Gourmand
        # Test that life is sad
        ok_(self.serializer(QueryDict('favourite_dishes='), to=MyWrappedQueryDict) == {
            'favourite_dishes': [''],
        })
        # Test that with our cast it is much brighter
        qd_cast = QueryDictFlatener(mm_to_cast={
            Mm(list, list): StripEmptyValues(empty_value='EMPTY')
        })
        cast = DjangoSerializer(mm_to_cast={
            Mm(QueryDict): qd_cast
        })
        ok_(cast(QueryDict('favourite_dishes=EMPTY'), to=MyWrappedQueryDict) == {
            'favourite_dishes': [],
        })

donttest="""

.. currentmodule:: spiteat.djangosrz

This module contains a serializer :class:`ModelSrz` for your Django models. This serializer features :

    - Deep serialization. Foreign keys, and foreign keys of foreign keys, and so on ... are completely serialized.
    - Support multi-table inheritance. All attributes from parent models can be serialized.


Content type - GenericForeignKey
----------------------------------

    >>> bookmark = Bookmark(name='favourite', to=foiegras)

    >>> bookmark_srz = ModelSrz(custom_for=Bookmark, include=['to', 'pk'])
    >>> bookmark = bookmark_srz.eat({'pk': bookmark.pk, 'to': ('test_models', 'dish', salmon.pk)})
    >>> bookmark.to == salmon
    True

    >>> bookmark_srz.spit(bookmark) == {'to': ('test_models', 'dish', salmon.pk), 'pk': bookmark.pk}
    True

"""
