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


class AttributeState(BehaviorTreeNodeStateLeaf):

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


class Attribute(BehaviorTreeNode):

    def __init__(self, name, *, nullable=False):
        super().__init__()

        # shared settings.
        self.name = name
        self.bh_rename(name)

        self.nullable = nullable


class Bool(Attribute):
    pass


class BoolState(AttributeState):

    ATTR_TYPE = 'bool'
    PYTHON_TYPE = bool


class Integer(Attribute):
    pass


class IntegerState(AttributeState):

    ATTR_TYPE = 'integer'
    PYTHON_TYPE = int


class Float(Attribute):
    pass


class FloatState(AttributeState):

    ATTR_TYPE = 'float'
    PYTHON_TYPE = float


class String(Attribute):
    pass


class StringState(AttributeState):

    ATTR_TYPE = 'string'
    PYTHON_TYPE = str


class PrimitiveArray(Attribute):
    pass


class PrimitiveArrayState(AttributeState):

    ATTR_TYPE = 'primitive_array'
    PYTHON_TYPE = list


class PrimitiveObject(Attribute):
    pass


class PrimitiveObjectState(AttributeState):

    ATTR_TYPE = 'primitive_object'
    PYTHON_TYPE = dict


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
                raise Exception('contains Attribute class')
            if not isinstance(attr, Attribute):
                raise Exception('contains non-Attribute instance')

    def _transfrom_to_instances(self, element_attrs, rename_list):
        element_attrs = self._to_iterable(element_attrs)
        assert len(element_attrs) == len(rename_list)

        ret = []
        for idx, attr in enumerate(element_attrs):
            if inspect.isclass(attr):
                if not issubclass(attr, Attribute):
                    raise Exception('contains non-Attribute subclass')
                else:
                    attr = attr(rename_list[idx])
            elif not isinstance(attr, Attribute):
                raise Exception('contains non-Attribute instance')

            ret.append(attr)
        return ret


class NestedAttributeState(BehaviorTreeNodeStateNested):

    @property
    def element_attrs(self):
        return self._bh_node._bh_children

    @property
    def element_attr_states(self):
        return self._bh_children

    @property
    def element_named_attrs(self):
        return self._bh_node._bh_named_children

    @property
    def element_named_attr_states(self):
        return self._bh_named_children

    def next_element_state(self):
        pass

    def next_named_element_state(self, name):
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


class ArrayState(NestedAttributeState):

    ATTR_TYPE = 'array'

    def add_value(self, value):
        next_state = self.next_element_state()
        if not isinstance(next_state, NestedAttributeState):
            next_state.bh_value = value
            self.bh_add_child(next_state)
        elif isinstance(value, AttributeState):
            self.bh_add_child(value)
        else:
            raise 'Cannot add value'

    def add_collection(self, iterable):
        assert isinstance(iterable, abc.Iterable)
        for value in iterable:
            self.add_value(value)

    def next_element_state(self):
        return self.bh_create_state(
            self._bh_node.ELEMENT_ATTR_NAME,
        )

    def validate(self):
        element_attr_cls = self.bh_get_statecls(
            self._bh_node.ELEMENT_ATTR_NAME,
        )

        for child_state in self.element_attr_states:
            if type(child_state) is not element_attr_cls:
                return False
            if not child_state.validate():
                return False

        return True

    def can_abbr(self):
        if self.bh_child_size == 0:
            return False
        else:
            return not isinstance(self.bh_child(), NestedAttributeState)

    def element_attr_type(self):
        return self.bh_child().ATTR_TYPE

    def serialize(self):
        output_list = []

        can_abbr = self.can_abbr()
        element_attr_type = self.element_attr_type()

        for child_state in self.element_attr_states:
            element_value = child_state.serialize()

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


class TupleState(ArrayState):

    ATTR_TYPE = 'tuple'

    def next_element_state(self):
        if self.bh_child_size >= self._bh_node.bh_child_size:
            raise 'Cannot get next tuple element class.'

        return self.bh_create_state(
            self._bh_node.element_attr_name(self.bh_child_size),
        )

    def can_abbr(self):
        if self.bh_child_size == 0:
            return False

        element_attr_type = self.bh_child().ATTR_TYPE
        for child_state in self.element_attr_states:
            if element_attr_type != child_state.ATTR_TYPE:
                return False

        return not isinstance(self.bh_child(), NestedAttributeState)

    def validate(self):

        if len(self.element_attrs) != len(self.element_attr_states):
            return False

        for idx, child_state in enumerate(self.element_attr_states):
            statecls = self.bh_get_statecls(
                self._bh_node.element_attr_name(idx),
            )
            if statecls is not type(child_state):
                return False
            if not child_state.validate():
                return False

        return True


class Object(NestedAttribute):

    def __init__(self, name, *element_attrs, **options):
        super().__init__(name, **options)

        self._assert_not_contain_attribute_class(element_attrs)
        for attr in element_attrs:
            self.bh_add_child(attr)


class ObjectState(NestedAttributeState):

    ATTR_TYPE = 'object'
    PYTHON_TYPE = dict

    def next_named_element_state(self, name):
        return self.bh_create_state(name)

    def add_named_value(self, name, value):
        named_state = self.next_named_element_state(name)
        if not isinstance(named_state, NestedAttributeState):
            named_state.bh_value = value
            self.bh_add_child(named_state)
        elif isinstance(value, AttributeState):
            self.bh_add_child(value)
        else:
            raise 'Cannot add value'

    def add_named_collection(self, mapping):
        assert isinstance(mapping, abc.Mapping)

        for name, value in mapping.items():
            self.add_named_value(name, value)

    def validate(self):
        if (set(self.element_named_attr_states) !=
                set(self.element_named_attrs)):
            return False

        for name, child_state in self.element_named_attr_states.items():
            statecls = self.bh_get_statecls(name)

            if statecls is not type(child_state):
                return False

            if not child_state.validate():
                return False

        return True

    def serialize(self):
        ret = {}
        for name, child_state in self.element_named_attr_states.items():
            ret[name] = child_state.serialize()
        return ret
