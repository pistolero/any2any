# -*- coding: utf-8 -*-
import copy

from node import NodeInfo, Node
from utils import ClassSetDict, AttrDict


class Cast(object):

    def __init__(self, node_class_map, fallback_map={}):
        self.node_class_map = ClassSetDict(node_class_map)
        self.fallback_map = ClassSetDict(fallback_map)
        self._depth_counter = 0
        self.debug = False

    def __call__(self, inpt, frm=NodeInfo(), to=NodeInfo()):
        self._depth_counter += 1

        # If `frm`, isn't a node class yet, we must find one for it
        if (isinstance(frm, type) and not issubclass(frm, Node))\
                or isinstance(frm, NodeInfo):

            # For this, we first get a NodeInfo, and resolve it to a
            # node class. 
            if not isinstance(frm, NodeInfo):
                node_info = NodeInfo(frm)
            else:
                node_info = copy.copy(frm)
                if node_info.lookup_with is None:
                    node_info.lookup_with = type(inpt)
            frm_node_class = self.resolve_node_class(node_info, inpt)
        else:
            frm_node_class = frm
        
        # If `to`, isn't a node class yet, we must find one for it
        if (isinstance(to, type) and not issubclass(to, Node))\
                or isinstance(to, NodeInfo):

            # For this, we first get a NodeInfo
            if not isinstance(to, NodeInfo):
                node_info = NodeInfo(to)
            else:
                node_info = copy.copy(to)

            # If the NodeInfo provides no class to use for looking-up
            # the Node class, we try to find a good fallback.
            if node_info.lookup_with is None:
                to_node_class = self._get_fallback(frm_node_class)
            else:
                to_node_class = self.resolve_node_class(node_info, inpt)
        else:
            to_node_class = to

        # Compiling schemas : if it fails with the 2 schemas found,
        # we use the actual schema of `inpt`
        out_schema = AttrDict(to_node_class.schema_load())
        in_schema = AttrDict(frm_node_class.schema_dump())
        try:
            compiled = CompiledSchema(in_schema, out_schema)
        except SchemasDontMatch:
            in_schema = self.improvise_schema(inpt, frm_node_class)
            compiled = CompiledSchema(in_schema, out_schema)

        # Generator iterating on the casted items, and which will be used
        # to load the casted object.
        # It calls the casting recursively if the schema has any nesting.
        generator = _Generator(self, frm_node_class.new(inpt).dump(), in_schema, out_schema)

        # Finally, we load the casted object.
        self.log('%s <= %s' % (frm_node_class, inpt))
        casted = to_node_class.load(generator).obj
        self.log('%s => %s' % (to_node_class, casted))
        self._depth_counter -= 1
        return casted

    def log(self, msg):
        if self.debug: print '\t' * self._depth_counter, msg

    def _get_fallback(self, frm_node_class):
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

    def resolve_node_class(self, node_info, inpt):
        """
        Resolves the node class from a node info.
        """
        klass = node_info.do_lookup(type(inpt))
        node_class = self.node_class_map.subsetget(klass)
        if node_class is None:
            raise NoSuitableNodeClass(klass)
        return node_class.get_subclass(klass=klass, **node_info.kwargs)

    def improvise_schema(self, obj, node_class):
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

    def __init__(self, cast, items_iter, in_schema, out_schema):
        self.cast = cast
        self.items_iter = items_iter
        self.in_schema = in_schema
        self.out_schema = out_schema

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
                to=self.out_schema[key],
                frm=self.in_schema[key]
            )
        return key, casted_value


class SchemaError(TypeError): pass
class SchemaNotValid(SchemaError): pass
class SchemasDontMatch(SchemaError): pass

class CompiledSchema(object):

    def __init__(self, in_schema, out_schema):
        self.validate_schema(in_schema)
        self.validate_schema(out_schema)
        self.validate_schemas_match(in_schema, out_schema)

    @classmethod
    def validate_schemas_match(cls, in_schema, out_schema):
        if AttrDict.KeyAny in in_schema:
            if not AttrDict.KeyAny in out_schema:
                raise SchemasDontMatch("in_schema contains 'KeyAny', but out_schema doesn't")
        elif AttrDict.KeyFinal in in_schema or AttrDict.KeyFinal in out_schema:
            if not (AttrDict.KeyFinal in in_schema and AttrDict.KeyFinal in out_schema):
                raise SchemasDontMatch("both in_schema and out_schema must contain 'KeyFinal'")
        elif AttrDict.KeyAny in out_schema:
            pass
        elif set(out_schema) >= set(in_schema):
            pass
        else:
            raise SchemasDontMatch("out_schema doesn't contain '%s'" %
            list(set(in_schema) - set(out_schema)))

    @classmethod
    def validate_schema(cls, schema):
        if (AttrDict.KeyFinal in schema) and len(schema) != 1:
            raise SchemaNotValid("schema cannot contain several items if it contains 'KeyFinal'")

