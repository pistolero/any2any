# coding=utf-8

#import serializers_tests, api_tests
#__test__ = dict()
#__test__['serializers_tests'] = serializers_tests.__doc__
#__test__['api_tests'] = api_tests.__doc__

from django.db.models import AutoField, CharField, ForeignKey, Model
from django.db.models.manager import Manager

from any2any.djangocast import *
from models import *

from nose.tools import assert_raises, ok_

class IntrospectMixin_Test(object):
    
    def fields_test(self):
        """
        Test IntrospectMixin.fields
        """
        introspector = IntrospectMixin()
        columnist_fields = introspector.fields(Columnist)
        gourmand_fields = introspector.fields(Gourmand)
        ok_(set(columnist_fields) == set(['id', 'lastname', 'firstname', 'journal', 'column', 'nickname']))
        ok_(isinstance(columnist_fields['id'], AutoField))
        ok_(isinstance(columnist_fields['lastname'], CharField))
        ok_(isinstance(columnist_fields['nickname'], CharField))
        ok_(isinstance(columnist_fields['journal'], ForeignKey))
        ok_(set(gourmand_fields) == set(['id', 'lastname', 'firstname', 'favourite_dishes', 'pseudo']))
        ok_(isinstance(gourmand_fields['firstname'], CharField))
        ok_(isinstance(gourmand_fields['favourite_dishes'], ManyToManyField))
        ok_(isinstance(gourmand_fields['pseudo'], CharField))


class ModelToDict_Test(object):
    """
    Tests for ModelToDict
    """

    def setUp(self):
        self.author = Author(firstname='John', lastname='Steinbeck', nickname='JS')
        self.book = Book(title='Grapes of Wrath', author=self.author, comments='great great great')
        self.foiegras = Dish(name='Foie gras')
        self.salmon = Dish(name='salmon')
        self.gourmand = Gourmand(pseudo='Taz', firstname='T', lastname='Aznicniev')
        self.journal = Journal(name="C'est pas sorcier") ; self.journal.save()
        self.columnist = Columnist(firstname='Jamy', lastname='Gourmaud', journal=self.journal, column='truck')
        self.author.save()
        self.book.save()
        self.foiegras.save()
        self.salmon.save()
        self.gourmand.save()
        self.journal.save()
        self.columnist.save()

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

    def tearDown(self):
        self.author.delete()
        self.book.delete()
        self.foiegras.delete()
        self.salmon.delete()
        self.gourmand.delete()
        self.columnist.delete()
        self.journal.delete()


class DictToModel_Test(object):
    """
    Tests for DictToModel
    """

    def setUp(self):
        self.author = Author(firstname='John', lastname='Steinbeck', nickname='JS')
        self.book = Book(title='Grapes of Wrath', author=self.author, comments='great great great')
        self.author.save()
        self.book.save()

    def call_test(self):
        """
        Simple test DictToModel.call
        """
        cast = DictToModel(mm=Mm(dict, Author))
        authors_before = Author.objects.count()
        da = cast.call({'firstname': 'James Graham', 'lastname': 'Ballard', 'id': 3, 'nickname': 'JC Ballard'})
        # We check the fields
        ok_(da.firstname == 'James Graham')
        ok_(da.lastname == 'Ballard')
        ok_(da.id == 3)
        ok_(da.nickname == 'JC Ballard')
        # We check that new author was created
        ok_(Author.objects.count() == authors_before + 1)
        da.delete()

    def update_objects_test(self):
        """
        Test deserialize already existing object with an already existing foreignkey 
        """
        book_cast = DictToModel(mm=Mm(dict, Book))
        authors_before = Author.objects.count()
        books_before = Book.objects.count()
        db = book_cast.call({
            'id': self.book.pk, 'title': 'In cold blood', 'comments': 'great great great',
            'author': {'id': self.author.pk, 'firstname': 'Truman', 'lastname': 'Capote'}, 
        })
        # We check the fields
        ok_(db.title == 'In cold blood')
        author = Author.objects.get(pk=db.author.pk)
        ok_(author.firstname == 'Truman')
        ok_(author.lastname == 'Capote')
        # We check that no item was created
        ok_(Book.objects.count() == books_before)
        ok_(Author.objects.count() == authors_before)
        # cleaning-up
        author = db.author
        book.delete()
        author.delete()

    def create_objects_auto_assign_pk_test(self):
        """
        Test deserialize new object with new foreignkey, automatically picked PK. 
        """
        book_cast = DictToModel(mm=Mm(dict, Book))
        authors_before = Author.objects.count()
        books_before = Book.objects.count()
        db = book_cast.call({
            'title': '1984', 'comments': 'great great great',
            'author': {'firstname': 'George', 'lastname': 'Orwell'}
        })
        # We check the fields
        ok_(db.title == 'Grapes of Wrath')
        author = Author.objects.get(firstname='George', lastname='Orwell')
        ok_(db.author.firstname == 'Jo')
        ok_(db.author.lastname == 'Stein')
        # We check that no item was created
        ok_(Book.objects.count() == books_before + 1)
        ok_(Author.objects.count() == authors_before + 1)
        # cleaning-up
        author = db.author
        book.delete()
        author.delete()

    def tearDown(self):
        self.author.delete()
        self.book.delete()


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


default_attr_schema
---------------------

    >>> author_srz.default_attr_schema('id')[0] == AutoField
    True
    >>> author_srz.default_attr_schema('firstname')[0] == CharField
    True
    >>> book_srz = ModelSrz(custom_for=Book)
    >>> book_srz.default_attr_schema('author')[0] == Author
    True
    >>> gourmand_srz = ModelSrz(custom_for=Gourmand)
    >>> from spiteat.utils import specialize
    >>> gourmand_srz.default_attr_schema('favourite_dishes') == (Manager, {'custom_for': specialize(list, Dish)})
    True

Deserialization ManyToManyField
-------------------------------

If the record exist, no new record is created

    >>> g_before = Gourmand.objects.count()
    >>> d_before = Dish.objects.count()
    >>> gourmand = gourmand_srz.eat({
    ...     'pk': 1,
    ...     'pseudo': 'Taaaaz',
    ...     'favourite_dishes': [
    ...         {'pk': 1, 'name': 'Pretty much'},
    ...         {'pk': 2, 'name': 'Anything'},
    ...     ]
    ... })
    >>> Gourmand.objects.count() == g_before
    True
    >>> Dish.objects.count() == d_before
    True

    >>> set(gourmand.favourite_dishes.all()) == set([salmon, foiegras])
    True
    >>> gourmand.pseudo
    'Taaaaz'
    >>> Dish.objects.get(pk=1).name
    u'Pretty much'
    >>> Dish.objects.get(pk=2).name
    u'Anything'

If it doesn't exist, record is created, and manytomany related objects as well.

    >>> g_before = Gourmand.objects.count()
    >>> d_before = Dish.objects.count()
    >>> gourmand = gourmand_srz.eat({
    ...     'pk': 444,
    ...     'pseudo': 'Touz',
    ...     'favourite_dishes': [
    ...         {'pk': 888, 'name': 'Vitamine O'},
    ...         {'pk': 1},
    ...         {'pk': 2},
    ...     ]
    ... })
    >>> Gourmand.objects.count() == g_before + 1
    True
    >>> Dish.objects.count() == d_before + 1
    True

    >>> vitamineo = Dish.objects.get(pk=888)
    >>> set(gourmand.favourite_dishes.all()) == set([vitamineo, foiegras, salmon])
    True
    >>> gourmand.pseudo
    'Touz'
    >>> vitamineo.name
    u'Vitamine O'


Content type - GenericForeignKey
----------------------------------

    >>> bookmark = Bookmark(name='favourite', to=foiegras)

    >>> bookmark_srz = ModelSrz(custom_for=Bookmark, include=['to', 'pk'])
    >>> bookmark = bookmark_srz.eat({'pk': bookmark.pk, 'to': ('test_models', 'dish', salmon.pk)})
    >>> bookmark.to == salmon
    True

    >>> bookmark_srz.spit(bookmark) == {'to': ('test_models', 'dish', salmon.pk), 'pk': bookmark.pk}
    True

Natural key
-------------

    >>> columnist_srz = ModelSrz(custom_for=Columnist, key_schema=('firstname', 'lastname'))
    >>> columnist_srz.get_obj_key({
    ...     'firstname': 'Jamy',
    ...     'lastname': 'Gourmaud',
    ...     'journal': {'id': cps.pk, 'pk': cps.pk, 'name': 'C\\'est pas sorcier'},
    ...     'id': jamy.pk,
    ...     'pk': jamy.pk,
    ...     'column': 'truck',
    ... })
    ('Jamy', 'Gourmaud')

    >>> columnist_before = Columnist.objects.count()
    >>> jamy = columnist_srz.eat({
    ...     'firstname': 'Jamy',
    ...     'lastname': 'Gourmaud',
    ... })
    >>> columnist_before == Columnist.objects.count()
    True

    >>> columnist_before = Columnist.objects.count()
    >>> fred = columnist_srz.eat({
    ...     'firstname': 'Frédéric',
    ...     'lastname': 'Courant',
    ...     'journal': {'id': cps.pk},
    ...     'column': 'field',
    ... })
    >>> columnist_before + 1 == Columnist.objects.count()
    True
"""
