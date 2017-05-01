import collections.abc as abc

from .attributes import (
    Bool,
    Integer,
    Float,
    String,
    PrimitiveArray,
    PrimitiveObject,
    Array,
    Tuple,
    Object,
)
from .behavior_tree import (
    BehaviorTreeNodeStateLeaf,
    BehaviorTreeNodeStateNested,
)


def create_attribute_state_tree(node, value, node2statecls):

    '''
    1. Attribute classes has nothing to do with side effect, including building
    nodes and consuming input value.
    2. Multiple state classes could be associated to an Attribute class,
    leading to different behavior for a single structure.
    3. State.init_state should consume the entire input value. Kind of top-down
    parsing structure.
    '''

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


class NestedAttributeState(BehaviorTreeNodeStateNested):

    @property
    def element_attrs(self):
        return self.bh_node.bh_children

    @property
    def element_attr_size(self):
        return self.bh_node.bh_children_size

    @property
    def element_attr_states(self):
        return self.bh_children

    @property
    def element_named_attrs(self):
        return self.bh_node._bh_named_children

    def element_named_attr(self, name):
        return self.bh_node.bh_named_child(name)

    @property
    def element_named_attr_states(self):
        return self._bh_named_children

    def init_state(self, value, node2statecls):
        pass


class BoolStateForOutputDefault(LeafAttributeState):
    BH_NODECLS = Bool

    ATTR_TYPE = 'bool'
    PYTHON_TYPE = bool


class IntegerStateForOutputDefault(LeafAttributeState):
    BH_NODECLS = Integer

    ATTR_TYPE = 'integer'
    PYTHON_TYPE = int


class FloatStateForOutputDefault(LeafAttributeState):
    BH_NODECLS = Float

    ATTR_TYPE = 'float'
    PYTHON_TYPE = float


class StringStateForOutputDefault(LeafAttributeState):
    BH_NODECLS = String

    ATTR_TYPE = 'string'
    PYTHON_TYPE = str


class PrimitiveArrayStateForOutputDefault(LeafAttributeState):
    BH_NODECLS = PrimitiveArray

    ATTR_TYPE = 'primitive_array'
    PYTHON_TYPE = list


class PrimitiveObjectStateForOutputDefault(LeafAttributeState):
    BH_NODECLS = PrimitiveObject

    ATTR_TYPE = 'primitive_object'
    PYTHON_TYPE = dict


class ArrayStateForOutputDefault(NestedAttributeState):
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


class TupleStateForOutputDefault(ArrayStateForOutputDefault):
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

    def element_attr_name(self, idx):
        return self.bh_node.element_attr_name(idx)

    def init_state(self, values, node2statecls):
        assert isinstance(values, abc.Iterable)

        if len(values) != self.element_attr_size:
            raise RuntimeError('tuple values not matched')

        # recursive construction.
        for element_attr, element_value in zip(self.element_attrs, values):
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
                self.element_attr_name(idx),
            )
            if element_state.bh_nodecls is not element_attr:
                return False
            if not element_state.validate():
                return False

        return True


class ObjectStateForOutputDefault(NestedAttributeState):
    BH_NODECLS = Object

    ATTR_TYPE = 'object'

    def init_state(self, mapping, node2statecls):
        assert isinstance(mapping, abc.Mapping)

        # recursive construction.
        for element_name, element_value in mapping.items():
            element_attr = self.element_named_attr(element_name)
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
