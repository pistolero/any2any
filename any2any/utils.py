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

    @staticmethod
    def pick_best(klass, choice_map, exc_type=ValueError):
        class_sets = set(filter(lambda cs: klass <= cs, choice_map))
        # Eliminate supersets
        for cs1 in class_sets.copy():
            for cs2 in class_sets.copy():
                if cs1 <= cs2 and not cs1 is cs2:
                    class_sets.discard(cs2)
        try:
            best_match = list(class_sets)[0]
        except IndexError:
            raise exc_type("couldn't find a match for %s" % klass)
        return choice_map[best_match]


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


class ClassSetDict(dict):

    def subset_get(self, klass, default=None):
        try:
            return ClassSet.pick_best(klass, choice_map, exc_type=KeyError)
        except KeyError: # TODO: KeyError not a good exception choice
            return default


def classproperty(func):
    class _classproperty(property):
        def __get__(self, cls, owner):
            return self.fget.__get__(None, owner)()
    return _classproperty(classmethod(func))
