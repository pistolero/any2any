# -*- coding: utf-8 -*-
import copy

from node import NodeInfo, Node
from utils import ClassSetDict, AttrDict
from exceptions import NotIncludedError


class Cast(object):

    def __init__(self, node_class_map, fallback_map={}):
        self.node_class_map = ClassSetDict(node_class_map)
        self.fallback_map = ClassSetDict(fallback_map)
        self._depth_counter = 0
        self.debug = False

    def __call__(self, inpt, frm=NodeInfo(), to=NodeInfo()):
        self._depth_counter += 1

        # If `frm`, isn't a node class yet, we must find one for it.
        # For this, we'll first get a NodeInfo, and then resolve it to a
        # node class. 
        if (isinstance(frm, type) and not issubclass(frm, Node))\
                or isinstance(frm, NodeInfo):

            if not isinstance(frm, NodeInfo):
                node_info = NodeInfo(frm)
            else:
                node_info = copy.copy(frm)
                if node_info.class_info is None:
                    node_info.class_info = type(inpt)
            frm_node_class = self._resolve_node_class(node_info, inpt)
        else:
            frm_node_class = frm
        
        # If `to`, isn't a node class yet, we must find one for it.
        # For this, we first get a NodeInfo ...
        if (isinstance(to, type) and not issubclass(to, Node))\
                or isinstance(to, NodeInfo):

            if not isinstance(to, NodeInfo):
                node_info = NodeInfo(to)
            else:
                node_info = copy.copy(to)

            # If the NodeInfo doesn't provide any useful `class_info` about
            # the node class, we directly try to find a good fallback.
            if node_info.class_info is None:
                to_node_class = self._get_fallback(frm_node_class)
            else:
                to_node_class = self._resolve_node_class(node_info, inpt)
        else:
            to_node_class = to

        # Checking schema compatibility : if it fails with the 2 schemas found,
        # we use the actual schema of `inpt`
        frm_schema = AttrDict(frm_node_class.schema_dump())
        to_schema = AttrDict(to_node_class.schema_load())
        try:
            frm_schema.validate_inclusion(to_schema)
        except NotIncludedError:
            frm_schema = self._improvise_schema(inpt, frm_node_class)
            frm_schema.validate_inclusion(to_schema)

        # Generator iterating on the casted items, and which will be used
        # to load the casted object.
        # It calls the casting recursively if the schema has any nesting.
        generator = _Generator(self, frm_node_class.new(inpt).dump(), frm_schema, to_schema)

        # Finally, we load the casted object.
        self.log('%s <= %s' % (frm_node_class, inpt))
        casted = to_node_class.load(generator).obj
        self.log('%s => %s' % (to_node_class, casted))
        self._depth_counter -= 1
        return casted

    def log(self, msg):
        if self.debug: print '\t' * self._depth_counter, msg

    def _get_fallback(self, frm_node_class):
        """
        Gets a fallback node class for the output, as a last resort.
        """
        # If input is a final value, we'll just assume that ouput is also
        if AttrDict.KeyFinal in frm_node_class.schema_dump():
            return frm_node_class

        # we try to get a node class from the `fallback_map`
        frm = frm_node_class.klass
        if isinstance(frm, type):
            node_class = self.fallback_map.subsetget(frm)
            if not node_class is None:
                return node_class

        # Or we'll just use `frm_node_class`, so that operation is an identity.
        return frm_node_class # TODO: shouldn't this rather be an error ?

    def _resolve_node_class(self, node_info, inpt):
        """
        Resolves the node class from a node info.
        """
        klass = node_info.get_class(type(inpt))
        node_class = self.node_class_map.subsetget(klass)
        if node_class is None:
            raise NoNodeClassError(klass)
        return node_class.get_subclass(klass=klass, **node_info.kwargs)

    def _improvise_schema(self, obj, node_class):
        """
        This method can be used to get the dump schema for an object, when the
        schema obtained 'a priori' is not sufficient.
        """
        node = node_class.new(obj)
        schema = {}
        for k, v in node.dump():
            schema[k] = type(v)
        return AttrDict(schema)


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
        if key is AttrDict.KeyFinal:
            casted_value = value
        else:
            self.cast.log('[ %s ]' % key)
            casted_value = self.cast(value,
                to=self.to_schema[key],
                frm=self.frm_schema[key]
            )
        return key, casted_value

