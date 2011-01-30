from utils import FROM, TO

class ValidationError(Exception): pass

def validate_input(cast, data):
    if not isinstance(data, cast.conversion[FROM]):
        raise ValidationError('Wrong argument type for %s, expected : %s, got : %s' %\
            (cast, cast.conversion[FROM], type(data)))
