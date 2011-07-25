# -*- coding: utf-8 -*-
# TODO: document + tests
try:
    import abc
except ImportError:
    from compat import abc
from containercast import ContainerCast

class RouteToOperands(ContainerCast):

    defaults = dict(
        operands = []
    )

    def iter_output(self, items_iter):
        for key, value in items_iter:            
            yield key, self.operands[key](value)

class ConcatDict(ContainerCast):

    def build_output(self, items_iter):
        concat_dict = {}
        for key, value in items_iter:
            concat_dict.update(value)
        return concat_dict

class SplitDict(ContainerCast):
    
    defaults = dict(
        key_to_route = {}
    )

    def iter_input(self, inpt):
        dict_list = [dict() for o in self.operands]
        for key, value in inpt.iteritems():
            ind = self.route(key, value)
            dict_list[ind][key] = value
        return enumerate(dict_list)
    
    @abc.abstractmethod
    def get_route(self, key, value):
        return

    def route(self, key, value):
        if key in self.key_to_route:
            return self.key_to_route[key]
        else:
            return self.get_route(key, value)
