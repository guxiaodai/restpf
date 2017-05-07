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

Appearance: one of there state: REQUIRE, PROHIBITE, FREE

- appear_in_get: For GET, FREE by default.
- appear_in_post: For POST, REQUIRE by default.
- appear_in_put: For Put, REQUIRE by default.
- appear_in_patch: For PATCH, FREE by default.

special attributes:

- id: PROHIBITE in POST, REQUIRE in GET.
"""

import collections.abc as abc
import inspect

from restpf.utils.constants import AppearanceConfig
from restpf.utils.helper_functions import to_iterable
from .behavior_tree import BehaviorTreeNode


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

    def __init__(self, **options):
        super().__init__()

        # shared settings.
        self.rename('undefined')
        self._init_appearance_options(**options)

    def _init_appearance_options(self, **options):

        def helper(name, default):
            setattr(self, name, options.get(name, default))
            assert getattr(self, name) in AppearanceConfig

        helper('appear_in_get', AppearanceConfig.FREE)
        helper('appear_in_patch', AppearanceConfig.FREE)
        helper('appear_in_post', AppearanceConfig.REQUIRE)
        helper('appear_in_put', AppearanceConfig.REQUIRE)

    def rename(self, name):
        self.bh_rename(name)

    @property
    def name(self):
        return self.bh_name


class LeafAttribute(Attribute):
    pass


class NestedAttribute(Attribute):
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