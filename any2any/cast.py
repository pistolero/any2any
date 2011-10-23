# -*- coding: utf-8 -*-


class NoSuitableBundleClass(Exception): pass

    
class Cast(object):

    bundle_class_list = []

    def __call__(self, inpt, to=None, d=False):
        if d:
            import pdb; pdb.set_trace()
        try:
            bundle = self.bundle_from_obj(inpt)
        except NoSuitableBundleClass:
            return inpt
        to_bundle_class = self.bundle_class(to)
        final_dict = dict()
        for key, value in bundle:
            item_to = to_bundle_class.get_class(key)
            item_final = any2any(value, item_to)
            final_dict[key] = value
        return to_bundle_class.factory(final_dict).obj

    def bundle_from_obj(self, obj):
        return bundle_class(type(obj), self.bundle_class_list)(obj)

    def is_usable(self, bundle_class, for_class):
        return bundle_class.use_for >= for_class

    def bundle_class(self, klass):
        bundle_classes = set(filter(lambda b: is_usable(b, klass), self.bundle_class_list))
        for m1 in bundle_classes.copy():
            for m2 in bundle_classes.copy():
                if m1 <= m2 and not m1 is m2:
                    bundle_classes.discard(m2)
        try:
            return list(bundle_classes)[0]
        except IndexError:
            raise NoSuitableBundleClass()
