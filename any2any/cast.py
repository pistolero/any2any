# -*- coding: utf-8 -*-
import copy

from bundle import Bundle, IdentityBundle, BundleInfo
from utils import AllSubSetsOf, Singleton, ClassSet, ClassSetDict, SmartDict


class Cast(object):

    def __init__(self, bundle_class_map, fallback_map={}):
        self.bundle_class_map = ClassSetDict(bundle_class_map)
        self.fallback_map = ClassSetDict(fallback_map)

    def __call__(self, inpt, in_class=None, out_class=None):
        # `in_class` is always known, because we at least have the 
        # `inpt`'s class
        if in_class in [None, SmartDict.ValueUnknown]:
            in_class = type(inpt)
        if not isinstance(in_class, BundleInfo):
            in_value_info = BundleInfo(in_class)
        else:
            in_value_info = in_class
        in_bundle_class = in_value_info.get_bundle_class(inpt, self.bundle_class_map)

        # `out_class` can be unknown, and it that case, we find a good fallback 
        if out_class in [None, SmartDict.ValueUnknown]:
            out_value_info = BundleInfo(self._get_fallback(in_bundle_class))
        elif (not isinstance(out_class, BundleInfo)):
            out_value_info = BundleInfo(out_class)
        else:
            out_value_info = out_class
        out_bundle_class = out_value_info.get_bundle_class(inpt, self.bundle_class_map)

        # Compiling schemas : if it fails with the 2 schemas found,
        # we use the actual schema of `inpt`
        out_schema = out_bundle_class.get_schema()
        in_schema = in_bundle_class.get_schema()
        try:
            compiled = CompiledSchema(in_schema, out_schema)
        except SchemasDontMatch:
            in_schema = in_bundle_class(inpt).get_actual_schema()
            compiled = CompiledSchema(in_schema, out_schema)

        # realize the casting
        def generator():
            for key, value in in_bundle_class(inpt):
                if key is SmartDict.KeyFinal:
                    casted_value = value
                else:
                    # recursive call      
                    casted_value = self(value,
                        out_class=out_schema[key],
                        in_class=in_schema[key]
                    )
                yield key, casted_value
        return out_bundle_class.build(generator()).obj

    def log(self, inpt, in_value_info, in_schema, out_value_info, out_schema):
        pass
        #print '%s\n%s-%s => %s-%s\n' % (inpt, in_value_info.__name__, in_schema, out_value_info.__name__, out_schema) 

    def _get_fallback(self, in_bundle_class):
        # If input is a final value, we'll just assume that ouput is also
        if SmartDict.KeyFinal in in_bundle_class.get_schema():
            return in_bundle_class

        # we try to get a bundle class from the `fallback_map`
        bundle_class = self.fallback_map.subsetget(in_bundle_class.klass)
        if not bundle_class is None:
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
        elif (SmartDict.KeyAny in schema) and len(schema) != 1:
            raise SchemaNotValid("schema cannot contain several items if it contains 'KeyAny'")

