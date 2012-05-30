# -*- coding: utf-8 -*-
import copy

from node import NodeInfo, Node
from utils import ClassSetDict, AttrDict
from exceptions import NotIncludedError, NoNodeClassError


class Cast(object):

    def __init__(self, node_class_map, fallback_map={}):
        #TODO: fallback mightn't be needed, if checking type of dumped inpt
        self.node_class_map = ClassSetDict(node_class_map)
        self.fallback_map = ClassSetDict(fallback_map)
        self._depth_counter = 0
        self.debug = False

    def __call__(self, inpt, dumper=NodeInfo(), loader=NodeInfo()):
        self._depth_counter += 1

        # First, looking for a proper dumper for `inpt`.
        dschema = None
        if hasattr(inpt, '__dump__'):
            dumper = inpt
            inpt_iter = dumper.__dump__()
            if hasattr(inpt, '__dschema__'):
                dschema = inpt.__dschema__()
        else:
            # if neither `inpt` nor `dumper` actually have a `__dump__`
            # method, we need to find a suitable dumper from `node_class_map`.
            if not hasattr(dumper, '__dump__'):
                node_info = None
                if not isinstance(dumper, NodeInfo):
                    node_info = NodeInfo(dumper)
                else:
                    node_info = copy.copy(dumper)
                    if node_info.class_info is None:
                        node_info.class_info = [type(inpt)]
                dumper = self._resolve_node_class(inpt, node_info)

            inpt_iter = dumper.__dump__(inpt)
            if hasattr(dumper, '__dschema__'):
                dschema = dumper.__dschema__(inpt)

        if dschema is None:
            dschema = self.default_dschema()
        dschema = AttrDict(dschema)

        # if `loader` doesn't actually have a `__load__` method,
        # we need to find a suitable loader from `node_class_map`,
        # or `fallback_map`.
        if not hasattr(loader, '__load__'):
            node_info = None
            if not isinstance(loader, NodeInfo):
                node_info = NodeInfo(loader)
            else:
                node_info = copy.copy(loader)

            # If the NodeInfo doesn't provide any useful `class_info` about
            # the node class, we directly try to find a good fallback.
            if node_info.class_info is None:
                loader = self._get_fallback(inpt, dumper)
            else:
                loader = self._resolve_node_class(inpt, node_info)

        if hasattr(loader, '__lschema__'):
            lschema = loader.__lschema__()
        else:
            lschema = self.default_lschema()
        lschema = AttrDict(lschema)

        # Generator iterating on the dumped data, and which will be passed
        # to the loader. Calls the casting recursively if the schema has any nesting.
        generator = _Generator(self, inpt_iter, dschema, lschema)

        # Finally, we load the casted object.
        #self.log('%s <= %s' % (frm_node_class, inpt))
        casted = loader.__load__(generator)
        #self.log('%s => %s' % (loader, casted))
        self._depth_counter -= 1
        return casted

    def default_dschema(self):
        return {AttrDict.KeyAny: NodeInfo()}

    def default_lschema(self):
        return {AttrDict.KeyAny: NodeInfo()}

    def log(self, msg):
        if self.debug: print '\t' * self._depth_counter, msg

    def _get_fallback(self, inpt, dumper):
        """
        Gets a fallback node class for the output, as a last resort.
        """
        # we try to get a node class from the `fallback_map`
        node_class = self.fallback_map.subsetget(type(inpt))
        if not node_class is None:
            return node_class
        elif hasattr(dumper, '__load__'):
            return dumper
        else:
            raise NoNodeClassError('Couldn\'t find a fallback for %s' % inpt)

    def _resolve_node_class(self, inpt, node_info):
        """
        Resolves the node class from a node info.
        """
        # TODO: duck typing (get_subclass could be a function).
        klass = node_info.get_class(type(inpt))
        if not issubclass(klass, Node):
            node_class = self.node_class_map.subsetget(klass)
            if node_class is None:
                raise NoNodeClassError(klass)
            return node_class.get_subclass(klass=klass, **node_info.kwargs)
        # If the value picked is a node class, we use that.
        else:
            return klass.get_subclass(**node_info.kwargs)


class _Generator(object):
    """
    Generator used to pass the data from one node to another.
    """

    def __init__(self, cast, items_iter, dschema, lschema):
        self.cast = cast
        self.items_iter = items_iter
        self.dschema = dschema
        self.lschema = lschema

    def __iter__(self):
        return self
        
    def next(self):
        key, value = self.items_iter.next()
        self.last_key = key
        if key is AttrDict.KeyFinal:
            casted_value = value
        else:
            if not key in self.lschema:
                raise NotIncludedError("loader schema doesn't contain key '%s'" % key)
            self.cast.log('[ %s ]' % key)
            casted_value = self.cast(value,
                dumper=self.dschema[key],
                loader=self.lschema[key],
            )
        return key, casted_value

