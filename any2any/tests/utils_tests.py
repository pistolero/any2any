"""
    >>> import os, sys
    >>> sys.path.append(os.path.abspath('../..'))
    >>> from spiteat.utils import *
    >>> closest_conversion((int, basestring), [(int, basestring), (int, str), (object, object), (object, str), (int, object)])
    (<type 'int'>, <type 'basestring'>)
    >>> closest_conversion((int, basestring), [(object, basestring), (int, str), (object, object)])
    (<type 'int'>, <type 'str'>)
    >>> closest_conversion((int, basestring), [(int, str), (int, unicode)]) #impossible to know result !?
    (<type 'int'>, <type 'str'>)

    >>> closest_parent(object, [object, int, str])
    <type 'object'>
    >>> closest_parent(int, [object, int, str])
    <type 'int'>
    >>> closest_parent(str, [object, basestring, unicode, int])
    <type 'basestring'>

"""
if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.REPORT_ONLY_FIRST_FAILURE)
