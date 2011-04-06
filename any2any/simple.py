from base import Cast

class Identity(Cast):
    """
    Identity operation. Default cast for the conversion **(object, object)**.

        >>> Identity()('1')
        '1'
    """

    def call(self, obj):
        return obj

class ContainerCast(Cast):
    """
    Base cast for container types. This class is virtual. The casting goes this way ::

        SomeContainer(obj1, ..., objN) ----> SomeContainer(obj1_converted, ..., objN_converted)

    Which means that only the content is converted.
    """

    class Settings:
        conversion = (object, object)

    @classmethod
    def new_container(cls):
        """
        Returns an empty container.
        """
        raise NotImplementedError('This class is virtual')

    @classmethod
    def container_iter(cls, container):
        """
        Returns an iterator on pairs **(index, value)**, where *index* and *value* are such as ::
        
            container[index] == value
        """
        raise NotImplementedError('This class is virtual')

    @classmethod
    def container_insert(cls, container, index, value):
        """
        Inserts *value* at *index* in container.
        """
        raise NotImplementedError('This class is virtual')

    @classmethod
    def reset_container(self, container):
        """
        Empties *container*.
        """
        raise NotImplementedError('This class is virtual')

    def call(self, obj):
        new_container = self.new_container()
        elem_conversion = (self.conversion[FROM].feature, self.conversion[TO].feature)
        elem_cast = self.cast_for(elem_conversion, {'conversion': elem_conversion})
        for index, value in self.container_iter(obj):
            self.container_insert(new_container, index, elem_cast(value))
        return new_container

class MappingCast(ContainerCast):
    """
    Cast for dictionaries.

        >>> MappingCast()({'1': anObject1, '2': anObject2})
        {'1': 'its converted version 1', '2': 'its converted version 2'}
    """
    
    @classmethod
    def new_container(cls):
        return dict()
    
    @classmethod
    def container_iter(cls, container):
        return container.items()
    
    @classmethod
    def container_insert(cls, container, index, value):
        container[index] = value

    @classmethod
    def reset_container(cls, container):
        container.clear()
    

class SequenceCast(ContainerCast):
    """
    Cast for lists and tuples.

        >>> SequenceCast()([anObject1, anObject2])
        ['its converted version 1', 'its converted version 2']
    """

    @classmethod
    def new_container(cls):
        return list()
    
    @classmethod
    def container_iter(cls, container):
        return enumerate(container)
    
    @classmethod
    def container_insert(cls, container, index, value):
        container.insert(index, value)

    @classmethod
    def reset_container(cls, container):
        for index in range(0, len(container)):
            container.pop()

