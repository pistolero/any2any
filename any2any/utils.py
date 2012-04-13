# -*- coding: utf-8 -*-
import collections

from exceptions import NotIncludedError


class BaseClassSet(object):
    """
    Set of classes, allowing to easily calculate inclusions
    with comparison operators, e.g. ``a < B`` <=> "A strictly included in B".
    """

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
        if not isinstance(klass, BaseClassSet):
            return ClassSet(klass)
        else:
            return klass


class ClassSet(BaseClassSet):
    """
    Finite set of classes, e.g. ::

        number_classes = ClassSet(int, float)
    """

    def __init__(self, *classes):
        self._classes = set(classes)

    def __eq__(self, other):
        other = self._default_to_singleton(other)
        if isinstance(other, ClassSet):
            return self._classes == other._classes
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, ClassSet):
            return self._classes < other._classes and not other == self
        elif isinstance(other, AllSubSetsOf):
            return all([issubclass(k, other._klass) for k in self._classes])
        else:
            return False

    def __repr__(self):
        return u"{%s}" % ', '.join([c.__name__ for c in self._classes])

    def __hash__(self):
        return hash(('%s' % self.__class__.__name__, tuple(self._classes)))


class AllSubSetsOf(BaseClassSet):
    """
    Infinite set of all the subclasses of a class. e.g. ::

        all_subclasses_of_dict = AllSubSetsOf(dict)
    """

    def __init__(self, klass):
        self._klass = klass

    def __eq__(self, other):
        if isinstance(other, AllSubSetsOf):
            return self._klass == other._klass
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, AllSubSetsOf):
            return issubclass(self._klass, other._klass) and not other == self
        else:
            return False

    def __repr__(self):
        return u"Any '%s'" % self._klass.__name__

    def __hash__(self):
        return hash(('%s' % self.__class__.__name__, self._klass))


class ClassSetDict(dict):
    """
    Dictionary whose keys are instances of :class:`BaseClassSet`.
    Allows to easily lookup the best match for a given class by using :meth:`subsetget`. 
    """

    def subsetget(self, klass, default=None):
        """
        Similar to :meth:`dict.get`, but looks-up by the smallest class set including
        `klass`.
        """
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


class AttrDict(collections.MutableMapping):
    """
    Dictionary used internally to handle schemas.
    """

    class KeyAny(object): pass
    class KeyFinal(object): pass

    def __init__(self, *args, **kwargs):
        self.dict = dict(*args, **kwargs)
        self._validate()

    def iter_attrs(self):
        """
        Returns an iterator over attribute names in the dictionary.
        Special values like :class:`KeyAny` or :class: `KeyFinal` are not included.
        """
        return (a for a in self if a not in [self.KeyAny, self.KeyFinal])

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
        self._validate()

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
        return '%s(%s)' % (self.__class__.__name__, self.dict)

    def _validate(self):
        if (self.KeyFinal in self.dict) and len(self.dict) != 1:
            raise ValueError("schema cannot contain several items if it contains %s" 
                % self.KeyFinal)

    def validate_inclusion(self, other):
        """
        Validates that the calling attribute dict's keys are included in `other`'s keys.
        If the validation failed :class:`NotIncludedError` is raised.

        For example :

            >>> ad1 = AttrDict({'a': 1, 'b': 2})
            >>> ad2 = AttrDict({'a': 3})
     
        `ad2` is included in `ad1`, but `ad1` is not included in `ad2`.
        """
        if self.KeyAny in self:
            if not self.KeyAny in other:
                raise NotIncludedError("%s contains %s, but %s doesn't" % (self, self.KeyAny, other))
        elif self.KeyFinal in self or self.KeyFinal in other:
            if not (self.KeyFinal in self and self.KeyFinal in other):
                raise NotIncludedError("both %s and %s must contain %s" % (self, other, self.KeyFinal))
        elif self.KeyAny in other:
            pass
        elif set(other) >= set(self):
            pass
        else:
            raise NotIncludedError("%s doesn't contain '%s'" %
            (other, list(set(self) - set(other))) )
