import collections.abc as abc
from functools import wraps

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
    AppearanceConfig,
    UnknowAttributeConfig,
)
from restpf.utils.behavior_tree import (
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


def _check_on_none_value_case(state, attr_context):

    if isinstance(state, LeafAttributeState):
        is_null = state.bh_value is None
    elif isinstance(state, NestedAttributeState):
        is_null = state.bh_children_size == 0
    else:
        raise NotImplemented

    if is_null:
        return (
            True,
            attr_context.appear(state.bh_node) is not AppearanceConfig.REQUIRE
        )
    else:
        return (
            False,
            None,
        )


def nullable_processor(validator):

    @wraps(validator)
    def validator_with_nullable_processing(self, attr_context):
        can_return, flag = _check_on_none_value_case(self, attr_context)
        if can_return:
            return flag
        else:
            return validator(self, attr_context)

    return validator_with_nullable_processing


class LeafAttributeState(BehaviorTreeNodeStateLeaf):

    # require subclass to override.
    ATTR_TYPE = 'none'
    PYTHON_TYPE = None

    def init_state(self, value, node2statecls):
        raise NotImplemented

    @nullable_processor
    def validate(self, attr_context):
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

    def init_state(self, value=None, node2statecls=None):
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

    def element_named_attr_state(self, name):
        return self.bh_named_child(name)

    def element_remove_named_attr_state(self, name):
        self.bh_remove_named_child(name)

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

    @nullable_processor
    def validate(self, attr_context):
        element_attrcls = self.element_attrcls()
        for element_state in self.element_attr_states:
            if element_state.bh_nodecls is not element_attrcls:
                return False
            if not element_state.validate(attr_context):
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

    @nullable_processor
    def validate(self, attr_context):

        if len(self.element_attrs) != len(self.element_attr_states):
            return False

        for idx, element_state in enumerate(self.element_attr_states):
            element_attr = self.bh_relative_nodecls(
                self.element_attr_name(idx),
            )
            if element_state.bh_nodecls is not element_attr:
                return False
            if not element_state.validate(attr_context):
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


class UnknownStatePlaceholderForObject(LeafAttributeState):

    def __init__(self, name, value):
        super().__init__()
        self.bh_rename(name)
        self.bh_value = value


class ObjectStateCommon(ObjectStateConfig, NestedAttributeState):

    def init_state(self, mapping, node2statecls):
        assert isinstance(mapping, abc.Mapping)

        # recursive construction.
        for element_name, element_value in mapping.items():
            element_attr = self.element_named_attr(element_name)

            if element_attr:
                element_state = create_attribute_state_tree(
                    element_attr,
                    element_value,
                    node2statecls,
                )
            else:
                element_state = UnknownStatePlaceholderForObject(
                    element_name, element_value,
                )

            self.bh_add_child(element_state)

    @nullable_processor
    def validate(self, attr_context):
        can_ignore_unknown = (
            attr_context.unknown(self.bh_node)
            is UnknowAttributeConfig.IGNORE
        )

        all_attr_names = set(self.element_named_attrs)
        all_state_names = set(self.element_named_attr_states)

        # for missing keys.
        for name in (all_attr_names - all_state_names):
            attr = self.element_named_attr(name)
            if attr_context.appear(attr) is AppearanceConfig.REQUIRE:
                return False

        for name in all_state_names:
            element_state = self.element_named_attr_state(name)

            # process unknown name.
            if isinstance(element_state, UnknownStatePlaceholderForObject):
                # conditional raise.
                if can_ignore_unknown:
                    continue
                else:
                    return False

            element_attr = self.bh_relative_nodecls(name)

            if element_state.bh_nodecls is not element_attr:
                return False
            if not element_state.validate(attr_context):
                return False

        return True

    def get(self, name):
        return self.__getattr__(name)

    def __getattr__(self, name):
        '''
        1. Raise error on unregistered name.
        2. return None for empty child state.
        '''
        # make sure name is registered.
        assert self.element_named_attr(name)
        # get child state.
        child = self.bh_named_child(name)
        return child


class ObjectStateForOutputDefault(ObjectStateCommon):

    def serialize(self):
        ret = {}
        for name, element_state in self.element_named_attr_states.items():
            # ignore unknown name.
            if isinstance(element_state, UnknownStatePlaceholderForObject):
                continue
            # serialize element.
            ret[name] = element_state.serialize()
        return ret


class ObjectStateForInputDefault(ObjectStateCommon):

    '''
    Both ObjectStateForInputDefault and ObjectStateForOutputDefault should use
    the same way to construct the state.
    '''

    def serialize(self):
        return None


def node2statecls_generator(*state_clses):

    def _decorator(func):
        TO_STATECLS = {s.BH_NODECLS: s for s in state_clses}

        @wraps(func)
        def _wrapper(node):
            return TO_STATECLS[type(node)]

        return _wrapper

    return _decorator


@node2statecls_generator(
    BoolStateForOutputDefault,
    IntegerStateForOutputDefault,
    FloatStateForOutputDefault,
    StringStateForOutputDefault,
    ArrayStateForOutputDefault,
    TupleStateForOutputDefault,
    ObjectStateForOutputDefault,
)
def node2statecls_default_output():
    pass


@node2statecls_generator(
    BoolStateForInputDefault,
    IntegerStateForInputDefault,
    FloatStateForInputDefault,
    StringStateForInputDefault,
    ArrayStateForInputDefault,
    TupleStateForInputDefault,
    ObjectStateForInputDefault,
)
def node2statecls_default_input():
    pass


def create_attribute_state_tree_for_input(node, value):
    return create_attribute_state_tree(
        node, value,
        node2statecls_default_input,
    )


def create_attribute_state_tree_for_output(node, value):
    return create_attribute_state_tree(
        node, value,
        node2statecls_default_output,
    )
