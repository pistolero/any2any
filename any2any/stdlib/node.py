import datetime

from any2any.node import ObjectNode


class DateNode(ObjectNode):

    klass = datetime.date

    @classmethod
    def common_schema(cls):
        return {
            'year': int,
            'month': int,
            'day': int,
        }

    @classmethod
    def schema_dump(cls):
        return cls.common_schema()

    @classmethod
    def schema_load(cls):
        return cls.common_schema()


class DateTimeNode(ObjectNode):

    klass = datetime.datetime
    
    @classmethod
    def common_schema(cls):
        return {
            'year': int,
            'month': int,
            'day': int,
            'hour': int,
            'minute': int,
            'second': int,
            'microsecond': int,
        }

    @classmethod
    def schema_dump(cls):
        return cls.common_schema()

    @classmethod
    def schema_load(cls):
        return cls.common_schema()
