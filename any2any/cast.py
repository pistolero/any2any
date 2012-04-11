# -*- coding: utf-8 -*-
import copy

from node import NodeInfo
from utils import ClassSetDict, SmartDict


class Cast(object):

    def __init__(self, node_class_map, fallback_map={}):
        self.node_class_map = ClassSetDict(node_class_map)
        self.fallback_map = ClassSetDict(fallback_map)
        self._depth_counter = 0
        self.debug = False

    def __call__(self, inpt, in_class=None, out_class=None):
        self._depth_counter += 1

        # `in_class` is always known, because we at least have the 
        # `inpt`'s class
        if in_class in [None, SmartDict.ValueUnknown]:
            in_class = type(inpt)
        if not isinstance(in_class, NodeInfo):
            in_value_info = NodeInfo(in_class)
        else:
            in_value_info = in_class
        in_node_class = in_value_info.get_node_class(inpt, self.node_class_map)

        # `out_class` can be unknown, and it that case, we find a good fallback 
        if out_class in [None, SmartDict.ValueUnknown]:
            out_value_info = NodeInfo(self._get_fallback(in_node_class))
        elif (not isinstance(out_class, NodeInfo)):
            out_value_info = NodeInfo(out_class)
        else:
            out_value_info = out_class
        out_node_class = out_value_info.get_node_class(inpt, self.node_class_map)

        # Compiling schemas : if it fails with the 2 schemas found,
        # we use the actual schema of `inpt`
        out_schema = SmartDict(out_node_class.schema_load())
        in_schema = SmartDict(in_node_class.schema_dump())
        try:
            compiled = CompiledSchema(in_schema, out_schema)
        except SchemasDontMatch:
            in_schema = self.improvise_schema(inpt, in_node_class)
            compiled = CompiledSchema(in_schema, out_schema)

        # Generator iterating on the casted items, and which will be used
        # to load the casted object.
        # It calls the casting recursively if the schema has any nesting.
        generator = _Generator(self, in_node_class.new(inpt).dump(), in_schema, out_schema)

        # Finally, we load the casted object.
        self.log('%s <= %s' % (in_node_class, inpt))
        casted = out_node_class.load(generator).obj
        self.log('%s => %s' % (out_node_class, casted))
        self._depth_counter -= 1
        return casted

    def log(self, msg):
        if self.debug: print '\t' * self._depth_counter, msg

    def _get_fallback(self, in_node_class):
        # If input is a final value, we'll just assume that ouput is also
        if SmartDict.KeyFinal in in_node_class.schema_dump():
            return in_node_class

        # we try to get a node class from the `fallback_map`
        node_class = self.fallback_map.subsetget(in_node_class.klass)
        if not node_class is None:
            return node_class

        # Or we'll just use `in_node_class`, so that operation is an identity.
        return in_node_class # TODO: shouldn't this rather be an error ?

    def improvise_schema(self, obj, node_class):
        """
        This method can be used to get the dump schema for an object, when the
        schema obtained 'a priori' is not sufficient.
        """
        node = node_class.new(obj)
        schema = {}
        for k, v in node.dump():
            schema[k] = type(v)
        return SmartDict(schema)


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
        if key is SmartDict.KeyFinal:
            casted_value = value
        else:
            self.cast.log('[ %s ]' % key)
            casted_value = self.cast(value,
                out_class=self.out_schema[key],
                in_class=self.in_schema[key]
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
        if SmartDict.KeyAny in in_schema:
            if not SmartDict.KeyAny in out_schema:
                raise SchemasDontMatch("in_schema contains 'KeyAny', but out_schema doesn't")
        elif SmartDict.KeyFinal in in_schema or SmartDict.KeyFinal in out_schema:
            if not (SmartDict.KeyFinal in in_schema and SmartDict.KeyFinal in out_schema):
                raise SchemasDontMatch("both in_schema and out_schema must contain 'KeyFinal'")
        elif SmartDict.KeyAny in out_schema:
            pass
        elif set(out_schema) >= set(in_schema):
            pass
        else:
            raise SchemasDontMatch("out_schema doesn't contain '%s'" %
            list(set(in_schema) - set(out_schema)))

    @classmethod
    def validate_schema(cls, schema):
        if (SmartDict.KeyFinal in schema) and len(schema) != 1:
            raise SchemaNotValid("schema cannot contain several items if it contains 'KeyFinal'")

