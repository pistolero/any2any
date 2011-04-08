from base import Cast, CastSettings, Mm, Spz

class Identity(Cast):
    """
    Identity operation. Default cast for the conversion **(object, object)**.

        >>> Identity()('1')
        '1'
    """
    defaults = CastSettings(
        mm=Mm(object, object)
    )

    def call(self, obj):
        return obj


class ContainerCast(Cast):
    """
    Base cast for container types. This class is virtual. The casting goes this way ::

        SomeContainer(obj1, ..., objN) ----> SomeContainer(obj1_converted, ..., objN_converted)

    Which means that only the content is converted.

    Settings:
        The serializer to use for the container's elements
    """

    defaults = CastSettings(
        element_cast=None,
    )

    def new_container(self, items_iterator):
        raise NotImplementedError('This class is virtual')

    def container_iter(self, container):
        """
        Returns an iterator on pairs **(index, value)**, where *index* and *value* are such as ::
        
            container[index] == value
        """
        raise NotImplementedError('This class is virtual')

    def call(self, container):
        return self.new_container(self.items(container))

    def items(self, container):
        elem_cast = self._cast_for_elem()
        for index, value in self.container_iter(container):
            yield(index, elem_cast(value))

    @property
    def elem_mm(self):
        return Mm(self.mm.from_any.feature, self.mm.to.feature)

    def _cast_for_elem(self):
        return self.element_cast or self.cast_for(self.elem_mm, {'mm': self.elem_mm})


class MappingCast(ContainerCast):
    """
    Cast for dictionaries.

        >>> MappingCast()({'1': anObject1, '2': anObject2})
        {'1': 'its converted version 1', '2': 'its converted version 2'}
    """
    def container_iter(self, container):
        return container.items()

    def new_container(self, items_iterator):
        return self.mm.to.base(items_iterator)


class SequenceCast(ContainerCast):
    """
    Cast for lists and tuples.

        >>> SequenceCast()([anObject1, anObject2])
        ['its converted version 1', 'its converted version 2']
    """

    def container_iter(self, container):
        return enumerate(container)

    def new_container(self, items_iterator):
        return self.mm.to.base([item[1] for item in items_iterator])

