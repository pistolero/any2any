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
        set(introspector.fields(Person)) == set(['id', 'lastname', 'firstname'])
        set(introspector.fields(Columnist)) == set(['id', 'lastname', 'firstname', 'journal', 'column', 'nickname'])
        raise Exception("incomplete")

class ModelToDict_Test(object):

    def setUp(self):
        self.author = Author(firstname='John', lastname='Steinbeck', nickname='JS')
        self.book = Book(title='Grapes of Wrath', author=self.author, comments='great great great')
        self.foiegras = Dish(name='Foie gras')
        self.salmon = Dish(name='salmon')
        self.gourmand = Gourmand(pseudo='Taz')
        self.author.save()
        self.book.save()
        self.foiegras.save()
        self.salmon.save()
        self.gourmand.save()

    def call_test(self):
        """
        Simple test ModelToDict.call
        """
        cast = ModelToDict()
        ok_(cast.call(self.author) == {'firstname': 'John', 'lastname': 'Steinbeck', 'id': self.author.pk, 'nickname': 'JS'})

    def many2many_test(self):
        cast = ModelToDict()
        ok_(cast.call(self.gourmand) == {'id': self.gourmand.pk, 'pseudo': 'Taz', 'favourite_dishes': []})
        self.gourmand.favourite_dishes.add(self.salmon)
        self.gourmand.favourite_dishes.add(self.foiegras)
        self.gourmand.save()
        ok_(cast.call(self.gourmand) == {
            'id': 1, 'pseudo': 'Taz',
            'favourite_dishes': [
                {'id': 1, 'name': 'Foie gras'},
                {'id': 2, 'name': 'salmon'},
            ]
        })

    def tearDown(self):
        self.author.delete()
        self.book.delete()
        self.foiegras.delete()
        self.salmon.delete()
        self.gourmand.delete()

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



Deserialization
----------------

    >>> authors_before = Author.objects.count()
    >>> da = author_srz.eat({'firstname': 'James Graham', 'lastname': 'Ballard', 'id': 3, 'nickname': 'JC Ballard'})
    >>> Author.objects.count() == authors_before + 1
    True
    >>> da.firstname
    'James Graham'
    >>> da.lastname
    'Ballard'
    >>> da.id
    3
    >>> da.nickname
    'JC Ballard'

Serialization foreignkey
-------------------------

    >>> book_srz = ModelSrz(custom_for=Book)
    >>> book_srz.class_srz_map.get(Author, None) == None
    True
    >>> book_srz.spit(book) == {
    ...     'id': 1, 'pk': 1,
    ...     'title': 'Grapes of Wrath',
    ...     'author': {
    ...         'id': author.pk, 'pk': author.pk,
    ...         'firstname': 'John',
    ...         'lastname': 'Steinbeck',
    ...         'nickname': 'JS'
    ...     },
    ...     'comments': 'great great great'
    ... }
    True
    >>> book_srz.class_srz_map.get(Author, None) == None
    True


Deserialization foreignkey
---------------------------

If the record already exist, no new record is created

    >>> authors_before = Author.objects.count()
    >>> books_before = Book.objects.count()
    >>> book_pk = Book.objects.all()[0].pk
    >>> author_pk = Author.objects.all()[0].pk

    >>> db = book_srz.eat({'id': book_pk, 'title': 'Grapes of Wrath', 'author': {'id': author_pk, 'firstname': 'John', 'lastname': 'Steinbeck'}, 'comments': 'great great great'})
    >>> db.title
    'Grapes of Wrath'
    >>> db.author.firstname
    'John'
    >>> db.author.lastname
    'Steinbeck'

    >>> Book.objects.count() == books_before
    True
    >>> Author.objects.count() == authors_before
    True

On the other hand, if the record doesn't exist, it is created.

    >>> authors_before = Author.objects.count()
    >>> books_before = Book.objects.count()

    >>> db = book_srz.eat({'title': 'Grapes of Wrath', 'author': {'firstname': 'Jo', 'lastname': 'Stein'}, 'comments': 'great great great'})
    >>> db.title
    'Grapes of Wrath'
    >>> db.author.firstname
    'Jo'
    >>> db.author.lastname
    'Stein'

    >>> Book.objects.count() == books_before + 1
    True
    >>> Author.objects.count() == authors_before + 1
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

Serialize model + parent fields
---------------------------------

    >>> cps = Journal(name='C\\'est pas sorcier')
    >>> cps.save()
    >>> jamy = Columnist(firstname='Jamy', lastname='Gourmaud', journal=cps, column='truck')
    >>> jamy.save()

    >>> columnist_srz.spit(jamy) == {
    ...     'firstname': 'Jamy',
    ...     'lastname': 'Gourmaud',
    ...     'journal': {'id': cps.pk, 'pk': cps.pk, 'name': 'C\\'est pas sorcier'},
    ...     'id': jamy.pk,
    ...     'pk': jamy.pk,
    ...     'column': 'truck',
    ...     'nickname': ''
    ... }
    True

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
