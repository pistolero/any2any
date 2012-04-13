class NoNodeClassError(Exception):
    """Error raised by :class:`Cast`, when no suitable node class could be found for the transformation."""
    pass

class NotIncludedError(ValueError):
    """Error raised by :meth:`AttrDict.validate_match`, when the validation failed."""
    pass
