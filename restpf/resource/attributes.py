"""
Defines the primitive fields.

Primitive Types:

- bool
- integer
- float
- string

- datetime
- interval
- duration

- primitive_array
- primitive_object

Nested Types:

- array[T]
- tuple[T, ...]
- object[named T, ...]
"""

import collections.abc as abc
import inspect


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

    return node.create_state(statecls, value, node2statecls)


class Attribute(BehaviorTreeNode):

    def __init__(self, name, *, nullable=False):
        super().__init__()

        # shared settings.
        self.name = name
        self.bh_rename(name)

        self.nullable = nullable

    def create_state(self, statecls, value, node2statecls):
        pass


class LeafAttribute(Attribute):

    def create_state(self, statecls, value, node2statecls):
        state = statecls()
        state.bh_value = value
        state.bh_bind_node(self)

        return state


class LeafAttributeState(BehaviorTreeNodeStateLeaf):

    # require subclass to override.
    ATTR_TYPE = 'none'
    PYTHON_TYPE = None

    def validate(self):
        return isinstance(self.bh_value, self.PYTHON_TYPE)

    def serialize(self):
        return {
            'type': self.ATTR_TYPE,
            'value': self.bh_value,
        }


class NestedAttribute(Attribute):

    def _to_iterable(self, element):
        assert element

        if not isinstance(element, abc.Iterable):
            element = (element,)
        return element

    def _assert_not_contain_attribute_class(self, element_attrs):
        element_attrs = self._to_iterable(element_attrs)

        for attr in element_attrs:
            if inspect.isclass(attr):
                raise RuntimeError('contains Attribute class')
            if not isinstance(attr, Attribute):
                raise RuntimeError('contains non-Attribute instance')

    def _transfrom_to_instances(self, element_attrs, rename_list):
        element_attrs = self._to_iterable(element_attrs)
        assert len(element_attrs) == len(rename_list)

        ret = []
        for idx, attr in enumerate(element_attrs):
            if inspect.isclass(attr):
                if not issubclass(attr, Attribute):
                    raise RuntimeError('contains non-Attribute subclass')
                else:
                    attr = attr(rename_list[idx])
            elif not isinstance(attr, Attribute):
                raise RuntimeError('contains non-Attribute instance')

            ret.append(attr)
        return ret

    def create_state(self, statecls, value, node2statecls):
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

    def __init__(self, name, element_attr, **options):
        super().__init__(name, **options)

        element_attr = self._transform_element_attr_to_instance(element_attr)
        self.bh_add_child(element_attr)

    def _transform_element_attr_to_instance(self, element_attr):
        return self._transfrom_to_instances(
            element_attr,
            [self.ELEMENT_ATTR_NAME],
        )[0]

    @property
    def element_attr(self):
        return self.bh_named_child(self.ELEMENT_ATTR_NAME)

    def create_state(self, statecls, values, node2statecls):
        assert isinstance(values, abc.Iterable)

        element_attr = self.element_attr

        # element container.
        state = statecls()
        state.bh_bind_node(self)

        # recursive construction.
        for element_value in values:
            element_state = create_attribute_state_tree(
                element_attr,
                element_value,
                node2statecls,
            )
            state.bh_add_child(element_state)

        return state


class Tuple(NestedAttribute):

    ELEMENT_ATTR_PREFIX = 'element_attr_'

    def __init__(self, name, *element_attrs, **options):
        super().__init__(name, **options)

        rename_list = [
            self.element_attr_name(idx)
            for idx, _ in enumerate(element_attrs)
        ]
        element_attrs = self._transfrom_to_instances(
            element_attrs, rename_list,
        )

        for attr in element_attrs:
            self.bh_add_child(attr)

    def element_attr_name(self, idx):
        return self.ELEMENT_ATTR_PREFIX + str(idx)

    def create_state(self, statecls, values, node2statecls):
        assert isinstance(values, abc.Iterable)

        if len(values) != self.bh_children_size:
            raise RuntimeError('tuple values not matched')

        # tuple element container.
        state = statecls()
        state.bh_bind_node(self)

        # recursive construction.
        for element_attr, element_value in zip(self.bh_children, values):
            element_state = create_attribute_state_tree(
                element_attr,
                element_value,
                node2statecls,
            )
            state.bh_add_child(element_state)

        return state


class Object(NestedAttribute):

    def __init__(self, name, *element_attrs, **options):
        super().__init__(name, **options)

        self._assert_not_contain_attribute_class(element_attrs)
        for attr in element_attrs:
            self.bh_add_child(attr)

    def create_state(self, statecls, mapping, node2statecls):
        assert isinstance(mapping, abc.Mapping)

        # object element container.
        state = statecls()
        state.bh_bind_node(self)

        # recursive construction.
        for element_name, element_value in mapping.items():
            element_attr = self.bh_named_child(element_name)
            if element_attr is None:
                raise RuntimeError('cannot find attribute ' + element_name)

            element_state = create_attribute_state_tree(
                element_attr,
                element_value,
                node2statecls,
            )
            state.bh_add_child(element_state)

        return state


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

    def validate(self):
        element_attrcls = self.element_attrcls()
        for element_state in self.element_attr_states:
            if element_state.bh_nodecls is not element_attrcls:
                return False
            if not element_state.validate():
                return False

        return True

    def can_abbr(self):
        if self.bh_children_size == 0:
            return False
        else:
            return not isinstance(self.bh_child(), NestedAttributeState)

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
