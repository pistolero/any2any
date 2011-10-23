# -*- coding: utf-8 -*-


class NoSuitableBundleClass(Exception): pass

    
class Cast(object):

    bundle_class_list = []

    def __call__(self, inpt, to=None):
        bundle = self.build_bundle(inpt)
        to_bundle_class = self.get_bundle_class(to)
        casted_dict = {}
        for key, value in bundle:
            if key is Bundle.Final:
                casted_value = value
            else:
                value_to = to_bundle_class.get_class(key)        
                casted_value = any2any(value, value_to)
            casted_dict[key] = casted_value
        return to_bundle_class.factory(casted_dict).obj

    def build_bundle(self, obj):
        return bundle_class(type(obj), self.bundle_class_list)(obj)

    def is_usable(self, bundle_class, for_class):
        return bundle_class.use_for >= for_class

    def get_bundle_class(self, klass):
        if issubclass(klass, Bundle):
            return klass
        bundle_classes = set(filter(lambda b: self.is_usable(b, klass), self.bundle_class_list))
        for m1 in bundle_classes.copy():
            for m2 in bundle_classes.copy():
                if m1 <= m2 and not m1 is m2:
                    bundle_classes.discard(m2)
        try:
            return list(bundle_classes)[0]
        except IndexError:
            raise NoSuitableBundleClass()
