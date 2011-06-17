# -*- coding: utf-8 -*-
try:
    import abc
except ImportError:
    from compat import abc
from base import Cast, Mm, Spz
from containercast import FromDict, ToDict
from simple import Identity

class ListToFirstElem(Cast):
    """
    List to its first element :

        >>> cast = ListToFirstElem()
        >>> cast([33, 77, 'e'])
        33
        >>> cast([]) == None
        True
    """

    def call(self, inpt):
        try:
            return inpt[0]
        except IndexError:
            return self.no_elem_error()

    def no_elem_error(self):
        pass


class OneElemToList(Cast):
    """
    Object to a list of one element :

        >>> cast = OneElemToList()
        >>> cast('BLA')
        ['BLA']
    """

    def call(self, inpt):
        return [inpt]

class QueryDictCast(FromDict, ToDict):
    """
    Cast for flatening a dictionary with a nested structure.

        >>> cast = DictFlatener(list_keys=['a_list', 'another_list'])
        >>> cast({'a_list': [1, 2], 'a_normal_key': [1, 2, 3], 'another_list': []}) == {
        ...     'a_list': [1, 2],
        ...     'a_normal_key': 1,
        ...     'another_list': []
        ... }
        True
    """

    defaults = dict(
        mm_to_cast = {
            Mm(list, object): ListToFirstElem(),
            Mm(from_any=object, to=list): OneElemToList(),
            Mm(list, list): Identity(),
        },
        list_keys = [],
    )

    def get_to_class(self, key):
        if (key in self.list_keys) or self.value_is_list(key):
            return list
        else:
            return object

    def value_is_list(self, key):
        return False

