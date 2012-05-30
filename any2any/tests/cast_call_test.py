import unittest

from any2any import *


class BaseBook(object):

    def __init__(self, title):
        self.title = title


class BaseAuthor(object):

    def __init__(self, name, books):
        self.name = name
        self.books = books


class Book(BaseBook):
    """
    A book object that knows how to dump and load itself
    """

    def __dump__(self):
        yield 'title', self.title

    @classmethod
    def __load__(cls, items_iter):
        attrs = dict(items_iter)
        return cls(attrs['title'])


class Author(BaseAuthor):
    """
    An author object that knows how to dump and load itself
    """

    def __dump__(self):
        for k in ['name', 'books']:
            yield k, getattr(self, k)

    @classmethod
    def __load__(cls, items_iter):
        attrs = dict(items_iter)
        return cls(attrs['name'], attrs['books'])

    @classmethod
    def __lschema__(cls):
        return {
            'books': IterableNode.get_subclass(value_type=Book),
            AttrDict.KeyAny: NodeInfo()
        }


class AuthorNode(object):
    """
    A class that knows how to dump and load authors
    """

    @classmethod
    def __dump__(cls, obj):
        for k in ['name', 'books']:
            yield k, getattr(obj, k)

    @classmethod
    def __dschema__(cls, obj):
        return {
            'books': IterableNode.get_subclass(value_type=BookNode),
            'name': str
        }

    @classmethod
    def __load__(cls, items_iter):
        attrs = dict(items_iter)
        return BaseAuthor(attrs['name'], attrs['books'])

    @classmethod
    def __lschema__(cls):
        return {
            'books': IterableNode.get_subclass(value_type=BookNode),
            'name': str
        }


class BookNode(object):
    """
    A class that knows how to dump and load books
    """

    @classmethod
    def __dump__(cls, obj):
        yield 'title', obj.title

    @classmethod
    def __dschema__(cls, obj):
        return {'title': str}

    @classmethod
    def __load__(cls, items_iter):
        attrs = dict(items_iter)
        return BaseBook(attrs['title'])

    @classmethod
    def __lschema__(cls):
        return {'title': str}


class Cast_complex_calls_test(unittest.TestCase):

    def setUp(self):
        books = [Book('1984'), Book('animal farm')]
        george = Author('George Orwell', books)
        self.george = george

        base_books = [BaseBook('1984'), BaseBook('animal farm')]
        base_george = BaseAuthor('George Orwell', base_books)
        self.base_george = base_george

        self.serializer = Cast({
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): IdentityNode,
        }, {
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): IdentityNode,
            AllSubSetsOf(BaseAuthor): MappingNode,
            AllSubSetsOf(BaseBook): MappingNode,
        })

        self.deserializer = Cast({
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): IdentityNode,
        })

    def serialize_dump_test(self):
        """
        test serialize object relying on its `__dump__` method.
        """
        self.assertEqual(self.serializer(self.george), {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })

    def deserialize_load_test(self):
        """
        test deserialize object relying on its `__load__` method.
        """
        truman = self.deserializer({'name': 'Truman Capote', 'books': [
            {'title': 'In cold blood'},
        ]}, loader=Author)
        self.assertTrue(isinstance(truman, Author))
        self.assertEqual(truman.name, 'Truman Capote')
        self.assertEqual(len(truman.books), 1)
        for book in truman.books:
            self.assertTrue(isinstance(book, Book))
        self.assertEqual(truman.books[0].title, 'In cold blood')

    def serialize_with_node_test(self):
        """
        test serialize object using a node that knows how to load and dump that object.
        """
        self.assertEqual(self.serializer(self.base_george, dumper=AuthorNode), {
            'name': 'George Orwell', 'books': [
                {'title': '1984'},
                {'title': 'animal farm'}
            ]
        })

    def deserialize_with_node_test(self):
        """
        test deserialize object using a node that knows how to load and dump that object.
        """
        truman = self.deserializer({'name': 'Truman Capote', 'books': [
            {'title': 'In cold blood'},
        ]}, loader=AuthorNode)
        self.assertTrue(isinstance(truman, BaseAuthor))
        self.assertEqual(truman.name, 'Truman Capote')
        self.assertEqual(len(truman.books), 1)
        for book in truman.books:
            self.assertTrue(isinstance(book, BaseBook))
        self.assertEqual(truman.books[0].title, 'In cold blood')

