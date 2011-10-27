# -*- coding: utf-8 -*-
from bundle import Bundle, IdentityBundle
from utils import AllSubSetsOf, Singleton, ClassSet


class NoSuitableBundleClass(Exception): pass


class Cast(object):

    def __init__(self, bundle_class_map, fallback_map={}):
        self.bundle_class_map = bundle_class_map
        self.fallback_map = fallback_map

    def __call__(self, inpt, in_class=None, out_class=None):
        # `in_class` is always known, because we at least have the 
        # `inpt`'s class
        if in_class in [None, Bundle.ValueUnknown]:
            in_class = type(inpt)
        if not issubclass(in_class, Bundle):
            in_b_class = self.get_bundle_class(in_class, self.bundle_class_map)
        else:
            in_b_class = in_class
        in_schema = in_b_class.get_schema()
        # `out_class` can be unknown, and it that case, we find a good fallback 
        if out_class in [None, Bundle.ValueUnknown]:
            # If input is a final value, we'll just assume that ouput is also
            if Bundle.KeyFinal in in_schema:
                out_b_class = IdentityBundle
            else:
                out_b_class = self._get_fallback(in_class, out_class)
        elif not issubclass(out_class, Bundle):
            out_b_class = self.get_bundle_class(out_class, self.bundle_class_map)
            out_b_class = out_b_class.get_subclass(klass=out_class)
        else:
            out_b_class = out_class
        out_schema = out_b_class.get_schema()
        # Compiling schemas : if it fails with the 2 schemas found, we try to be clever
        # and guess the in_schema by bundling `inpt` and iterating over it.
        try:
            compiled = CompiledSchema(in_schema, out_schema)
        except SchemasDontMatch:
            in_schema = in_b_class(inpt).get_actual_schema()
            compiled = CompiledSchema(in_schema, out_schema) 
        self.log(inpt, in_b_class, in_schema, out_b_class, out_schema)
        # realize the casting
        def generator():
            for key, value in in_b_class(inpt):
                if key is Bundle.KeyFinal:
                    casted_value = value
                else:
                    # recursive call      
                    casted_value = self(value,
                        out_class=compiled.get_out_class(key),
                        in_class=compiled.get_in_class(key)
                    )
                yield key, casted_value
        return out_b_class.factory(generator()).obj

    def log(self, inpt, in_b_class, in_schema, out_b_class, out_schema):
        print '%s\n%s-%s => %s-%s\n' % (inpt, in_b_class.__name__, in_schema, out_b_class.__name__, out_schema) 

    def _get_fallback(self, in_class, out_class):
        if issubclass(in_class, Bundle):
            in_class = in_class.klass
        # we try to get a bundle from the `fallback_map`
        try:
            return self.get_bundle_class(in_class, self.fallback_map)
        except NoSuitableBundleClass:
            pass
        # Or we'll just try to build a bundle with `in_class`, so
        # that operation would be an identity.
        try:
            out_b_class = self.get_bundle_class(in_class, self.bundle_class_map)
        except NoSuitableBundleClass:
            raise NoSuitableBundleClass("out_class is 'ValueUnknown', and no fallback could be found")
        else:
            return out_b_class.get_subclass(klass=in_class)

    @classmethod
    def get_bundle_class(cls, klass, bundle_class_map):
        class_sets = set(filter(lambda cs: klass <= cs, bundle_class_map))
        # Eliminate supersets
        for cs1 in class_sets.copy():
            for cs2 in class_sets.copy():
                if cs1 <= cs2 and not cs1 is cs2:
                    class_sets.discard(cs2)
        try:
            best_match = list(class_sets)[0]
        except IndexError:
            raise NoSuitableBundleClass('%s' % klass)
        return bundle_class_map[best_match]


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
