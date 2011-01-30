A more complete example
--------------------------

For example, let's build a simple serializer for :class:`xml.dom.minidom.Node`.

    >>> from xml.dom.minidom import Element, parseString
    >>> from any2any.objectsrz import ObjectSrz, Accessor
    >>> class ChildNodesAccessor(Accessor):
    ...     def get_attr(self, obj, name):
    ...         return obj.childNodes
    ...     def set_attr(self, obj, name, value):
    ...         for child in value:
    ...             obj.appendChild(child)
    >>> class NodeAttrsAccessor(Accessor):
    ...     def get_attr(self, obj, name):
    ...         return obj.getAttribute(name)
    ...     def set_attr(self, obj, name, value):
    ...         obj.setAttribute(name, value)
    >>> class NodeSrz(ObjectSrz):
    ...     class Settings:
    ...         class_accessor_map = {object: NodeAttrsAccessor}
    >>> class FillingNodeSrz(NodeSrz):
    ...     class Settings:
    ...         include = ['name', 'kind']
    ...     def new_object(self, eaten_data):
    ...         return Element('filling')
    >>> class SandwichNodeSrz(NodeSrz):
    ...     class Settings:
    ...         include = ['name', 'bread', 'fillings']
    ...         attr_accessor_map = {'fillings': ChildNodesAccessor}
    ...         attr_class_map = {'fillings': (list, Filling)}
    ...         class_srz_map = {Filling: FillingNodeSrz}
    ...     def new_object(self, eaten_data):
    ...         return Element('sandwich')
    ... 
    >>> sandwich_xml = ''\
    ... '<sandwich name="The French" bread="baguette">'\
    ...     '<filling name="mustard" kind="sauce"/>'\
    ...     '<filling name="camembert" kind="cheese"/>'\
    ... '</sandwich>'
    >>> sandwich_node = parseString(sandwich_xml).firstChild
    >>> nodesrz = SandwichNodeSrz()
    >>> nodesrz.spit(sandwich_node) == {
    ...     'name': u'The French', 
    ...     'bread': u'baguette',
    ...     'fillings': [{
    ...         'kind': u'sauce', 
    ...         'name': u'mustard',
    ...     },
    ...     {
    ...         'kind': u'cheese', 
    ...         'name': u'camembert'
    ...     }],
    ... }
    True
 
    >>> from any2any.base import SrzWizard
    >>> class SandwichXMLSrz(SrzWizard):
    ...     class Settings:
    ...         eat_chain = [
    ...             lambda xml_str: parseString(xml_str).firstChild,
    ...             SandwichNodeSrz().spit,
    ...             SandwichSrz().eat,
    ...         ]
    ...         spit_chain = [
    ...             SandwichSrz().spit,
    ...             SandwichNodeSrz().eat,
    ...             lambda node: node.toxml(),
    ...         ]
    >>> import json, pickle
    >>> class SandwichJSONSrz(SrzWizard):
    ...     class Settings:
    ...         eat_chain = [
    ...             json.loads,
    ...             SandwichSrz().eat,
    ...         ]
    ...         spit_chain = [
    ...             SandwichSrz().spit,
    ...             json.dumps,
    ...         ]
    >>> class SandwichPickleSrz(SrzWizard):
    ...     class Settings:
    ...         eat_chain = [
    ...             pickle.loads,
    ...             SandwichSrz().eat,
    ...         ]
    ...         spit_chain = [
    ...             SandwichSrz().spit,
    ...             pickle.dumps,
    ...         ]

    >>> sandwich_xml = ''\
    ... '<sandwich name="The French" bread="baguette">'\
    ...     '<filling name="mustard" kind="sauce"/>'\
    ...     '<filling name="camembert" kind="cheese"/>'\
    ... '</sandwich>'
    >>> sandwich = SandwichXMLSrz().eat(sandwich_xml)
    >>> sandwich
    Sandwich(The French, baguette): [Filling(camembert, cheese), Filling(mustard, sauce)]
    >>> SandwichXMLSrz().spit(sandwich) == '<sandwich bread="baguette" name="The French">'\
    ...     '<filling kind="sauce" name="mustard"/>'\
    ...     '<filling kind="cheese" name="camembert"/>'\
    ... '</sandwich>'
    True

    >>> sandwich_json = json.dumps({
    ...     'name': u'The French', 
    ...     'bread': u'baguette',
    ...     'fillings': [{
    ...         'kind': u'sauce', 
    ...         'name': u'mustard',
    ...     },
    ...     {
    ...         'kind': u'cheese', 
    ...         'name': u'camembert'
    ...     }],
    ... })
    >>> sandwich = SandwichJSONSrz().eat(sandwich_json)
    >>> sandwich
    Sandwich(The French, baguette): [Filling(camembert, cheese), Filling(mustard, sauce)]
    >>> SandwichJSONSrz().spit(sandwich) == sandwich_json
    True
