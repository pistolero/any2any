# -*- coding: utf-8 -*-
import types
import datetime

from cast import Cast
from utils import AllSubSetsOf, ClassSet, AttrDict
from node import (Node, ObjectNode, IterableNode,
MappingNode, IdentityNode)
from stdlib.node import DateNode, DateTimeNode

serialize = Cast({
    AllSubSetsOf(dict): MappingNode,
    AllSubSetsOf(list): IterableNode,
    AllSubSetsOf(int): IdentityNode,
    AllSubSetsOf(float): IdentityNode,
    AllSubSetsOf(bool): IdentityNode,
    AllSubSetsOf(basestring): IdentityNode,
    AllSubSetsOf(types.NoneType): IdentityNode,
    AllSubSetsOf(datetime.datetime): DateTimeNode,
    AllSubSetsOf(datetime.date): DateNode,
}, {
    AllSubSetsOf(dict): MappingNode,
    AllSubSetsOf(list): IterableNode,
    AllSubSetsOf(object): MappingNode,
})


deserialize = Cast({
    AllSubSetsOf(dict): MappingNode,
    AllSubSetsOf(list): IterableNode,
    AllSubSetsOf(int): IdentityNode,
    AllSubSetsOf(float): IdentityNode,
    AllSubSetsOf(bool): IdentityNode,
    AllSubSetsOf(basestring): IdentityNode,
    AllSubSetsOf(types.NoneType): IdentityNode,
    AllSubSetsOf(datetime.datetime): DateTimeNode,
    AllSubSetsOf(datetime.date): DateNode,
})
