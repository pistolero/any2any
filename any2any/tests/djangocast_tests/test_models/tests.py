# coding=utf-8

from django.db.models import AutoField, CharField, ForeignKey, Model
from django.db.models.manager import Manager

from any2any.djangocast import *
from models import *

from nose.tools import assert_raises, ok_

class IntrospectMixin_Test(object):
    
    def setUp(self):
        # hack to have a model
        class Introspect(IntrospectMixin):
            defaults = CastSettings(
                model = Columnist
            )
            def call(self): pass
            def get_model(self):
                return self.model
        self.columnist_introspector = Introspect(model=Columnist)
        self.gourmand_introspector = Introspect(model=Gourmand)
        self.wsausage_introspector = Introspect(model=WritingSausage)

    def fields_test(self):
        """
        Test IntrospectMixin.fields
        """
        columnist_fields = self.columnist_introspector.fields
        gourmand_fields = self.gourmand_introspector.fields
        wsausage_fields = self.wsausage_introspector.fields
        ok_(set(columnist_fields) == set(['id', 'lastname', 'firstname', 'journal', 'column', 'nickname']))
        ok_(isinstance(columnist_fields['id'], AutoField))
        ok_(isinstance(columnist_fields['lastname'], CharField))
        ok_(isinstance(columnist_fields['nickname'], CharField))
        ok_(isinstance(columnist_fields['journal'], ForeignKey))
        ok_(set(gourmand_fields) == set(['id', 'lastname', 'firstname', 'favourite_dishes', 'pseudo']))
        ok_(isinstance(gourmand_fields['firstname'], CharField))
        ok_(isinstance(gourmand_fields['favourite_dishes'], ManyToManyField))
        ok_(isinstance(gourmand_fields['pseudo'], CharField))
        ok_(set(wsausage_fields) == set(['id', 'lastname', 'firstname', 'nickname', 'name', 'greasiness']))

    def nk_test(self):
        self.columnist_introspector.settings['key_schema'] = ('firstname', 'lastname')
        ok_(self.columnist_introspector.extract_pk({
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
        cast = ModelToDict()
        ok_(cast.call(self.author) == {'firstname': 'John', 'lastname': 'Steinbeck', 'id': self.author.pk, 'nickname': 'JS'})

    def mti_test(self):
        """
        Test ModelToDict.call with a model with long inheritance chain.
        """
        cast = ModelToDict()
        ok_(cast.call(self.columnist) == {
            'firstname': 'Jamy',
            'lastname': 'Gourmaud',
            'journal': {'id': self.journal.pk, 'name': "C'est pas sorcier"},
            'id': self.columnist.pk,
            'column': 'truck',
            'nickname': ''
        })

    def fk_test(self):
        """
        Test ModelToDict.call with foreignkeys
        """
        cast = ModelToDict()
        ok_(cast.call(self.book) == {
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
        Test ModelToDict.call with many2many field.
        """
        cast = ModelToDict()
        ok_(cast.call(self.gourmand) == {
            'id': self.gourmand.pk, 'pseudo': 'Taz', 'favourite_dishes': [],
            'firstname': 'T', 'lastname': 'Aznicniev'
        })
        self.gourmand.favourite_dishes.add(self.salmon)
        self.gourmand.favourite_dishes.add(self.foiegras)
        self.gourmand.save()
        ok_(cast.call(self.gourmand) == {
            'id': self.gourmand.pk, 'pseudo': 'Taz', 'firstname': 'T', 'lastname': 'Aznicniev',
            'favourite_dishes': [
                {'id': self.foiegras.pk, 'name': 'Foie gras'},
                {'id': self.salmon.pk, 'name': 'salmon'},
            ]
        })

    def relatedmanager_test(self):
        """
        Test ModelToDict.call serializing a reverse relationship (fk, m2m).
        """
        journalist_cast = ModelToDict(include=['firstname', 'lastname'])
        cast = ModelToDict(include_extra=['journalist_set'], exclude=['id'], mm_to_cast={Mm(Journalist, dict): journalist_cast})
        ok_(cast.call(self.journal) == {
            'journalist_set': [
                {'lastname': u'Courant', 'firstname': u'Fred'},
                {'lastname': u'Gourmaud', 'firstname': u'Jamy'}
            ],
            'name': "C'est pas sorcier"
        })

        self.gourmand.favourite_dishes.add(self.salmon)
        self.gourmand.save()
        gourmand_cast = ModelToDict(include=['pseudo'])
        cast = ModelToDict(include=['gourmand_set', 'name'], mm_to_cast={Mm(Gourmand, dict): gourmand_cast})
        ok_(cast.call(self.salmon) == {
            'gourmand_set': [
                {'pseudo': u'Taz'},
            ],
            'name': 'salmon'
        })

    def date_and_datetime_test(self):
        """
        Test ModelToDict.call serializing date and datetime
        """
        journal_cast = ModelToDict(include=['name'])
        cast = ModelToDict(exclude=['id'], key_to_cast={'journal': journal_cast})
        ok_(cast.call(self.issue) == {
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
        cast = DictToModel(to=Author)
        authors_before = Author.objects.count()
        james = cast.call({'firstname': 'James Graham', 'lastname': 'Ballard', 'nickname': 'JC Ballard'})
        james = Author.objects.get(pk = james.pk)
        # We check the fields
        ok_(james.firstname == 'James Graham')
        ok_(james.lastname == 'Ballard')
        ok_(james.nickname == 'JC Ballard')
        # We check that new author was created
        ok_(Author.objects.count() == authors_before + 1)
        james.delete()

    def update_object_with_fk_test(self):
        """
        Test deserialize already existing object with an already existing foreignkey 
        """
        book_cast = DictToModel(to=Book)
        authors_before = Author.objects.count()
        books_before = Book.objects.count()
        book = book_cast.call({
            'id': self.book.pk, 'title': 'In cold blood', 'comments': 'great great great',
            'author': {'id': self.author.pk, 'firstname': 'Truman', 'lastname': 'Capote'}, 
        })
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
        book_cast = DictToModel(to=Book)
        authors_before = Author.objects.count()
        books_before = Book.objects.count()
        book = book_cast.call({
            'title': '1984', 'comments': 'great great great',
            'author': {'firstname': 'George', 'lastname': 'Orwell'}
        })
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
        book_cast = DictToModel(to=Book)
        authors_before = Author.objects.count()
        books_before = Book.objects.count()
        book = book_cast.call({
            'id': 989, 'title': '1984', 'comments': 'great great great',
            'author': {'id': 76,'firstname': 'George', 'lastname': 'Orwell'}
        })
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
        gourmand_cast = DictToModel(to=Gourmand)
        gourmand = gourmand_cast.call({
            'id': self.gourmand.pk,
            'pseudo': 'Taaaaz',
            'favourite_dishes': [
                {'id': self.salmon.pk, 'name': 'Pretty much'},
                {'id': self.foiegras.pk, 'name': 'Anything'},
            ]
        })
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
        gourmand_cast = DictToModel(to=Gourmand)
        gourmand = gourmand_cast.call({
            'pseudo': 'Touz',
            'favourite_dishes': [
                {'id': 888, 'name': 'Vitamine O'},
                {'id': self.salmon.pk},
                {'id': self.foiegras.pk},
            ]
        })
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
        cast = DictToModel(to=Journal)
        assert_raises(TypeError, cast.call, {
            'id': self.journal.id,
            'journalist_set': [],
        })

        self.gourmand.save()
        cast = DictToModel(to=Dish)
        salmon = cast.call({
            'id': self.salmon.id,
            'gourmand_set': [
                {'id': self.gourmand.id},
            ]
        })
        ok_(set(salmon.gourmand_set.all()) == set([self.gourmand]))

    def update_object_with_nk_test(self):
        """
        Test update an object with its natural key, natural key already existing.
        """
        columnist_before = Columnist.objects.count()
        columnist_cast = DictToModel(to=Columnist, key_schema=('firstname', 'lastname'))
        jamy = columnist_cast.call({
            'firstname': 'Jamy',
            'lastname': 'Gourmaud',
            'column': 'truck'
        })
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
        columnist_cast = DictToModel(to=Columnist, key_schema=('firstname', 'lastname'))
        fred = columnist_cast.call({
            'firstname': 'Frédéric',
            'lastname': 'Courant',
            'journal': {'id': self.journal.pk},
            'column': 'on the field',
        })
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
        cast = DictToModel(to=Issue)
        issue = cast.call({
            'id': self.issue.pk,
            'issue_date': {'year': 1865, 'month': 1, 'day': 1},
            'last_char_datetime': {'year': 1864, 'month': 12, 'day': 31, 'hour': 1},
        })
        ok_(issue.issue_date == datetime.date(year=1865, month=1, day=1))
        ok_(issue.last_char_datetime == datetime.datetime(year=1864, month=12, day=31, hour=1))


donttest="""

.. currentmodule:: spiteat.djangosrz

This module contains a serializer :class:`ModelSrz` for your Django models. This serializer features :

    - Deep serialization. Foreign keys, and foreign keys of foreign keys, and so on ... are completely serialized.
    - Support multi-table inheritance. All attributes from parent models can be serialized.


new_object
---------------

If we provide the primary key, we can do this either by using the property name *pk*, or the explicit primary key field name :

    >>> author = author_srz.new_object({'id': 5})
    >>> isinstance(author, Author)
    True
    >>> author.pk
    5

    >>> author = author_srz.new_object({'pk': 5})
    >>> isinstance(author, Author)
    True
    >>> author.pk
    5

:class:`NCModelSrz` never create new objects :

    >>> author.save()
    >>> ncauthor_srz = NCModelSrz(custom_for=Author)
    >>> author_copy = ncauthor_srz.eat({'id': 5})
    >>> author_copy == author
    True
    >>> ncauthor_srz.eat({'id': 5777777})


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
