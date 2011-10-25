# -*- coding: utf-8 -*-
from bundle import Bundle
from utils import AllSubSetsOf, Singleton, ClassSet


class NoSuitableBundleClass(Exception): pass


class Cast(object):

    def __init__(self, bundle_class_map):
        self.bundle_class_map = bundle_class_map

    def __call__(self, inpt, to=None):
        # bundles input, finds an output bundle class
        in_bundle_class = self.get_bundle_class(type(inpt))
        out_bundle_class = self.get_bundle_class(to)
        # match schemas
        in_schema = in_bundle_class.get_schema()
        out_schema = out_bundle_class.get_schema()
        compiled = CompiledSchema(in_schema, out_schema)
        # realize the casting
        def generator():
            for key, value in in_bundle_class(inpt):
                if key is Bundle.KeyFinal:
                    casted_value = value
                else:
                    # recursive call      
                    casted_value = self(value, to=compiled.get(key))
                yield key, casted_value
        return out_bundle_class.factory(generator()).obj

    def get_bundle_class(self, klass):
        if issubclass(klass, Bundle):
            return klass
        class_sets = set(filter(lambda cs: klass <= cs, self.bundle_class_map))
        # Eliminate supersets
        for cs1 in class_sets.copy():
            for cs2 in class_sets.copy():
                if cs1 <= cs2 and not cs1 is cs2:
                    class_sets.discard(cs2)
        try:
            best_match = list(class_sets)[0]
        except IndexError:
            raise NoSuitableBundleClass()
        bundle_class = self.bundle_class_map[best_match]
        return type(bundle_class.__name__, (bundle_class,), {'klass': klass})


class SchemaError(TypeError): pass
class SchemaNotValid(SchemaError): pass
class SchemasDontMatch(SchemaError): pass


class CompiledSchema(object):

    def __init__(self, in_schema, out_schema):
        self.validate_schema(in_schema)
        self.validate_schema(out_schema)
        self.in_schema = in_schema
        self.out_schema = out_schema
        self._get_out_class = None
        if (set(out_schema) <= set(in_schema)):
            if Bundle.KeyFinal in out_schema:
                def get_out_class(key):
                    return out_schema[key]
            elif Bundle.KeyAny in out_schema:
                out_class = out_schema[Bundle.KeyAny]
                def get_out_class(key):
                    return out_class
            else:
                def get_out_class(key):
                    return out_schema[key]
        elif Bundle.KeyFinal in in_schema:
            raise SchemasDontMatch("both schemas must contain 'KeyFinal'")
        elif Bundle.KeyAny in out_schema:
            out_class = out_schema[Bundle.KeyAny]
            def get_out_class(key):
                return out_class
        else:
            raise SchemasDontMatch("in_schema doesn't provide '%s'" % list(set(out_schema) - set(in_schema)))
        self._get_out_class = get_out_class

    @classmethod
    def validate_schema(cls, schema):
        if (Bundle.KeyFinal in schema) and len(schema) != 1:
            raise SchemaNotValid("schema cannot contain several items if it contains 'KeyFinal'")
        elif (Bundle.KeyAny in schema) and len(schema) != 1:
            raise SchemaNotValid("schema cannot contain several items if it contains 'KeyAny'")

    def get(self, key):
        return self._get_out_class(key)
