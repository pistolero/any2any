from django.db.models.fields.related import ManyRelatedObjectsDescriptor, ForeignRelatedObjectsDescriptor

from any2any.utils import classproperty
from any2any.django.node import QUERYSET_FIELDS

class ModelIntrospector(object):
    """
    Mixin for adding introspection capabilities to any class.
    """

    @classproperty
    def fields(cls):
        # Returns a set with all the fields,
        # but excluding the pointers used for MTI
        mod_opts = cls.model._meta
        ptr_fields = cls.collect_ptrs(cls.model)
        all_fields = mod_opts.fields + mod_opts.many_to_many
        return set(all_fields) - set(ptr_fields)

    @classproperty
    def fields_dict(cls):
        # Returns a dictionary `{<field_name>, <field>}`
        return dict(((f.name, f) for f in cls.fields))

    @classproperty
    def related_dict(cls):
        # Returns a dictionary {<attr_name>: <descriptor>} with all the related descriptors
        def retrieve_desc((k, v)):
            return isinstance(v, (ManyRelatedObjectsDescriptor,
            ForeignRelatedObjectsDescriptor))
        return dict(filter(retrieve_desc, cls.model.__dict__.items()))

    @classproperty
    def all_dict(cls):
        # Returns a dictionary {<attr_name>: <attr>} with fields and related.
        return dict(cls.related_dict, **cls.fields_dict)

    @classproperty
    def pk_field_name(cls):
        # We get pk's field name from the "super" parent (i.e. the "eldest").
        # This allows to handle MTI nicely (and transparently).
        all_pks = set([p._meta.pk for p in cls.model._meta.get_parent_list()])
        all_pks.add(cls.model._meta.pk)
        all_ptrs = set(cls.collect_ptrs(cls.model))
        return list(all_pks - all_ptrs)[0].name

    @classproperty
    def pk_field(cls):
        return cls.fields_dict[cls.pk_field_name]

    @classmethod
    def collect_ptrs(cls, model):
        # Recursively collects all the fields pointing to parents of `model`
        ptr_fields = []
        for parent_model, ptr_field in model._meta.parents.iteritems():
            ptr_fields.append(ptr_field)
            ptr_fields += cls.collect_ptrs(parent_model)
        return ptr_fields

    @classmethod
    def is_queryset_field(cls, key):
        return isinstance(cls.all_dict[key], QUERYSET_FIELDS)
