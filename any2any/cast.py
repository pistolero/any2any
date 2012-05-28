# -*- coding: utf-8 -*-
import copy

from node import NodeInfo, Node
from utils import ClassSetDict, AttrDict
from exceptions import NotIncludedError, NoNodeClassError


class Cast(object):

    def __init__(self, node_class_map, fallback_map={}):
        #TODO: fallback shouldn't be needed, if checking type of dumped inpt
        self.node_class_map = ClassSetDict(node_class_map)
        self.fallback_map = ClassSetDict(fallback_map)
        self._depth_counter = 0
        self.debug = False

    def __call__(self, inpt, frm=NodeInfo(), to=NodeInfo()):
        self._depth_counter += 1

        # If `frm`, isn't a node class yet, we must find one for it.
        # For this, we'll first get a NodeInfo, and then resolve it to a
        # node class.
        inpt_iter, frm_schema, dumper = None, None, None
        if hasattr(inpt, 'dump'):
            inpt_iter = inpt.dump()
            dumper = inpt
            if hasattr(inpt, 'schema_dump'):
                frm_schema = inpt.schema_dump()
        else:
            frm_node_class = None
            if hasattr(frm, 'dump'):
                frm_node_class = frm
            else:
                node_info = None
                if not isinstance(frm, NodeInfo):
                    node_info = NodeInfo(frm)
                else:
                    node_info = copy.copy(frm)
                    if node_info.class_info is None:
                        node_info.class_info = [type(inpt)]
                frm_node_class = self._resolve_node_class(inpt, node_info)

            inpt_iter = frm_node_class.dump(inpt)
            dumper = frm_node_class
            if hasattr(frm_node_class, 'schema_dump'):
                frm_schema = frm_node_class.schema_dump(inpt)
        if frm_schema is None:
            frm_schema = {AttrDict.KeyAny: NodeInfo()}
        frm_schema = AttrDict(frm_schema)
            
        # If `to`, isn't a node class yet, we must find one for it.
        # For this, we first get a NodeInfo ...
        loader = None
        if hasattr(to, 'load'):
            loader = to
        else:
            node_info = None
            if not isinstance(to, NodeInfo):
                node_info = NodeInfo(to)
            else:
                node_info = copy.copy(to)

            # If the NodeInfo doesn't provide any useful `class_info` about
            # the node class, we directly try to find a good fallback.
            if node_info.class_info is None:
                loader = self._get_fallback(inpt, dumper)
            else:
                loader = self._resolve_node_class(inpt, node_info)

        if hasattr(loader, 'schema_load'):
            to_schema = loader.schema_load()
        else:
            to_schema = {AttrDict.KeyAny: NodeInfo()}
        to_schema = AttrDict(to_schema)

        # Generator iterating on the casted items, and which will be used
        # to load the casted object.
        # It calls the casting recursively if the schema has any nesting.
        generator = _Generator(self, inpt_iter, frm_schema, to_schema)

        # Finally, we load the casted object.
        #self.log('%s <= %s' % (frm_node_class, inpt))
        casted = loader.load(generator)
        #self.log('%s => %s' % (loader, casted))
        self._depth_counter -= 1
        return casted

    def log(self, msg):
        if self.debug: print '\t' * self._depth_counter, msg

    def _get_fallback(self, inpt, dumper):
        """
        Gets a fallback node class for the output, as a last resort.
        """
        # we try to get a node class from the `fallback_map`
        node_class = self.fallback_map.subsetget(type(inpt))
        if not node_class is None:
            return node_class
        elif hasattr(dumper, 'load'):
            return dumper
        else:
            raise NoNodeClassError('Couldn\'t find a fallback for %s' % inpt)

    def _resolve_node_class(self, inpt, node_info):
        """
        Resolves the node class from a node info.
        """
        klass = node_info.get_class(type(inpt))
        if not issubclass(klass, Node):
            node_class = self.node_class_map.subsetget(klass)
            if node_class is None:
                raise NoNodeClassError(klass)
            return node_class.get_subclass(klass=klass, **node_info.kwargs)
        # If the value picked is a node class, we use that.
        else:
            return klass.get_subclass(**node_info.kwargs)


class _Generator(object):
    """
    Generator used to pass the data from one node to another.
    """

    def __init__(self, cast, items_iter, frm_schema, to_schema):
        self.cast = cast
        self.items_iter = items_iter
        self.frm_schema = frm_schema
        self.to_schema = to_schema

    def __iter__(self):
        return self
        
    def next(self):
        key, value = self.items_iter.next()
        self.last_key = key
        #TODO : test if key included in schema_to ?
        if key is AttrDict.KeyFinal:
            casted_value = value
        else:
            self.cast.log('[ %s ]' % key)
            casted_value = self.cast(value,
                to=self.to_schema[key],
                frm=self.frm_schema[key]
            )
        return key, casted_value

