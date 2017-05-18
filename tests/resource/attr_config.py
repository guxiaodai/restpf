# flake8: noqa

from restpf.resource.attributes import (
    Bool,
    Integer,
    Float,
    String,
    Array,
    Tuple,
    Object,
    AppearanceConfig,
    AttributeContextOperator,
    HTTPMethodConfig,
)

from restpf.resource.attribute_states import (
    create_attribute_state_tree,

    BoolStateForOutputDefault,
    IntegerStateForOutputDefault,
    FloatStateForOutputDefault,
    StringStateForOutputDefault,
    ArrayStateForOutputDefault,
    TupleStateForOutputDefault,
    ObjectStateForOutputDefault,

    BoolStateForInputDefault,
    IntegerStateForInputDefault,
    FloatStateForInputDefault,
    StringStateForInputDefault,
    ArrayStateForInputDefault,
    TupleStateForInputDefault,
    ObjectStateForInputDefault,
)


def node2statecls_output(node):
    TO_STATECLS = {
        Bool: BoolStateForOutputDefault,
        Integer: IntegerStateForOutputDefault,
        Float: FloatStateForOutputDefault,
        String: StringStateForOutputDefault,
        Array: ArrayStateForOutputDefault,
        Tuple: TupleStateForOutputDefault,
        Object: ObjectStateForOutputDefault,
    }

    return TO_STATECLS[type(node)]


def node2statecls_input(node):
    TO_STATECLS = {
        Bool: BoolStateForInputDefault,
        Integer: IntegerStateForInputDefault,
        Float: FloatStateForInputDefault,
        String: StringStateForInputDefault,
        Array: ArrayStateForInputDefault,
        Tuple: TupleStateForInputDefault,
        Object: ObjectStateForInputDefault,
    }

    return TO_STATECLS[type(node)]
