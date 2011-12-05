# -*- coding: utf-8 -*-
import copy

from bundle import Bundle, IdentityBundle, ValueInfo, NoSuitableBundleClass
from utils import AllSubSetsOf, Singleton, ClassSet


class Cast(object):

    def __init__(self, bundle_class_map, fallback_map={}):
        self.bundle_class_map = bundle_class_map
        self.fallback_map = fallback_map

    def __call__(self, inpt, in_class=None, out_class=None):
        # `in_class` is always known, because we at least have the 
        # `inpt`'s class
        if in_class in [None, Bundle.ValueUnknown]:
            in_class = type(inpt)
        in_value_info = ValueInfo(in_class)
        in_bundle_class = in_value_info.get_bundle_class(self.bundle_class_map)
        # `out_class` can be unknown, and it that case, we find a good fallback 
        if out_class in [None, Bundle.ValueUnknown]:
            out_value_info = ValueInfo(self._get_fallback(in_bundle_class))
        else:
            out_value_info = ValueInfo(out_class)
        out_bundle_class = out_value_info.get_bundle_class(self.bundle_class_map)
        # Compiling schemas : if it fails with the 2 schemas found,
        # we use the actual schema of `inpt`
        try:
            compiled = CompiledSchema(in_bundle_class.get_schema(), out_bundle_class.get_schema())
        except SchemasDontMatch:
            in_schema = in_bundle_class(inpt).get_actual_schema()
            compiled = CompiledSchema(in_schema, out_bundle_class.get_schema())
        # realize the casting
        def generator():
            for key, value in in_bundle_class(inpt):
                if key is Bundle.KeyFinal:
                    casted_value = value
                else:
                    # recursive call      
                    casted_value = self(value,
                        out_class=compiled.get_out_class(key),
                        in_class=compiled.get_in_class(key)
                    )
                yield key, casted_value
        return out_bundle_class.build(generator()).obj

    def log(self, inpt, in_value_info, in_schema, out_value_info, out_schema):
        pass
        #print '%s\n%s-%s => %s-%s\n' % (inpt, in_value_info.__name__, in_schema, out_value_info.__name__, out_schema) 

    def _get_fallback(self, in_bundle_class):
        # If input is a final value, we'll just assume that ouput is also
        if Bundle.KeyFinal in in_bundle_class.get_schema():
            return in_bundle_class
        # we try to get a bundle class from the `fallback_map`
        try:
            bundle_class = ClassSet.pick_best(
                in_bundle_class.klass,
                self.fallback_map,
                exc_type=NoSuitableBundleClass
            )
        except NoSuitableBundleClass:
            pass
        else:
            return bundle_class
        # Or we'll just use `in_bundle_class`, so that operation is an identity.
        return in_bundle_class # TODO: shouldn't this rather be an error ?


class SchemaError(TypeError): pass
class SchemaNotValid(SchemaError): pass
class SchemasDontMatch(SchemaError): pass


class CompiledSchema(object):

    def __init__(self, in_schema, out_schema):
        self.validate_schema(in_schema)
        self.validate_schema(out_schema)
        self.validate_schemas_match(in_schema, out_schema)
        self.in_schema = in_schema
        self.out_schema = out_schema
        self._get_in_class = self.compile_schema(in_schema)
        self._get_out_class = self.compile_schema(out_schema)

    @classmethod
    def validate_schemas_match(cls, in_schema, out_schema):
        if Bundle.KeyAny in in_schema:
            if not Bundle.KeyAny in out_schema:
                raise SchemasDontMatch("in_schema contains 'KeyAny', but out_schema doesn't")
        elif Bundle.KeyFinal in in_schema or Bundle.KeyFinal in out_schema:
            if not (Bundle.KeyFinal in in_schema and Bundle.KeyFinal in out_schema):
                raise SchemasDontMatch("both in_schema and out_schema must contain 'KeyFinal'")
        elif Bundle.KeyAny in out_schema:
            pass
        elif set(out_schema) >= set(in_schema):
            pass
        else:
            raise SchemasDontMatch("out_schema doesn't contain '%s'" %
            list(set(in_schema) - set(out_schema)))

    @classmethod
    def validate_schema(cls, schema):
        if (Bundle.KeyFinal in schema) and len(schema) != 1:
            raise SchemaNotValid("schema cannot contain several items if it contains 'KeyFinal'")
        elif (Bundle.KeyAny in schema) and len(schema) != 1:
            raise SchemaNotValid("schema cannot contain several items if it contains 'KeyAny'")

    def compile_schema(self, schema):
        if Bundle.KeyAny in schema:
            klass = schema[Bundle.KeyAny]
            def get_class(key):
                return klass
        else:
            def get_class(key):
                return schema[key]
        return get_class

    def get_out_class(self, key):
        return self._get_out_class(key)

    def get_in_class(self, key):
        return self._get_in_class(key)
