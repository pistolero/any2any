# -*- coding: utf-8 -*-
import collections


class ClassSet(object):
    # Set of classes, allowing to easily calculate inclusions
    # with comparison operators : `a < B` <=> "A strictly included in B"

    def __init__(self, klass):
        self.klass = klass

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        other = self._default_to_singleton(other)
        return not self == other and other < self

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def _default_to_singleton(self, klass):
        if not isinstance(klass, ClassSet):
            return Singleton(klass)
        else:
            return klass


class AllSubSetsOf(ClassSet):

    def __eq__(self, other):
        if isinstance(other, AllSubSetsOf):
            return self.klass == other.klass
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, AllSubSetsOf):
            return issubclass(self.klass, other.klass) and not other == self
        else:
            return False

    def __repr__(self):
        return u"Any '%s'" % self.klass.__name__

    def __hash__(self):
        return hash(('set', self.klass))


class Singleton(ClassSet):

    def __eq__(self, other):
        other = self._default_to_singleton(other)
        return self.klass == other.klass

    def __lt__(self, other):
        if isinstance(other, AllSubSetsOf):
            return issubclass(self.klass, other.klass)
        else:
            return False

    def __repr__(self):
        return u"'%s'" % self.klass.__name__

    def __hash__(self):
        return hash(('singleton', self.klass))


class ClassSetDict(dict):

    def subsetget(self, klass, default=None):
        class_sets = set(filter(lambda cs: klass <= cs, self))
        # Eliminate supersets
        for cs1 in class_sets.copy():
            for cs2 in class_sets.copy():
                if cs1 <= cs2 and not cs1 is cs2:
                    class_sets.discard(cs2)
        try:
            best_match = list(class_sets)[0]
        except IndexError:
            return default
        return self[best_match]

    def __repr__(self):
        return 'ClassSetDict(%s)' % super(ClassSetDict, self).__repr__()


def classproperty(func):
    class _classproperty(property):
        def __get__(self, cls, owner):
            return self.fget.__get__(None, owner)()
    return _classproperty(classmethod(func))


class SmartDict(collections.MutableMapping):

    class KeyAny(object): pass
    class KeyFinal(object): pass
    class ValueUnknown(object): pass

    def __init__(self, *args, **kwargs):
        self.dict = dict(*args, **kwargs)

    def __getitem__(self, key):
        try:
            return self.dict[key]
        except KeyError as e:
            if not key is self.KeyFinal: 
                try:
                    return self.dict[self.KeyAny]
                except KeyError:
                    raise e
            else:
                raise e

    def __setitem__(self, key, value):
        self.dict[key] = value
    
    def __delitem__(self, key):
        del self.dict[key]

    def __len__(self):
        return len(self.dict)

    def __iter__(self):
        return iter(self.dict)

    def __contains__(self, key):
        return (key in self.dict or 
            (self.KeyAny in self.dict and not key is self.KeyFinal))

    def __repr__(self):
        return 'SmartDict(%s)' % self.dict

    def _validate(self):
        if (SmartDict.KeyFinal in schema) and len(schema) != 1:
            raise SchemaNotValid("schema cannot contain several items if it contains 'KeyFinal'")
        elif (SmartDict.KeyAny in schema) and len(schema) != 1:
            raise SchemaNotValid("schema cannot contain several items if it contains 'KeyAny'")
