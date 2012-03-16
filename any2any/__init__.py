# -*- coding: utf-8 -*-
import types
import datetime

from cast import Cast
from utils import Singleton, AllSubSetsOf, SmartDict
from bundle import (Bundle, ObjectBundle, IterableBundle,
MappingBundle, IdentityBundle)
from stdlib.bundle import DateBundle, DateTimeBundle

serialize = Cast({
    AllSubSetsOf(dict): MappingBundle,
    AllSubSetsOf(list): IterableBundle,
    AllSubSetsOf(int): IdentityBundle,
    AllSubSetsOf(float): IdentityBundle,
    AllSubSetsOf(bool): IdentityBundle,
    AllSubSetsOf(basestring): IdentityBundle,
    AllSubSetsOf(types.NoneType): IdentityBundle,
    AllSubSetsOf(datetime.datetime): DateTimeBundle,
    AllSubSetsOf(datetime.date): DateBundle,
}, {
    AllSubSetsOf(dict): MappingBundle,
    AllSubSetsOf(list): IterableBundle,
    AllSubSetsOf(object): MappingBundle,
})


deserialize = Cast({
    AllSubSetsOf(dict): MappingBundle,
    AllSubSetsOf(list): IterableBundle,
    AllSubSetsOf(int): IdentityBundle,
    AllSubSetsOf(float): IdentityBundle,
    AllSubSetsOf(bool): IdentityBundle,
    AllSubSetsOf(basestring): IdentityBundle,
    AllSubSetsOf(types.NoneType): IdentityBundle,
    AllSubSetsOf(datetime.datetime): DateTimeBundle,
    AllSubSetsOf(datetime.date): DateBundle,
})
