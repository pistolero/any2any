# -*- coding: utf-8 -*-
import datetime
from types import FunctionType

from any2any import (Cast, CastStack, FromMapping, ToMapping, FromIterable, ToIterable,
FromObject, ToObject, WrappedObject, CastItems, Mm, DivideAndConquerCast)

#TODO: document, reorganize tests

class Identity(Cast):

    def call(self, obj):
        return obj


class ToType(Cast):

    def call(self, obj):
        return self.to(obj)


class CallFunction(Cast):

    def call(self, func):
        return func()


class DictToDict(FromMapping, CastItems, ToMapping, DivideAndConquerCast):

    class Meta:
        defaults = {'from_': dict, 'to': dict}


class ListToList(FromIterable, CastItems, ToIterable, DivideAndConquerCast):

    class Meta:
        defaults = {'from_': list, 'to': list}


class TupleToTuple(FromIterable, CastItems, ToIterable, DivideAndConquerCast):

    class Meta:
        defaults = {'from_': tuple, 'to': tuple}


class SetToSet(FromIterable, CastItems, ToIterable, DivideAndConquerCast):

    class Meta:
        defaults = {'from_': set, 'to': set}


class ObjectToDict(FromObject, CastItems, ToMapping, DivideAndConquerCast):
    
    class Meta:
        defaults = {'to': dict}


class DictToObject(FromMapping, CastItems, ToObject, DivideAndConquerCast):

    class Meta:
        defaults = {'from_': dict}


class WrappedDateTime(WrappedObject):

    klass = datetime.datetime
    
    @classmethod
    def default_schema(cls):
        return {
            'year': int,
            'month': int,
            'day': int,
            'hour': int,
            'minute': int,
            'second': int,
            'microsecond': int,
        }


class WrappedDate(WrappedObject):

    klass = datetime.date

    @classmethod
    def default_schema(cls):
        return {
            'year': int,
            'month': int,
            'day': int,
        }


class BasicStack(CastStack):

    class Meta:
        defaults = {
            'mm_to_cast': {
                Mm(from_any=object, to_any=object): Identity(), # Fallback, when no cast was found
                Mm(from_any=FunctionType): CallFunction(),
                Mm(from_any=list): ListToList(),
                Mm(from_any=tuple): TupleToTuple(),
                Mm(from_any=set): SetToSet(),
                Mm(from_any=dict): DictToDict(),
                Mm(from_any=datetime.date): ObjectToDict(from_wrapped=WrappedDate),
                Mm(from_any=datetime.datetime): ObjectToDict(from_wrapped=WrappedDateTime),
                Mm(to_any=datetime.date): DictToObject(to_wrapped=WrappedDate),
                Mm(to_any=datetime.datetime): DictToObject(to_wrapped=WrappedDateTime),
            }
        }

