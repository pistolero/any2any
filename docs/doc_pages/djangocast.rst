Casts for Django
+++++++++++++++++

Basic usage
#############

First, we'll import our casts, and a few models we'll demontrate with :

    >>> from djangocast_tests.test_models.models import Author, Book, Dish, Gourmand
    >>> from any2any.djangocast import ModelToDict, DictToModel
    >>> from any2any.utils import Mm

Converting an object to a dictionary
=====================================

First, we create a cast :

    >>> cast = ModelToDict()

Then we can use it on any object :

    >>> author = Author(firstname='John', lastname='Steinbeck', nickname='JS')
    >>> cast(author) == {'id': None, 'firstname': 'John', 'lastname': 'Steinbeck', 'nickname': 'JS'}
    True

And it also serializes nicely foreign-keys at any depth :

    >>> book = Book(title='Grapes of Wrath', author=author, comments='great great great')
    >>> cast(book) == {
    ...     'author': {'id': None, 'firstname': 'John', 'lastname': 'Steinbeck', 'nickname': 'JS'},
    ...     'id': None, 'comments': 'great great great', 'title': 'Grapes of Wrath'
    ... }
    True

... many-to-many relationships :

    >>> foiegras = Dish(name='Foie gras') ; salmon = Dish(name='salmon') ; foiegras.save() ; salmon.save()
    >>> taz = Gourmand(pseudo='Taz', firstname='T', lastname='Aznicniev') ; taz.save()
    >>> taz.favourite_dishes.add(salmon)
    >>> taz.favourite_dishes.add(foiegras)
    >>> cast(taz) == {
    ...     'id': taz.pk, 'pseudo': 'Taz', 'firstname': 'T', 'lastname': 'Aznicniev',
    ...     'favourite_dishes': [
    ...         {'id': foiegras.pk, 'name': 'Foie gras'},
    ...         {'id': salmon.pk, 'name': 'salmon'},
    ...     ]
    ... }
    True

and reverse relationships (i.e. ForeignKeys and ManyToManyFields) :

    >>> willy = Gourmand(pseudo='Willy', firstname='Free', lastname='William') ; willy.save()
    >>> willy.favourite_dishes.add(salmon)
    >>> willy.save()
    >>> cast = ModelToDict(include_extra=['gourmand_set']) # You have to add it explicitely to the output
    >>> cast(salmon) == {
    ...     'id': salmon.pk, 'name': 'salmon',
    ...     'gourmand_set': [
    ...         {
    ...             'id': taz.pk, 'pseudo': 'Taz', 'firstname': 'T', 'lastname': 'Aznicniev',
    ...             'favourite_dishes': [
    ...                 {'id': foiegras.pk, 'name': 'Foie gras'},
    ...                 {'id': salmon.pk, 'name': 'salmon'},
    ...             ]
    ...         },
    ...         {
    ...             'id': willy.pk, 'pseudo': 'Willy', 'firstname': 'Free', 'lastname': 'William',
    ...             'favourite_dishes': [
    ...                 {'id': salmon.pk, 'name': 'salmon'},
    ...             ]
    ...         },
    ...     ]
    ... }
    True

Notice that in this case, you have to ask explicitely to serialize the attribute *gourmand_set*, by setting *include_extra*.

Notice also that the output is pretty busy, as :class:`ModelToDict` will - by default - serialize all many-to-many relationships. But of course you can :ref:`control this behaviour<selecting_cast>`. 

..
    >>> foiegras.delete() ; salmon.delete()
    >>> taz.delete() ; willy.delete()

Converting a dictionary to an object
======================================

This time, to create a cast we need to specify which metamorphosis it should realize, i.e., what is the model to deserialize the data to. For example, with the same author as before :

    >>> cast = DictToModel(to=Author)
    >>> before = Author.objects.count()
    >>> author = cast({'firstname': 'John', 'lastname': 'Steinbeck'})
    >>> Author.objects.count() == before + 1 # An author was created
    True
    >>> (author.firstname, author.lastname) == ('John', 'Steinbeck')
    True

Notice that because the author didn't exist in the database, it has been created, saved, and has now an id :

    >>> bool(author.id)
    True

By specifying the id, you can now update this same author. Notice that no new object will be created :

    >>> before = Author.objects.count()
    >>> author = cast({'firstname': 'Truman', 'lastname': 'Capote', 'id': author.pk})
    >>> Author.objects.count() == before # No author was created
    True
    >>> (author.firstname, author.lastname) == ('Truman', 'Capote')
    True

You can also prevent the cast from creating an author at all, by setting the *create* setting of the cast to False. Then, exisiting objects are still updated :

    >>> cast = DictToModel(to=Author, create=False)
    >>> before = Author.objects.count()
    >>> author = cast({'firstname': 'JC', 'lastname': 'Ballard', 'id': author.pk})
    >>> Author.objects.count() == before # No author was created
    True
    >>> (author.firstname, author.lastname) == ('JC', 'Ballard')
    True

But if the object doesn't exist, :class:`DoesNotExist` error will be thrown :

    >>> author = cast({'id': 990})#doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    DoesNotExist: Author matching query does not exist.

Of course, once again you can deserialize foreign-keys at any depth :

    >>> cast = DictToModel(to=Book)
    >>> books_before = Book.objects.count() ; authors_before = Author.objects.count()
    >>> book = cast({
    ...     'author': {'firstname': 'George', 'lastname': 'Orwell'},
    ...     'title': '1984'
    ... })
    >>> Book.objects.count() == books_before + 1 , Author.objects.count() == authors_before + 1
    ... # An author and a book were created
    (True, True)

And the same thing goes for many-to-many relationships and reverse relationships.


Customizing the casts
#######################

ModelToDict
=============

Selecting the attributes to include
------------------------------------

In order to select which fields to serialize, you can use the settings *include*, *exclude* and *include_extra* :

Say, I want to serialize a book but include only the title :

    >>> book = Book.objects.get(title='1984')
    >>> cast = ModelToDict(include=['title'])
    >>> cast(book) == {'title': '1984'}
    True

Or maybe I want to exclude the id and author from the output :

    >>> cast = ModelToDict(exclude=['id', 'author'])
    >>> cast(book) == {'title': '1984', 'comments': ''}
    True

Adding virtual attributes to the output
-----------------------------------------

Let's add something to the output, for example the model name. As the model name is not an attribute of the object, we will need to use the setting *include_extra* to explicitely add it to the output, and the setting *attrname_to_getter* in order to specify a getter for the value :

    >>> def get_model_name(obj, name):
    ...     return obj.__class__.__name__.lower()
    ... 
    >>> cast = ModelToDict(
    ...     include=['title', 'model_name'],
    ...     attrname_to_getter={'model_name': get_model_name}
    ... )
    >>> book = Book.objects.get(title='1984')
    >>> cast(book) == {'model_name': 'book', 'title': '1984'}
    True

DictToModel
============

Deserializing with a natural key
----------------------------------

In order to deserialize an object by using a natural key, you can use the setting *key_schema*. For example, if I want to refer to my authors only by the pair ``(<firstname>, <lastname>)`` :

    >>> cast = DictToModel(to=Author, key_schema=('firstname', 'lastname'))
    >>> before = Author.objects.count()
    >>> author = cast({'firstname': 'George', 'lastname': 'Orwell', 'nickname': 'Jojo'})
    >>> Author.objects.count() == before # No author was created
    True
    >>> author.nickname
    'Jojo'

Deserializing virtual attributes
----------------------------------

To deserialize virtual attributes you need to use the setting *attrname_to_setter* in order to specify a setter for the attribute. For example :

    >>> def set_names(obj, name, value):
    ...     firstname, lastname = value.split(' ')
    ...     obj.firstname = firstname
    ...     obj.lastname = lastname
    ...     
    >>> cast = DictToModel(to=Author, attrname_to_setter={'combined_names': set_names})
    >>> author = cast({'combined_names': 'Boris Vian'})
    >>> author.firstname, author.lastname
    ('Boris', 'Vian')

.. _selecting_cast:

Both
======

Under the hood, the transformation is actually made recursively. When encountering a foreign-key, our cast gets a default cast for models and calls it. You can however control this behaviour in several different ways.

Setting a cast as default for a model
---------------------------------------

Say we want all the authors to be serialized to their complete name. To do that, we can declare a whole new cast (or also use :class:`ModelToDict` with nice settings) :

    >>> from any2any.base import Cast
    >>> class AuthorCast(Cast):
    ...     
    ...     def call(self, author): # You only need to subclass the 'call' method
    ...         return '%s %s' % (author.firstname, author.lastname)
    ...
    >>> author_cast = AuthorCast()

And tell our cast to use it for all instances of Author :

    >>> from any2any.utils import Mm
    >>> book_cast = ModelToDict(mm_to_cast={
    ...     Mm(Author, dict): author_cast # metamorphosis : Author -> dict
    ... })

The setting *mm_to_cast* maps a metamorphosis to a cast instance. So everytime ``book_cast`` needs to change an Author into a dict, ``author_cast`` will be called.

And now, when serializing a book, the author will be only a name :

    >>> book = Book.objects.get(title='1984')
    >>> book_cast(book) == {
    ...     'author': 'George Orwell',
    ...     'title': '1984', 'id': book.pk, 'comments': '',
    ... }
    True

Another solution is to set our AuthorCast as global default for all instances of Author :

    >>> from any2any.base import register
    >>> register(author_cast, Mm(Author, dict))
    >>> book_cast = ModelToDict()
    >>> book_cast(book) == {
    ...     'author': 'George Orwell',
    ...     'title': '1984', 'id': book.pk, 'comments': '',
    ... }
    True

Setting a cast for a given attribute
-----------------------------------------

If you want to override the default behaviour only for a given attribute, you can use the setting *key_to_cast*. For example, say we want to deserialize authors by using the natural key ``(<firstname>, <lastname>)`` (see example above) :

    >>> author_cast = DictToModel(to=Author, key_schema=('firstname', 'lastname'))
    >>> book_cast = DictToModel(to=Book, key_to_cast={'author': author_cast})
    >>> author_before = Author.objects.count() ; book_before = Book.objects.count()
    >>> book = book_cast({
    ...     'title': 'Animal farm',
    ...     'author': {'firstname': 'George', 'lastname': 'Orwell'},
    ... })
    >>> Author.objects.count() == author_before, Book.objects.count() == book_before + 1 # No author was created, a book was created
    (True, True)

..
    >>> Book.objects.all().delete()
    >>> Author.objects.all().delete()
    >>> register(ModelToDict(), Mm(Author, dict))
