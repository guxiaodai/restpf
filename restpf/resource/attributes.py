"""
Defines the primitive attributes.

Primitive Types:

- bool
- integer
- float
- string

- datetime (TODO)
- interval (TODO)
- duration (TODO)

- primitive_array
- primitive_object

Nested Types:

- array[T]
- tuple[T, ...]
- object[named T, ...]


Common configuration for attributes:

- name: [string] Name of the attribute.
- nullable: [a list of http methods].
    - GET: corresponding value in IST is allowed to be null.
    - POST: it's ok to not post this attribute for resource creation.
    - PUT: same as POST.
    - PATCH: similar to POST. notice, attributes are nullable in PATCH by
    default, except for some special attributes like id and type.
    - OPTIONS: might have something to do with definition exporting. (TODO)
    - DELETE: not support.
"""

import collections.abc as abc
import inspect


from restpf.utils.constants import ALL_HTTP_METHODS
from restpf.utils.helper_functions import to_iterable
from .behavior_tree import (
    BehaviorTreeNode,
    BehaviorTreeNodeStateLeaf,
    BehaviorTreeNodeStateNested,
)


def create_attribute_state_tree(node, value, node2statecls):
    statecls = node2statecls(node)

    if statecls is None:
        raise RuntimeError('cannot get corresponding statecls for node.')
    if not isinstance(node, statecls.bh_nodecls):
        raise RuntimeError('statecls is not bound to nodecls.')

    # create state for node.
    state = statecls()
    state.bh_bind_node(node)

    # process
    state.init_state(value, node2statecls)

    return state


def create_ist_from_bh_object(attr_obj, value_binder=lambda x: x):
    tree = {}
    for name, element_attr in attr_obj.bh_named_children.items():

        if isinstance(element_attr, Object):
            child_value = create_ist_from_bh_object(
                element_attr, value_binder,
            )
        else:
            child_value = None

        tree[name] = value_binder(child_value)
    return tree


def assert_not_contain_attribute_class(element_attrs):
    element_attrs = to_iterable(element_attrs)

    for attr in element_attrs:
        if inspect.isclass(attr):
            raise RuntimeError('contains Attribute class')
        if not isinstance(attr, Attribute):
            raise RuntimeError('contains non-Attribute instance')


def transfrom_to_attribute_states(element_attrs, rename_list):
    element_attrs = to_iterable(element_attrs)
    assert len(element_attrs) == len(rename_list)

    ret = []
    for attr, name in zip(element_attrs, rename_list):
        if inspect.isclass(attr):
            if not issubclass(attr, Attribute):
                raise RuntimeError('contains non-Attribute subclass')
            else:
                attr = attr()
        elif not isinstance(attr, Attribute):
            raise RuntimeError('contains non-Attribute instance')

        attr.rename(name)
        ret.append(attr)
    return ret


def transfrom_mapping_to_attribute_states(name2attr):
    assert isinstance(name2attr, abc.Mapping)

    rename_list = list(name2attr.keys())
    element_attrs = [name2attr[name] for name in rename_list]

    return transfrom_to_attribute_states(element_attrs, rename_list)


class Attribute(BehaviorTreeNode):

    def __init__(self, nullable=[]):
        super().__init__()

        # shared settings.
        self.rename('undefined')
        self._init_nullable(nullable)

    def _init_nullable(self, nullable):
        self.nullable = set()

        if not nullable:
            # passing None is ok.
            return
        # should be iterable.
        assert isinstance(nullable, abc.Iterable)

        for http_method in nullable:
            assert http_method in ALL_HTTP_METHODS
            self.nullable.add(http_method)

    def rename(self, name):
        self.bh_rename(name)

    @property
    def name(self):
        return self.bh_name


class LeafAttribute(Attribute):
    pass


class LeafAttributeState(BehaviorTreeNodeStateLeaf):

    # require subclass to override.
    ATTR_TYPE = 'none'
    PYTHON_TYPE = None

    def init_state(self, value, node2statecls):
        self.bh_value = value

    def validate(self):
        return isinstance(self.bh_value, self.PYTHON_TYPE)

    def serialize(self):
        return {
            'type': self.ATTR_TYPE,
            'value': self.bh_value,
        }

    @property
    def value(self):
        return self.bh_value


class NestedAttribute(Attribute):
    pass


class NestedAttributeState(BehaviorTreeNodeStateNested):

    @property
    def element_attrs(self):
        return self.bh_node.bh_children

    @property
    def element_attr_states(self):
        return self.bh_children

    @property
    def element_named_attrs(self):
        return self.bh_node._bh_named_children

    @property
    def element_named_attr_states(self):
        return self._bh_named_children

    def init_state(self, value, node2statecls):
        pass


class Bool(LeafAttribute):
    pass


class Integer(LeafAttribute):
    pass


class Float(LeafAttribute):
    pass


class String(LeafAttribute):
    pass


class PrimitiveArray(LeafAttribute):
    pass


class PrimitiveObject(LeafAttribute):
    pass


class Array(NestedAttribute):

    ELEMENT_ATTR_NAME = 'element_attr'

    def __init__(self, element_attr, **options):
        super().__init__(**options)

        element_attr = self._transform_element_attr_to_instance(element_attr)
        self.bh_add_child(element_attr)

    def _transform_element_attr_to_instance(self, element_attr):
        return transfrom_to_attribute_states(
            element_attr, [self.ELEMENT_ATTR_NAME],
        )[0]

    @property
    def element_attr(self):
        return self.bh_named_child(self.ELEMENT_ATTR_NAME)


class Tuple(NestedAttribute):

    ELEMENT_ATTR_PREFIX = 'element_attr_'

    def __init__(self, *element_attrs, **options):
        super().__init__(**options)

        rename_list = [
            self.element_attr_name(idx)
            for idx, _ in enumerate(element_attrs)
        ]
        element_attrs = transfrom_to_attribute_states(
            element_attrs, rename_list,
        )

        for attr in element_attrs:
            self.bh_add_child(attr)

    def element_attr_name(self, idx):
        return self.ELEMENT_ATTR_PREFIX + str(idx)


class Object(NestedAttribute):

    def __init__(self, *named_element_attrs, **options):
        '''
        form 1:
        named_element_attrs: { name: attr, ... }

        form 2:
        named_element_attrs: (name, element_attr), ...
        '''

        super().__init__(**options)

        if len(named_element_attrs) == 1 and \
                isinstance(named_element_attrs[0], abc.Mapping):
            # form 1.
            element_attrs = transfrom_mapping_to_attribute_states(
                named_element_attrs[0],
            )
        else:
            # form 2.
            name2attr = dict(named_element_attrs)
            element_attrs = transfrom_mapping_to_attribute_states(name2attr)

        for attr in element_attrs:
            self.bh_add_child(attr)


class BoolState(LeafAttributeState):
    BH_NODECLS = Bool

    ATTR_TYPE = 'bool'
    PYTHON_TYPE = bool


class IntegerState(LeafAttributeState):
    BH_NODECLS = Integer

    ATTR_TYPE = 'integer'
    PYTHON_TYPE = int


class FloatState(LeafAttributeState):
    BH_NODECLS = Float

    ATTR_TYPE = 'float'
    PYTHON_TYPE = float


class StringState(LeafAttributeState):
    BH_NODECLS = String

    ATTR_TYPE = 'string'
    PYTHON_TYPE = str


class PrimitiveArrayState(LeafAttributeState):
    BH_NODECLS = PrimitiveArray

    ATTR_TYPE = 'primitive_array'
    PYTHON_TYPE = list


class PrimitiveObjectState(LeafAttributeState):
    BH_NODECLS = PrimitiveObject

    ATTR_TYPE = 'primitive_object'
    PYTHON_TYPE = dict


class ArrayState(NestedAttributeState):
    BH_NODECLS = Array

    ATTR_TYPE = 'array'

    def element_attr(self):
        return self.bh_relative_node(
            self.bh_nodecls.ELEMENT_ATTR_NAME,
        )

    def element_attrcls(self):
        return self.bh_relative_nodecls(
            self.bh_nodecls.ELEMENT_ATTR_NAME,
        )

    def element_attr_type(self):
        if self.bh_children_size > 0:
            return self.bh_child().ATTR_TYPE
        else:
            return None

    def can_abbr(self):
        if self.bh_children_size == 0:
            return False
        else:
            return not isinstance(self.bh_child(), NestedAttributeState)

    def init_state(self, values, node2statecls):
        assert isinstance(values, abc.Iterable)

        element_attr = self.element_attr()

        # recursive construction.
        for element_value in values:
            element_state = create_attribute_state_tree(
                element_attr,
                element_value,
                node2statecls,
            )
            self.bh_add_child(element_state)

    def validate(self):
        element_attrcls = self.element_attrcls()
        for element_state in self.element_attr_states:
            if element_state.bh_nodecls is not element_attrcls:
                return False
            if not element_state.validate():
                return False

        return True

    def serialize(self):
        output_list = []

        can_abbr = self.can_abbr()
        element_attr_type = self.element_attr_type()

        for element_state in self.element_attr_states:
            element_value = element_state.serialize()

            if can_abbr:
                element_value = element_value['value']

            output_list.append(element_value)

        ret = {
            'type': self.ATTR_TYPE,
            'value': output_list,
        }
        if can_abbr:
            ret['element_type'] = element_attr_type

        return ret

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.bh_child(key)
        else:
            raise RuntimeError('wrong type')

    def __len__(self):
        return self.bh_children_size

    def __iter__(self):
        return iter(self.bh_children)


class TupleState(ArrayState):
    BH_NODECLS = Tuple

    ATTR_TYPE = 'tuple'

    def can_abbr(self):
        if self.bh_children_size == 0:
            return False

        element_attr_type = self.bh_child().ATTR_TYPE
        for element_state in self.element_attr_states:
            if element_attr_type != element_state.ATTR_TYPE:
                return False

        return not isinstance(self.bh_child(), NestedAttributeState)

    def init_state(self, values, node2statecls):
        assert isinstance(values, abc.Iterable)

        if len(values) != self.bh_node.bh_children_size:
            raise RuntimeError('tuple values not matched')

        # recursive construction.
        for element_attr, element_value in zip(self.bh_node.bh_children,
                                               values):
            element_state = create_attribute_state_tree(
                element_attr,
                element_value,
                node2statecls,
            )
            self.bh_add_child(element_state)

    def validate(self):

        if len(self.element_attrs) != len(self.element_attr_states):
            return False

        for idx, element_state in enumerate(self.element_attr_states):
            element_attr = self.bh_relative_nodecls(
                self.bh_node.element_attr_name(idx),
            )
            if element_state.bh_nodecls is not element_attr:
                return False
            if not element_state.validate():
                return False

        return True


class ObjectState(NestedAttributeState):
    BH_NODECLS = Object

    ATTR_TYPE = 'object'

    def init_state(self, mapping, node2statecls):
        assert isinstance(mapping, abc.Mapping)

        # recursive construction.
        for element_name, element_value in mapping.items():
            element_attr = self.bh_node.bh_named_child(element_name)
            if element_attr is None:
                raise RuntimeError('cannot find attribute ' + element_name)

            element_state = create_attribute_state_tree(
                element_attr,
                element_value,
                node2statecls,
            )
            self.bh_add_child(element_state)

    def validate(self):
        if (set(self.element_named_attr_states) !=
                set(self.element_named_attrs)):
            return False

        for name, element_state in self.element_named_attr_states.items():
            element_attr = self.bh_relative_nodecls(name)

            if element_state.bh_nodecls is not element_attr:
                return False

            if not element_state.validate():
                return False

        return True

    def serialize(self):
        ret = {}
        for name, element_state in self.element_named_attr_states.items():
            ret[name] = element_state.serialize()
        return ret

    def get(self, name):
        return self.__getattr__(name)

    def __getattr__(self, name):
        child = self.bh_named_child(name)
        assert child
        return child


# TODO
# def generate_builder(attrcls):
#
#     class Builder:
#
#         def __init__(self, *args, **kwargs):
#             self.args = args
#             self.kwargs = kwargs
#             self.name = None
#
#         def finalize(self):
#             if self.name is None:
#                 raise RuntimeError('name not set')
#
#             return attrcls(self.name, *self.args, **self.kwargs)
#
#         def __repr__(self):
#             return '<Builder: {}'.format(attrcls)
#
#     return Builder
#
#
# BoolBuilder = generate_builder(Bool)
# IntegerBuilder = generate_builder(Integer)
# FloatBuilder = generate_builder(Float)
# StringBuilder = generate_builder(String)
# ArrayBuilder = generate_builder(Array)
# TupleBuilder = generate_builder(Tuple)
# ObjectBuilder = generate_builder(Object)
