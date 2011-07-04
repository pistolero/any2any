# -*- coding: utf-8 -*-
# TODO: document + tests
try:
    import abc
except ImportError:
    from compat import abc
from base import Cast

class CombineCast(Cast):

    defaults = dict(
        operands = []
    )
        
    @abc.abstractmethod
    def iter_input(self, inpt):
        return

    @abc.abstractmethod
    def build_output(self, values_iter):
        return

    def iter_output(self, values_iter):
        for ind, value in enumerate(values_iter):            
            yield self.operands[ind](value) 

    def call(self, inpt):
        iter_input = self.iter_input(inpt)
        iter_ouput = self.iter_output(iter_input)
        return self.build_output(iter_ouput)

class ToConcatDict(CombineCast):

    def build_output(self, values_iter):
        concat_dict = {}
        for value in values_iter:
            concat_dict.update(value)
        return concat_dict

class FromConcatDict(CombineCast):
    
    defaults = dict(
        key_to_route = {}
    )

    def iter_input(self, inpt):
        dict_list = [dict() for o in self.operands]
        for key, value in inpt.iteritems():
            ind = self.route(key, value)
            dict_list[ind][key] = value
        return iter(dict_list)
    
    @abc.abstractmethod
    def get_route(self, key, value):
        return

    def route(self, key, value):
        if key in self.key_to_route:
            return self.key_to_route[key]
        else:
            return self.get_route(key, value)
