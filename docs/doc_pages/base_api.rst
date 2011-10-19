`any2any.base`
+++++++++++++++

.. currentmodule:: any2any.base

Casts
=======

.. autoclass:: Cast

    **Available Settings :**

    .. autoattribute:: Cast.from_
    .. autoattribute:: Cast.to
    .. autoattribute:: Cast.mm_to_cast
    .. autoattribute:: extra_mm_to_cast
    .. autoattribute:: Cast.from_wrapped
    .. autoattribute:: Cast.to_wrapped
    .. autoattribute:: Cast.logs

    **Members :**

    .. automethod:: Cast.call(inpt)
    .. automethod:: Cast.cast_for(mm)
    .. automethod:: Cast.set_debug_on
    .. automethod:: Cast.set_debug_off

.. autoclass:: CastStack

    .. autoattribute:: CastStack.call(inpt, from_=None, to=None)

Settings
=========

.. autoclass:: Setting
    :members:
