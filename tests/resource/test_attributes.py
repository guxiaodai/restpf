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
        state.add_collection(value)
    elif isinstance(state, ObjectState):
        state._bh_children.clear()
        state.add_named_collection(value)


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


def test_tuple():
    attr, state = gen_attr_and_state(Tuple, TupleState, (Float, String))

    assert_validate(state, (1.0, 'test'))

    assert_not_validate(state, (42,))
    assert_not_validate(state, [1, 'test'])

    assert_serialize(state, [1.0, 'test'], {
        'type': 'tuple',
        'value': [
            {'type': 'float', 'value': 1.0},
            {'type': 'string', 'value': 'test'},
        ],
    })


def test_tuple_abbr_serialization():
    attr, state = gen_attr_and_state(
        Tuple, TupleState, (Integer, Integer, Integer),
    )

    assert_serialize(state, [1, 2, 3], {
        'type': 'tuple',
        'element_type': 'integer',
        'value': [1, 2, 3],
    })


def test_object():
    attr, state = gen_attr_and_state(
        Object, ObjectState,
        (Integer('foo'), String('bar')),
    )

    assert_validate(state, {
        'foo': 42,
        'bar': 'test',
    })

    assert_not_validate(state, {
        'foo': '42',
        'bar': 'test',
    })
    assert_not_validate(state, {
        'bar': 'test',
    })

    assert_serialize(
        state,
        {
            'foo': 42,
            'bar': 'test',
        },
        {
            'foo': {'type': 'integer', 'value': 42},
            'bar': {'type': 'string', 'value': 'test'},
        },
    )
