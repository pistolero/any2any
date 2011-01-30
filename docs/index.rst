any2any : magic casting for Python
====================================

.. automodule:: any2any

BLABLA

..
    >>> import os, sys
    >>> sys.path.append(os.path.abspath('..'))

.. _demonstration-ref:

Here are two simple classes :

    >>> class Filling(object):
    ...
    ...     def __init__(self, name='', kind=''):
    ...         self.name = name
    ...         self.kind = kind
    ...
    ...     def __repr__(self):
    ...         return 'Filling(%s, %s)' % (self.name, self.kind)
    ...
    >>> class Sandwich(object):
    ...     
    ...     def __init__(self, fillings=[], name='', bread=''):
    ...         self.fillings = fillings
    ...         self.name = name
    ...         self.bread = bread
    ...     
    ...     def __repr__(self): #Simple representations, to make examples easier to read
    ...         return 'Sandwich(%s, %s): %s' % (self.name, self.bread, sorted(self.fillings, key=lambda f: f.name))
    ...

Let's create a cast to transform a :class:`Filling` to a dictionary : 

    >>> from any2any.objectcast import ObjectToDict
    >>> filling_to_dict = ObjectToDict(include=['name', 'kind'])
    >>> filling_to_dict(Filling('butter', 'sauce')) == {
    ...     'name': 'butter',
    ...     'kind': 'sauce'
    ... }
    True

And a dictionary to a :class:`Filling`

    >>> dict_to_filling = DictToObject(include=['name', 'kind'])
    >>> dict_to_filling({
    ...     'name': 'butter',
    ...     'kind': 'sauce'
    ... })
    Filling(butter, sauce)

Now, writing a cast for :class:`Sandwich` to dictionary requires just a little more tweaking :

Documentation summary
----------------------

.. toctree::
    :maxdepth: 3

    doc_pages/conception
    doc_pages/base
    doc_pages/base_api
    doc_pages/objectcast
    doc_pages/objectcast_api
    doc_pages/example_objectcast
