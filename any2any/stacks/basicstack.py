# -*- coding: utf-8 -*-
import datetime
from types import FunctionType

from any2any import (Cast, CastStack, FromMapping, ToMapping, FromIterable, ToIterable,
FromObject, ToObject, ContainerWrap, ObjectWrap, Wrap, CastItems, Mm)

#TODO: document, reorganize tests

class Identity(Cast):
    """
    Identity operation :

        >>> Identity()('1')
        '1'
    """

    def call(self, obj):
        return obj

class ToType(Cast):
    """
    Dumb cast :

        >>> to_int = ToType(to=int) # equivalent to >>> int('1')
        >>> to_int('1')
        1
    """

    def call(self, obj):
        return self.to(obj)

class CallFunction(Cast):
    """
    Function call operation :
        
        >>> def bla(): # Only works for functions that take no argument
        ...     return 'called'
        >>> call_func = CallFunction()
        >>> call_func(bla)
        'called'
    """
    
    def call(self, func):
        return func()

class MappingToMapping(FromMapping, CastItems, ToMapping):
    """
    Dictionaries to dictionaries :

        >>> MappingToMapping(to=dict)({'1': anObject1, 2: anObject2})
        {'1': 'its casted version 1', 2: 'its casted version 2'}
    """
    pass

class IterableToIterable(FromIterable, CastItems, ToIterable):
    """
    List to list :

        >>> IterableToIterable(to=list)([anObject1, anObject2])
        ['its casted version 1', 'its casted version 2']
    """
    pass

class ObjectToMapping(FromObject, CastItems, ToMapping):
    """
    Object to dictionary :

        >>> ObjectToMapping(to=dict)(anObject)
        {'attr1': 'its casted value', 'attr2': 'its casted value'}
    """
    pass

class MappingToObject(FromMapping, CastItems, ToObject):
    """
    Dictionary to object :

        >>> cast = MappingToObject(to=SomeObject)
        >>> cast({'attr1': 'its casted value 1', 'attr2': 'its casted value 2'})
        <SomeObject>
    """
    pass

WrappedDateTime = ObjectWrap(datetime.datetime, extra_schema={
    'year': Wrap(int, float),
    'month': Wrap(int, float),
    'day': Wrap(int, float),
    'hour': Wrap(int, float),
    'minute': Wrap(int, float),
    'second': Wrap(int, float),
    'microsecond': Wrap(int, float),
})

WrappedDate = ObjectWrap(datetime.date, extra_schema={
    'year': Wrap(int, float),
    'month': Wrap(int, float),
    'day': Wrap(int, float),
})

class BasicStack(CastStack):

    defaults = dict(
        mm_to_cast = {
            Mm(from_any=object, to_any=object): Identity(), # Fallback, when no cast was found
            Mm(from_any=FunctionType): CallFunction(),
            Mm(from_any=list): IterableToIterable(to=list), # Any list to a list (of undefined elements)
            Mm(from_any=tuple): IterableToIterable(to=tuple), # Any tuple to a tuple (of undefined elements)
            Mm(from_any=set): IterableToIterable(to=set), # Any tuple to a tuple (of undefined elements)
            Mm(from_any=dict): MappingToMapping(to=dict), # Any set to set (of undefined elements)
            Mm(from_any=datetime.date): ObjectToMapping(from_=WrappedDate, to=dict), # TODO: pb : from_ can't be customized
            Mm(from_any=datetime.datetime): ObjectToMapping(from_=WrappedDateTime, to=dict),
            Mm(to_any=datetime.date): MappingToObject(to=WrappedDate),
            Mm(to_any=datetime.datetime): MappingToObject(to=WrappedDateTime),
        },
        _meta = dict(mm_to_cast={'override': 'copy_and_update'}),
    )

any2any = BasicStack()
