# -*- coding: utf-8 -*-
import types
import datetime

from cast import Cast
from utils import AllSubSetsOf, ClassSet, AttrDict
from node import (Node, IterableNode,
MappingNode, IdentityNode, NodeInfo)

__all__ = ['serialize', 'deserialize', 'Cast', 'AllSubSetsOf',
'ClassSet', 'AttrDict', 'Node', 'IterableNode', 'MappingNode',
'IdentityNode', 'NodeInfo']

serialize = Cast({
    AllSubSetsOf(dict): MappingNode,
    AllSubSetsOf(list): IterableNode,
    AllSubSetsOf(int): IdentityNode,
    AllSubSetsOf(float): IdentityNode,
    AllSubSetsOf(bool): IdentityNode,
    AllSubSetsOf(basestring): IdentityNode,
    AllSubSetsOf(types.NoneType): IdentityNode,
}, {
    AllSubSetsOf(dict): MappingNode,
    AllSubSetsOf(list): IterableNode,
    AllSubSetsOf(object): IdentityNode,
})


deserialize = Cast({
    AllSubSetsOf(dict): MappingNode,
    AllSubSetsOf(list): IterableNode,
    AllSubSetsOf(int): IdentityNode,
    AllSubSetsOf(float): IdentityNode,
    AllSubSetsOf(bool): IdentityNode,
    AllSubSetsOf(basestring): IdentityNode,
    AllSubSetsOf(types.NoneType): IdentityNode,
})
