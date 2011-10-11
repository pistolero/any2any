`any2any.daccasts`
+++++++++++++++++++

.. currentmodule:: any2any.daccasts

DivideAndConquerCast
=====================

.. autoclass:: DivideAndConquerCast

    .. automethod:: iter_input
    .. automethod:: iter_output
    .. automethod:: build_output
    .. automethod:: get_item_from
    .. automethod:: get_item_to

Mixins for DivideAndConquerCast
================================

.. autoclass:: CastItems

    **Available settings :**
    
    .. autoattribute:: key_to_cast
    .. autoattribute:: value_cast
    .. autoattribute:: key_cast

    **Members :**

    .. automethod:: iter_output
    .. automethod:: strip_item

.. autoclass:: FromIterable
.. autoclass:: ToIterable
.. autoclass:: FromMapping
.. autoclass:: ToMapping
.. autoclass:: FromObject
.. autoclass:: ToObject

Wraps
========

.. autoclass:: ObjectWrap
    :members:
    :show-inheritance:
.. autoclass:: WrappedObject
.. autoclass:: ContainerWrap
    :members:
.. autoclass:: WrappedContainer
