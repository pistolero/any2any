.. currentmodule:: any2any

..
    >>> import os, sys
    >>> sys.path.append(os.path.abspath("../.."))

How any2any works 
+++++++++++++++++++

Analysing sandwich serialization
#################################

If we take our :ref:`example<demonstration-ref>` with sandwiches and fillings, here is the representation of what actually happens when we use :meth:`SandwichSrz.spit`. Serializers are represented as triangles, input on the left, output on the right.

.. image:: ../images/schema_demonstration.png
    :scale: 70 %

As this schema illustrates, **any2any** is based on two principles :

    1. **All (de)serializations are treated as a recursive operations.** Each serializer:
    
        * Decomposes (de)serialization in sub-operations
        * Delegates those sub-operations to other serializers (this implies to be able to find an appropriate serializer for any Python instance, see 2. ;-)
        * Combines the sub-operations' results

    2. **There is a suitable serializer for every single python class.** So it is always possible to delegate. Indeed, the identity is the simplest operation, and that's why :class:`base.IdentitySrz` is used by default for instances of :class:`object`.

Flexibility and code re-use
##############################

This architecture allows both a lot of flexibility, and a lot of code re-use.

**Code re-use** because each serializer does only a minimum amount of work, and delegates the rest.

**Code re-use** also because the most common (de)serialization patterns are already implemented (:class:`base.ContainerSrz`, :class:`objectsrz.ObjectSrz`, ...).

**Flexibility** because you can tweak at will the provided serializers.

**Flexibility** also because if tweaking's not enough, you can always write your own serializer from scratch and plug-it in.

Next
#####

The more common patterns for ``decomposing in sub-operations, delegating sub-operations, combining`` are actually already implemented by **any2any**, so you don't need to write to much code. Most of the time you'll just need to subclass one of these serializers : :class:`ObjectSrz`, :class:`ContainerSrz` or :class:`IdentitySrz`.

Facilities for finding a serializer, given a Python class, are implemented by :class:`Serializer`. For more info on how **any2any** maps a Python class to a serializer, and on how to customize this mapping go here.
