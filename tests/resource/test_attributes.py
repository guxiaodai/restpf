import pytest

from restpf.resource.attributes import (
    Bool,
    Integer,
    Float,
    String,
    Array,
    Tuple,
    Object,
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

from restpf.utils.constants import GET, POST


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


def _gen_test_result(attr, value, node2statecls):
    state = create_attribute_state_tree(attr, value, node2statecls)
    return state, state.validate(), state.serialize()


def gen_test_result_for_output(attr, value):
    return _gen_test_result(attr, value, node2statecls_output)


def gen_test_state_for_output(attr, value):
    return _gen_test_result(attr, value, node2statecls_output)[0]


def gen_test_result_for_input(attr, value):
    return _gen_test_result(attr, value, node2statecls_input)


def gen_test_state_for_input(attr, value):
    return _gen_test_result(attr, value, node2statecls_input)[0]


def _assert_validate(attr, value, result, node2statecls):
    _, v, _ = _gen_test_result(attr, value, node2statecls)
    assert v == result


def assert_validate_output(attr, value):
    _assert_validate(attr, value, True, node2statecls_output)


def assert_not_validate_output(attr, value):
    _assert_validate(attr, value, False, node2statecls_output)


def assert_validate_input(attr, value):
    _assert_validate(attr, value, True, node2statecls_input)


def assert_not_validate_input(attr, value):
    _assert_validate(attr, value, False, node2statecls_input)


def _assert_serialize(attr, value, expected, node2statecls):
    _, _, v = _gen_test_result(attr, value, node2statecls)
    assert v == expected


def assert_serialize_output(attr, value, expected):
    _assert_serialize(attr, value, expected, node2statecls_output)


def assert_serialize_input(attr, value, expected):
    _assert_serialize(attr, value, expected, node2statecls_input)


def test_bool():
    attr = Bool()

    assert_validate_output(attr, True)
    assert_validate_output(attr, False)

    assert_validate_input(attr, True)
    assert_validate_input(attr, {
        'type': 'bool',
        'value': True,
    })

    assert_not_validate_output(attr, 42)
    assert_not_validate_output(attr, [True])

    assert_serialize_output(attr, True, {
        'type': 'bool',
        'value': True
    })


def test_array_output():
    attr = Array(Integer)

    assert_validate_output(attr, [1, 2, 3])
    assert_validate_output(attr, [True, False])
    assert_validate_output(attr, [])

    assert_not_validate_output(attr, [42.0])
    assert_not_validate_output(attr, ['42'])

    assert_serialize_output(attr, [1, 2, 3], {
        'type': 'array',
        'element_type': 'integer',
        'value': [1, 2, 3],
    })


def test_array_input():
    attr = Array(Integer)

    assert_validate_input(attr, [1, 2, 3])
    assert_validate_input(attr, {
        'type': 'array',
        # TODO: explicit checking abbr.
        'element_type': 'integer',
        'value': [1, 2, 3],
    })
    assert_validate_input(attr, {
        'type': 'array',
        'value': [
            {'type': 'integer', 'value': 1},
            {'type': 'integer', 'value': 2},
            {'type': 'integer', 'value': 3},
        ],
    })

    assert_not_validate_output(attr, [42.0])
    assert_not_validate_output(attr, {
        'type': 'array',
        'value': [
            {'type': 'integer', 'value': '42'},
        ],
    })

    state = gen_test_state_for_input(attr, {
        'type': 'array',
        'value': [
            {'type': 'integer', 'value': 1},
            {'type': 'integer', 'value': 2},
            {'type': 'integer', 'value': 3},
        ],
    })
    for obj, value in zip(state, [1, 2, 3]):
        assert obj.value == value


def test_tuple_output():
    attr = Tuple(Float, String)

    assert_validate_output(attr, (1.0, 'test'))

    with pytest.raises(RuntimeError):
        assert_not_validate_output(attr, (42,))

    assert_not_validate_output(attr, [1, 'test'])

    assert_serialize_output(attr, [1.0, 'test'], {
        'type': 'tuple',
        'value': [
            {'type': 'float', 'value': 1.0},
            {'type': 'string', 'value': 'test'},
        ],
    })


def test_tuple_input():
    attr = Tuple(Float, String)

    assert_validate_input(attr, (1.0, 'test'))


def test_tuple_abbr_serialization():
    attr = Tuple(Integer, Integer, Integer)

    assert_serialize_output(attr, [1, 2, 3], {
        'type': 'tuple',
        'element_type': 'integer',
        'value': [1, 2, 3],
    })


def test_object_output():
    attr = Object(
        ('foo', Integer()),
        ('bar', String()),
    )

    assert_validate_output(attr, {
        'foo': 42,
        'bar': 'test',
    })

    assert_not_validate_output(attr, {
        'foo': '42',
        'bar': 'test',
    })
    assert_not_validate_output(attr, {
        'bar': 'test',
    })

    assert_serialize_output(
        attr,
        {
            'foo': 42,
            'bar': 'test',
        },
        {
            'foo': {'type': 'integer', 'value': 42},
            'bar': {'type': 'string', 'value': 'test'},
        },
    )


def test_object_input():
    attr = Object(
        ('foo', Integer()),
        ('bar', String()),
    )

    assert_validate_input(attr, {
        'foo': 42,
        'bar': 'test',
    })
    assert_validate_input(attr, {
        'foo': {
            'type': 'integer',
            'value': 42,
        },
        'bar': {
            'type': 'string',
            'value': 'test',
        },
    })


def test_object_mapping_constructor():
    attr = Object({
        'foo': Integer,
        'bar': String,
    })

    assert_validate_output(attr, {
        'foo': 42,
        'bar': 'test',
    })


def test_nullable():
    String(nullable=[POST, GET])
    String(nullable=None)
    with pytest.raises(AssertionError):
        String(nullable=['wrong'])


def test_value_property():
    attr = Bool()
    state = gen_test_state_for_output(attr, False)
    assert state.value is False

    attr = Integer()
    state = gen_test_state_for_output(attr, 42)
    assert state.value == 42


def test_array_getitem():
    attr = Array(Integer)
    state = gen_test_state_for_output(attr, [1, 2, 3, 4])
    # len.
    assert len(state) == 4
    # int.
    assert state[0].value == 1
    assert state[1].value == 2
    assert state[2].value == 3
    assert state[3].value == 4
    # slice.
    mid = state[1:3]
    assert mid[0].value == 2
    assert mid[1].value == 3


def test_array_iterable():
    attr = Array(Integer)
    state = gen_test_state_for_output(attr, [1, 2, 3])
    assert list(map(lambda x: x.value, state)) == [1, 2, 3]
    for obj, value in zip(state, [1, 2, 3]):
        assert obj.value == value


def test_object_getattr():
    attr = Object({
        'foo': Integer,
        'bar': String,
        'not an identifier': Integer,
    })

    state = gen_test_state_for_output(attr, {
        'foo': 42,
        'bar': 'test',
        'not an identifier': 42,
    })
    assert state.foo.value == 42
    assert state.bar.value == 'test'
    assert state.get('not an identifier').value == 42
