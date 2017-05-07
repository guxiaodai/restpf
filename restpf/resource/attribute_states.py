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
        raise NotImplemented

    def validate(self):
        return isinstance(self.bh_value, self.PYTHON_TYPE)

    def serialize(self):
        raise NotImplemented

    @property
    def value(self):
        return self.bh_value


class LeafAttributeOutputState(LeafAttributeState):

    def init_state(self, value, node2statecls):
        self.bh_value = value

    def serialize(self):
        return {
            'type': self.ATTR_TYPE,
            'value': self.bh_value,
        }


class LeafAttributeInputState(LeafAttributeState):

    '''
    InputState don't need to implement serialize.
    '''

    def init_state(self, value, node2statecls):
        if isinstance(value, abc.Mapping):
            assert value['type'] == self.ATTR_TYPE
            self.bh_value = value['value']
        else:
            self.bh_value = value

    def serialize(self):
        return None


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


class BoolStateConfig:
    BH_NODECLS = Bool

    ATTR_TYPE = 'bool'
    PYTHON_TYPE = bool


class BoolStateForOutputDefault(BoolStateConfig, LeafAttributeOutputState):
    pass


class BoolStateForInputDefault(BoolStateConfig, LeafAttributeInputState):
    pass


class IntegerStateConfig:
    BH_NODECLS = Integer

    ATTR_TYPE = 'integer'
    PYTHON_TYPE = int


class IntegerStateForOutputDefault(IntegerStateConfig,
                                   LeafAttributeOutputState):
    pass


class IntegerStateForInputDefault(IntegerStateConfig,
                                  LeafAttributeInputState):
    pass


class FloatStateConfig:
    BH_NODECLS = Float

    ATTR_TYPE = 'float'
    PYTHON_TYPE = float


class FloatStateForOutputDefault(FloatStateConfig, LeafAttributeOutputState):
    pass


class FloatStateForInputDefault(FloatStateConfig, LeafAttributeInputState):
    pass


class StringStateConfig:
    BH_NODECLS = String

    ATTR_TYPE = 'string'
    PYTHON_TYPE = str


class StringStateForOutputDefault(StringStateConfig, LeafAttributeOutputState):
    pass


class StringStateForInputDefault(StringStateConfig, LeafAttributeInputState):
    pass


class PrimitiveArrayStateConfig:
    BH_NODECLS = PrimitiveArray

    ATTR_TYPE = 'primitive_array'
    PYTHON_TYPE = list


class PrimitiveArrayStateForOutputDefault(PrimitiveArrayStateConfig,
                                          LeafAttributeOutputState):
    pass


class PrimitiveArrayStateForInputDefault(PrimitiveArrayStateConfig,
                                         LeafAttributeInputState):
    pass


class PrimitiveObjectStateConfig:
    BH_NODECLS = PrimitiveObject

    ATTR_TYPE = 'primitive_object'
    PYTHON_TYPE = dict


class PrimitiveObjectStateForOutputDefault(PrimitiveArrayStateConfig,
                                           LeafAttributeOutputState):
    pass


class PrimitiveObjectStateForInputDefault(PrimitiveObjectStateConfig,
                                          LeafAttributeInputState):
    pass


class ArrayStateConfig:
    BH_NODECLS = Array

    ATTR_TYPE = 'array'


class ArrayStateCommon(ArrayStateConfig, NestedAttributeState):

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.bh_child(key)
        else:
            raise RuntimeError('wrong type')

    def __len__(self):
        return self.bh_children_size

    def __iter__(self):
        return iter(self.bh_children)

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

    def init_state_for_list(self, values, node2statecls):
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


class ArrayStateForOutputDefault(ArrayStateCommon):

    def init_state(self, values, node2statecls):
        self.init_state_for_list(values, node2statecls)

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


class ArrayStateForInputDefault(ArrayStateCommon):

    def init_state(self, values, node2statecls):
        if isinstance(values, abc.Mapping):
            assert values['type'] == self.ATTR_TYPE
            self.init_state_for_list(values['value'], node2statecls)
        else:
            self.init_state_for_list(values, node2statecls)

    def serialize(self):
        return None


class TupleStateConfig:
    BH_NODECLS = Tuple

    ATTR_TYPE = 'tuple'


class TupleStateCommon(TupleStateConfig):

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

    def init_state_for_list(self, values, node2statecls):
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


class TupleStateForOutputDefault(TupleStateCommon, ArrayStateForOutputDefault):

    def init_state(self, values, node2statecls):
        self.init_state_for_list(values, node2statecls)


class TupleStateForInputDefault(TupleStateCommon, ArrayStateForInputDefault):

    '''
    Don't need to override anything, since init_state_for_list has already
    been override in TupleStateCommon.
    '''

    def serialize(self):
        return None


class ObjectStateConfig:
    BH_NODECLS = Object

    ATTR_TYPE = 'object'


class ObjectStateCommon(ObjectStateConfig, NestedAttributeState):

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

    def get(self, name):
        return self.__getattr__(name)

    def __getattr__(self, name):
        child = self.bh_named_child(name)
        assert child
        return child


class ObjectStateForOutputDefault(ObjectStateCommon):

    def serialize(self):
        ret = {}
        for name, element_state in self.element_named_attr_states.items():
            ret[name] = element_state.serialize()
        return ret


class ObjectStateForInputDefault(ObjectStateCommon):

    '''
    Both ObjectStateForInputDefault and ObjectStateForOutputDefault should use
    the same way to construct the state.
    '''

    def serialize(self):
        return None
