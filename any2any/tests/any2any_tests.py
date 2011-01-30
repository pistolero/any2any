"""
..

    >>> import os, sys
    >>> import os, sys
    >>> sys.path.append(os.path.abspath('../..'))

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

    >>> from any2any import any2any
    >>> any2any(Filling('butter', 'sauce'), dict) == {
    ...     'name': 'butter',
    ...     'kind': 'sauce'
    ... }
    True
    >>> any2any({
    ...     'name': 'butter',
    ...     'kind': 'sauce'
    ... }, Filling)
    Filling(butter, sauce)

Now, writing a cast for :class:`Sandwich` to dictionary requires just a little more tweaking :
"""

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.REPORT_ONLY_FIRST_FAILURE)
