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
)

from restpf.utils.constants import GET, POST


def node2statecls(node):
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


def _gen_test_result(attr, value):
    state = create_attribute_state_tree(attr, value, node2statecls)
    return state, state.validate(), state.serialize()


def assert_validate(attr, value):
    _, v, _ = _gen_test_result(attr, value)
    assert v


def assert_not_validate(attr, value):
    _, v, _ = _gen_test_result(attr, value)
    assert not v


def assert_serialize(attr, value, expected):
    _, _, v = _gen_test_result(attr, value)
    assert v == expected


def test_bool():
    attr = Bool()

    assert_validate(attr, True)
    assert_validate(attr, False)

    assert_not_validate(attr, 42)
    assert_not_validate(attr, [True])

    assert_serialize(attr, True, {
        'type': 'bool',
        'value': True
    })


def test_array():
    attr = Array(Integer)

    assert_validate(attr, [1, 2, 3])
    assert_validate(attr, [True, False])
    assert_validate(attr, [])

    assert_not_validate(attr, [42.0])
    assert_not_validate(attr, ['42'])

    assert_serialize(attr, [1, 2, 3], {
        'type': 'array',
        'element_type': 'integer',
        'value': [1, 2, 3],
    })


def test_tuple():
    attr = Tuple(Float, String)

    assert_validate(attr, (1.0, 'test'))

    with pytest.raises(RuntimeError):
        assert_not_validate(attr, (42,))
    assert_not_validate(attr, [1, 'test'])

    assert_serialize(attr, [1.0, 'test'], {
        'type': 'tuple',
        'value': [
            {'type': 'float', 'value': 1.0},
            {'type': 'string', 'value': 'test'},
        ],
    })


def test_tuple_abbr_serialization():
    attr = Tuple(Integer, Integer, Integer)

    assert_serialize(attr, [1, 2, 3], {
        'type': 'tuple',
        'element_type': 'integer',
        'value': [1, 2, 3],
    })


def test_object():
    attr = Object(
        ('foo', Integer()),
        ('bar', String()),
    )

    assert_validate(attr, {
        'foo': 42,
        'bar': 'test',
    })

    assert_not_validate(attr, {
        'foo': '42',
        'bar': 'test',
    })
    assert_not_validate(attr, {
        'bar': 'test',
    })

    assert_serialize(
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


def test_object_mapping_constructor():
    attr = Object({
        'foo': Integer,
        'bar': String,
    })

    assert_validate(attr, {
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
    state, _, _ = _gen_test_result(attr, False)
    assert state.value is False

    attr = Integer()
    state, _, _ = _gen_test_result(attr, 42)
    assert state.value == 42


def test_array_getitem():
    attr = Array(Integer)
    state, _, _ = _gen_test_result(attr, [1, 2, 3, 4])
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
    state, _, _ = _gen_test_result(attr, [1, 2, 3])
    assert list(map(lambda x: x.value, state)) == [1, 2, 3]
    for obj, value in zip(state, [1, 2, 3]):
        assert obj.value == value


def test_object_getattr():
    attr = Object({
        'foo': Integer,
        'bar': String,
        'not an identifier': Integer,
    })

    state, _, _ = _gen_test_result(attr, {
        'foo': 42,
        'bar': 'test',
        'not an identifier': 42,
    })
    assert state.foo.value == 42
    assert state.bar.value == 'test'
    assert state.get('not an identifier').value == 42
