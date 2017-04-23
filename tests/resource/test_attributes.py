import pytest

from restpf.resource.attributes import (
    create_attribute_state_tree,

    Bool,
    BoolState,

    Integer,
    IntegerState,

    Float,
    FloatState,

    String,
    StringState,

    Array,
    ArrayState,

    Tuple,
    TupleState,

    Object,
    ObjectState,
)


def node2statecls(node):
    TO_STATECLS = {
        Bool: BoolState,
        Integer: IntegerState,
        Float: FloatState,
        String: StringState,
        Array: ArrayState,
        Tuple: TupleState,
        Object: ObjectState,
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
    attr = Bool('test')

    assert_validate(attr, True)
    assert_validate(attr, False)

    assert_not_validate(attr, 42)
    assert_not_validate(attr, [True])

    assert_serialize(attr, True, {
        'type': 'bool',
        'value': True
    })


def test_array():
    attr = Array('test', Integer)

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
    attr = Tuple('test', Float, String)

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
    attr = Tuple('test', Integer, Integer, Integer)

    assert_serialize(attr, [1, 2, 3], {
        'type': 'tuple',
        'element_type': 'integer',
        'value': [1, 2, 3],
    })


def test_object():
    attr = Object('test', Integer('foo'), String('bar'))

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
