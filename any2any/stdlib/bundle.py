import datetime

from any2any.bundle import ObjectBundle


class DateBundle(ObjectBundle):

    klass = datetime.date

    @classmethod
    def default_schema(cls):
        return {
            'year': int,
            'month': int,
            'day': int,
        }


class DateTimeBundle(ObjectBundle):

    klass = datetime.datetime
    
    @classmethod
    def default_schema(cls):
        return {
            'year': int,
            'month': int,
            'day': int,
            'hour': int,
            'minute': int,
            'second': int,
            'microsecond': int,
        }
