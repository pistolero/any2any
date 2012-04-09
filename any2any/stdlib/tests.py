from nose.tools import ok_, assert_raises

from any2any.cast import Cast
from any2any.utils import AllSubSetsOf, Singleton
from any2any.node import *
from any2any.stdlib.node import *


class DateNode_Test(object):
    """
    Test DateNode
    """
    
    def setUp(self):
        self.serializer = Cast({
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): IdentityNode,
        }, {
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): MappingNode,
        })

        self.deserializer = Cast({
            AllSubSetsOf(dict): MappingNode,
            AllSubSetsOf(list): IterableNode,
            AllSubSetsOf(object): IdentityNode,
        })

    def serialize_date_test(self):
        """
        Test serialize date with DateNode
        """
        d = datetime.date(year=1900, month=1, day=1)
        ok_(self.serializer(d, in_class=DateNode) == {
            'year': 1900, 'month': 1, 'day': 1
        })

    def deserialize_date_test(self):
        """
        Test deserialize date with DateNode
        """
        d = self.deserializer({
            'year': 1906, 'month': 1, 'day': 12
        }, out_class=DateNode)
        ok_(isinstance(d, datetime.date))
        ok_(d.year == 1906)
        ok_(d.month == 1)
        ok_(d.day == 12)


class DateTimeNode_Test(DateNode_Test):

    def serialize_date_test(self):
        """
        Test serialize date with DateNode
        """
        d = datetime.datetime(year=2300, month=12, day=31, microsecond=6)
        ok_(self.serializer(d, in_class=DateTimeNode) == {
            'year': 2300, 'month': 12, 'day': 31, 'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 6
        })

    def deserialize_date_test(self):
        """
        Test deserialize date with DateNode
        """
        d = self.deserializer({
            'year': 1995, 'month': 6, 'day': 8, 'hour': 8
        }, out_class=DateTimeNode)
        ok_(isinstance(d, datetime.datetime))
        ok_(d.year == 1995)
        ok_(d.month == 6)
        ok_(d.day == 8)
        ok_(d.hour == 8)
        ok_(d.minute == 0)
