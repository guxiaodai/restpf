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


class AttributeValueContainer:

    def __init__(self, attr_operator, attr_value, **options):
        self.attr_operator = attr_operator
        self.attr_value = attr_value

    def serialize(self, **options):
        return self.attr_operator.serialize(
            self.attr_value,
            **options
        )


class Attribute:

    # require subclass to override.
    TYPENAME = 'none'
    PYTHON_TYPE = None
    # default value container.
    ATTRIBUTE_VALUE_CONTAINER_CLS = AttributeValueContainer

    def __init__(self, name, *, nullable=False):
        # shared settings.
        self.name = name
        self.nullable = nullable

    def validate(self, value, **options):
        return isinstance(value, self.PYTHON_TYPE)

    def construct(self, value, **options):
        return self.ATTRIBUTE_VALUE_CONTAINER_CLS(
            self,
            value,
            **options
        )

    def serialize(self, value, **options):
        return {
            'type': self.TYPENAME,
            'value': value,
        }


class Bool(Attribute):

    TYPENAME = 'bool'
    PYTHON_TYPE = bool


class Integer(Attribute):

    TYPENAME = 'integer'
    PYTHON_TYPE = int


class Float(Attribute):

    TYPENAME = 'float'
    PYTHON_TYPE = float


class String(Attribute):

    TYPENAME = 'string'
    PYTHON_TYPE = str


class PrimitiveArray(Attribute):

    TYPENAME = 'primitive_array'
    PYTHON_TYPE = list


class PrimitiveObject(Attribute):

    TYPENAME = 'primitive_object'
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

    def _transfrom_attribute_class(self, element_attrs):
        element_attrs = self._to_iterable(element_attrs)

        ret = []
        for attr in element_attrs:
            if inspect.isclass(attr):
                if not issubclass(attr, Attribute):
                    raise Exception('contains non-Attribute subclass')
                else:
                    attr = attr('anonymous')
            elif not isinstance(attr, Attribute):
                raise Exception('contains non-Attribute instance')

            ret.append(attr)
        return ret


class Array(NestedAttribute):

    TYPENAME = 'array'

    def __init__(self, name, element_attr, **options):
        super().__init__(name, **options)
        self.element_attr = self._transfrom_attribute_class(element_attr)[0]

    def validate(self, value, **options):
        if not isinstance(value, list):
            return False

        for element in value:
            if not self.element_attr.validate(element, **options):
                return False

        return True

    def serialize(self, value, **options):
        output_list = []

        for element in value:
            element_value = self.element_attr.serialize(element, **options)
            if not isinstance(self.element_attr, NestedAttribute):
                element_value = element_value['value']

            output_list.append(element_value)

        ret = super().serialize(output_list)
        if not isinstance(self.element_attr, NestedAttribute):
            ret['element_type'] = self.element_attr.TYPENAME
        return ret


class Tuple(NestedAttribute):

    TYPENAME = 'tuple'

    def __init__(self, name, *element_attrs, **options):
        super().__init__(name, **options)
        self.element_attrs = self._transfrom_attribute_class(element_attrs)

    def validate(self, value, **options):
        if not isinstance(value, tuple):
            return False
        if len(value) != len(self.element_attrs):
            return False

        for idx, element in enumerate(value):
            if not self.element_attrs[idx].validate(element, **options):
                return False

        return True

    def serialize(self, value, **options):
        can_abbr = False
        element_type = None

        attr_types = set(type(attr) for attr in self.element_attrs)
        if len(attr_types) == 1:
            attr_type = attr_types.pop()
            can_abbr = not issubclass(attr_type, NestedAttribute)
            if can_abbr:
                element_type = attr_type.TYPENAME

        output_list = []
        for idx, element in enumerate(value):
            element_value = self.element_attrs[idx].serialize(
                element, **options
            )
            if can_abbr:
                element_value = element_value['value']
            output_list.append(element_value)

        ret = super().serialize(output_list)
        if can_abbr:
            ret['element_type'] = element_type
        return ret


class Object(NestedAttribute):

    TYPENAME = 'object'
    PYTHON_TYPE = dict

    def __init__(self, name, *element_attrs, **options):
        super().__init__(name, **options)

        self._assert_not_contain_attribute_class(element_attrs)
        # build mapping.
        self.element_attrs = {}
        for attr in element_attrs:
            self.element_attrs[attr.name] = attr

    def validate(self, value, **options):
        if not super().validate(value, **options):
            return False

        for name, attr in self.element_attrs.items():
            if name not in value:
                # name for exists.
                return False
            if not attr.validate(value[name], **options):
                # cannot pass nesting validation.
                return False

        return True

    def serialize(self, value, **options):
        ret = {}
        for name, value in value.items():
            ret[name] = self.element_attrs[name].serialize(value, **options)
        return ret
