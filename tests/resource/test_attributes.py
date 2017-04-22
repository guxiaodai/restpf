from restpf.resource.attributes import (
    NestedAttributeState,

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


def gen_attr_and_state(attrcls, statecls, attrcls_args=()):
    to_statecls = {
        Bool: BoolState,
        Integer: IntegerState,
        Float: FloatState,
        String: StringState,
        Array: ArrayState,
        Tuple: TupleState,
        Object: ObjectState,
    }

    attr = attrcls('test', *attrcls_args)
    state = statecls(attr, to_statecls)
    return attr, state


def setup_state(state, value):
    if not isinstance(state, NestedAttributeState):
        state.bh_value = value
    elif isinstance(state, ArrayState):
        state._bh_children.clear()
        for v in value:
            child_state = state.bh_create_state('element_attr')
            child_state.bh_value = v
            state.bh_add_child(child_state)


def assert_validate(state, value):
    setup_state(state, value)
    assert state.validate()


def assert_not_validate(state, value):
    setup_state(state, value)
    assert not state.validate()


def assert_serialize(state, value, expected):
    setup_state(state, value)
    assert state.serialize() == expected


def test_bool():
    attr, state = gen_attr_and_state(Bool, BoolState)

    assert_validate(state, True)
    assert_validate(state, False)

    assert_not_validate(state, 42)
    assert_not_validate(state, [True])

    assert_serialize(state, True, {
        'type': 'bool',
        'value': True
    })


def test_array():
    attr, state = gen_attr_and_state(Array, ArrayState, (Integer,))

    assert_validate(state, [1, 2, 3])
    assert_validate(state, [True, False])
    assert_validate(state, [])

    assert_not_validate(state, [42.0])
    assert_not_validate(state, ['42'])

    assert_serialize(state, [1, 2, 3], {
        'type': 'array',
        'element_type': 'integer',
        'value': [1, 2, 3],
    })


"""
def test_tuple():
    attr = Tuple('test', Float, String)

    assert attr.validate((1.0, 'test'))
    assert not attr.validate(42)
    assert not attr.validate([1, 'test'])

    value = attr.construct([1.0, 'test'])
    assert value.serialize() == {
        'type': 'tuple',
        'value': [
            {'type': 'float', 'value': 1.0},
            {'type': 'string', 'value': 'test'},
        ],
    }


def test_tuple_abbr_serialization():
    attr = Tuple('test', Integer, Integer, Integer)

    value = attr.construct([1, 2, 3])
    assert value.serialize() == {
        'type': 'tuple',
        'element_type': 'integer',
        'value': [1, 2, 3],
    }


def test_object():
    attr = Object(
        'test',
        Integer('foo'),
        String('bar'),
    )

    assert attr.validate({
        'foo': 42,
        'bar': 'test',
    })
    assert not attr.validate(42)
    assert not attr.validate({
        'foo': '42',
        'bar': 'test',
    })
    assert not attr.validate({
        'bar': 'test',
    })

    value = attr.construct({
        'foo': 42,
        'bar': 'test',
    })
    assert value.serialize() == {
        'foo': {'type': 'integer', 'value': 42},
        'bar': {'type': 'string', 'value': 'test'},
    }
"""
