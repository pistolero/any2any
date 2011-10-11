# -*- coding: utf-8 -*-

from django.db.models import AutoField, CharField, ForeignKey, Model
from django.db.models.fields.related import ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor
from django.db.models.manager import Manager
from django.http import QueryDict

from any2any.stacks.djangostack import *
from any2any import Wrap
from models import *

from nose.tools import assert_raises, ok_

class ModelWrap_Test(object):

    def fields_test(self):
        """
        Test ModelWrap.default_schema
        """
        columnist_fields = ModelWrap(klass=Columnist).default_schema()
        gourmand_fields = ModelWrap(klass=Gourmand).default_schema()
        wsausage_fields = ModelWrap(klass=WritingSausage).default_schema()
        journal_fields = ModelWrap(klass=Journal).default_schema()
        dish_fields = ModelWrap(klass=Dish).default_schema()
        ok_(set(columnist_fields) == set(['id', 'lastname', 'firstname', 'journal', 'column', 'nickname']))
        ok_(Wrap.issubclass(columnist_fields['id'], AutoField))
        ok_(Wrap.issubclass(columnist_fields['lastname'], CharField))
        ok_(Wrap.issubclass(columnist_fields['nickname'], CharField))
        ok_(Wrap.issubclass(columnist_fields['journal'], ForeignKey))
        ok_(set(gourmand_fields) == set(['id', 'lastname', 'firstname', 'favourite_dishes', 'pseudo']))
        ok_(Wrap.issubclass(gourmand_fields['firstname'], CharField))
        ok_(Wrap.issubclass(gourmand_fields['favourite_dishes'], ManyToManyField))
        ok_(Wrap.issubclass(gourmand_fields['pseudo'], CharField))
        ok_(set(wsausage_fields) == set(['id', 'lastname', 'firstname', 'nickname', 'name', 'greasiness']))
        ok_(Wrap.issubclass(journal_fields['name'], CharField))
        ok_(Wrap.issubclass(journal_fields['journalist_set'], ForeignRelatedObjectsDescriptor))
        ok_(Wrap.issubclass(journal_fields['issue_set'], ForeignRelatedObjectsDescriptor))
        ok_(set(journal_fields) == set(['id', 'name', 'journalist_set', 'issue_set']))
        ok_(Wrap.issubclass(dish_fields['name'], CharField))
        ok_(Wrap.issubclass(dish_fields['gourmand_set'], ManyRelatedObjectsDescriptor))
        ok_(set(dish_fields) == set(['id', 'name', 'gourmand_set']))

    def nk_test(self):
        """
        Test ModelWrap.extract_pk
        """
        columnist_type = ModelWrap(klass=Columnist, key_schema=('firstname', 'lastname'))
        ok_(columnist_type.extract_pk({
            'firstname': 'Jamy',
            'lastname': 'Gourmaud',
            'journal': {'id': 806, 'name': "C'est pas sorcier"},
            'id': 7763,
            'column': 'truck',
        }) == ('Jamy', 'Gourmaud'))

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

        self.cast = DjangoStack()

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

class ModelToMapping_Test(BaseModel):
    """
    Tests for ModelToMapping
    """

    def call_test(self):
        """
        Simple test ModelToMapping.call
        """
        ok_(self.cast.call(self.author) == {'firstname': 'John', 'lastname': 'Steinbeck', 'id': self.author.pk, 'nickname': 'JS'})

    def mti_test(self):
        """
        Test ModelToMapping.call with a model with long inheritance chain.
        """
        ok_(self.cast.call(self.columnist) == {
            'firstname': 'Jamy',
            'lastname': 'Gourmaud',
            'journal': {'id': self.journal.pk, 'name': "C'est pas sorcier"},
            'id': self.columnist.pk,
            'column': 'truck',
            'nickname': ''
        })

    def fk_test(self):
        """
        Test ModelToMapping.call with foreignkeys
        """
        ok_(self.cast.call(self.book) == {
            'id': self.book.pk,
            'title': 'Grapes of Wrath',
            'author': {
                'id': self.author.pk,
                'firstname': 'John',
                'lastname': 'Steinbeck',
                'nickname': 'JS'
            },
            'comments': 'great great great'
        })

    def many2many_test(self):
        """
        Test ModelToMapping.call with many2many field.
        """
        ok_(self.cast.call(self.gourmand) == {
            'id': self.gourmand.pk, 'pseudo': 'Taz', 'favourite_dishes': [],
            'firstname': 'T', 'lastname': 'Aznicniev'
        })
        self.gourmand.favourite_dishes.add(self.salmon)
        self.gourmand.favourite_dishes.add(self.foiegras)
        self.gourmand.save()
        ok_(self.cast.call(self.gourmand) == {
            'id': self.gourmand.pk, 'pseudo': 'Taz', 'firstname': 'T', 'lastname': 'Aznicniev',
            'favourite_dishes': [
                {'id': self.foiegras.pk, 'name': 'Foie gras'},
                {'id': self.salmon.pk, 'name': 'salmon'},
            ]
        })

    def relatedmanager_test(self):
        """
        Test ModelToMapping.call serializing a reverse relationship (fk, m2m).
        """
        # reverse ForeignKey
        journalist_type = ModelWrap(klass=Journalist, include=['firstname', 'lastname'])
        journal_type = ModelWrap(klass=Journal,
            include=['name', 'journalist_set'],
            key_schema=('firstname', 'lastname')
        )
        journalist_cast = ModelToMapping(from_=journalist_type, to=dict)
        journal_cast = ModelToMapping(from_=journal_type, to=dict)
        cast = DjangoStack(extra_mm_to_cast={
            Mm(from_any=Journalist): journalist_cast,
            Mm(from_any=Journal): journal_cast,
        })
        ok_(cast.call(self.journal) == {
            'journalist_set': [
                {'lastname': u'Courant', 'firstname': u'Fred'},
                {'lastname': u'Gourmaud', 'firstname': u'Jamy'}
            ],
            'name': "C'est pas sorcier"
        })
        # reverse m2m
        self.gourmand.favourite_dishes.add(self.salmon)
        self.gourmand.save()
        gourmand_type = ModelWrap(klass=Gourmand, include=['pseudo'])
        dish_type = ModelWrap(klass=Dish, exclude=['id'], include_related=True)
        gourmand_cast = ModelToMapping(from_=gourmand_type, to=dict)
        dish_cast = ModelToMapping(from_=dish_type, to=dict)
        cast = DjangoStack(extra_mm_to_cast={
            Mm(from_any=Gourmand): gourmand_cast,
            Mm(from_any=Dish): dish_cast,
        })
        ok_(cast.call(self.salmon) == {
            'gourmand_set': [
                {'pseudo': u'Taz'},
            ],
            'name': 'salmon'
        })

    def date_and_datetime_test(self):
        """
        Test ModelToMapping.call serializing date and datetime
        """
        issue_type = ModelWrap(klass=Issue, include=['journal', 'issue_date', 'last_char_datetime'])
        journal_type = ModelWrap(klass=Journal, include=['name'])
        journal_cast = ModelToMapping(from_=journal_type, to=dict)
        issue_cast = ModelToMapping(from_=issue_type, to=dict, key_to_cast={'journal': journal_cast})
        cast = DjangoStack(extra_mm_to_cast={Mm(from_any=Issue): issue_cast})
        ok_(cast.call(self.issue) == {
            'journal': {'name': "C'est pas sorcier"},
            'issue_date': {'year': 1979, 'month': 11, 'day': 1},
            'last_char_datetime': {'year': 1979, 'month': 10, 'day': 29, 'hour': 0, 'minute': 12, 'second': 0, 'microsecond': 0},
        })

class MappingToModel_Test(BaseModel):
    """
    Tests for MappingToModel
    """

    def call_test(self):
        """
        Simple test MappingToModel.call
        """
        authors_before = Author.objects.count()
        james = self.cast.call({'firstname': 'James Graham', 'lastname': 'Ballard', 'nickname': 'JG Ballard'}, to=Author)
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
        book = self.cast.call({
            'id': self.book.pk, 'title': 'In cold blood', 'comments': 'great great great',
            'author': {'id': self.author.pk, 'firstname': 'Truman', 'lastname': 'Capote'}, 
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
        book = self.cast.call({
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
        book = self.cast.call({
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
        gourmand = self.cast.call({
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
        gourmand = self.cast.call({
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
        Test MappingToModel.call updating a reverse relationship (fk, m2m).
        """
        # reverse ForeignKey - only works if fk can be null
        journal_type = ModelWrap(klass=Journal, include_related=True)
        journal = self.cast.call({
            'id': self.journal.id,
            'journalist_set': [],
        }, to=journal_type)
        ok_(set(journal.journalist_set.all()) == set())
        journal = self.cast.call({
            'id': self.journal.id,
            'journalist_set': [
                {'id': self.journalist.id},
            ],
        }, to=journal_type)
        ok_(set(journal.journalist_set.all()) == set([self.journalist]))
        # reverse m2m
        dish_type = ModelWrap(klass=Dish, include_related=True)
        salmon = self.cast.call({
            'id': self.salmon.id,
            'gourmand_set': [
                {'id': self.gourmand.id},
            ]
        }, to=dish_type)
        ok_(set(salmon.gourmand_set.all()) == set([self.gourmand]))

    def update_object_with_nk_test(self):
        """
        Test update an object with its natural key, natural key already existing.
        """
        columnist_before = Columnist.objects.count()
        columnist_type = ModelWrap(klass=Columnist, key_schema=('firstname', 'lastname'))
        jamy = self.cast.call({
            'firstname': 'Jamy',
            'lastname': 'Gourmaud',
            'column': 'truck'
        }, to=columnist_type)
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
        columnist_type = ModelWrap(klass=Columnist, key_schema=('firstname', 'lastname'))
        fred = self.cast.call({
            'firstname': 'Frédéric',
            'lastname': 'Courant',
            'journal': {'id': self.journal.pk},
            'column': 'on the field',
        }, to=columnist_type)
        fred = Columnist.objects.get(pk=fred.pk)
        # We check the fields
        ok_(fred.column == 'on the field')
        # We check that items were created
        ok_(columnist_before + 1 == Columnist.objects.count())
        fred.delete()
    
    def update_date_and_datetime_test(self):
        """
        Test ModelToMapping.call serializing date and datetime
        """
        issue = self.cast.call({
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
        self.cast = DjangoStack()

    def call_test(self):
        """
        Test QueryDictFlatener.call
        """
        WrappedQueryDict = QueryDictWrap(list_keys=['a_list'])
        ok_(self.cast(QueryDict('a_list=1&a_list=2&a_normal_key=1&a_normal_key=2&a_normal_key=3'), to=WrappedQueryDict) == {
            'a_list': ['1', '2'],
            'a_normal_key': '1',
        })
        
    def call_with_model_test(self):
        """
        Test QueryDictFlatener.call configured for a model
        """
        WrappedQueryDict = QueryDictWrap(model=Gourmand)
        ok_(self.cast(QueryDict('favourite_dishes=1&favourite_dishes=2&pseudo=Taz&pseudo=Touz'), to=WrappedQueryDict) == {
            'favourite_dishes': ['1', '2'],
            'pseudo': 'Taz',
        })

    def call_with_model_and_empty_list_test(self):
        """
        Test QueryDictFlatener.call configured for a model
        """
        WrappedQueryDict = QueryDictWrap(model=Gourmand)
        # Test that life is sad
        ok_(self.cast(QueryDict('favourite_dishes='), to=WrappedQueryDict) == {
            'favourite_dishes': [''],
        })
        # Test that with our cast it is much brighter
        qd_cast = QueryDictFlatener(mm_to_cast={
            Mm(list, list): StripEmptyValues(empty_value='EMPTY')
        })
        cast = DjangoStack(mm_to_cast={
            Mm(QueryDict): qd_cast
        })
        ok_(cast(QueryDict('favourite_dishes=EMPTY'), to=WrappedQueryDict) == {
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
