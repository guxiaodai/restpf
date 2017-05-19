import pytest

from tests.utils.attr_config import *


class _TestContext:

    cxt = HTTPMethodConfig.GET

    @classmethod
    def set_context(cls, value):
        cls.cxt = value

    @classmethod
    def gen_attr_context(cls):
        return AttributeContextOperator(cls.cxt)


def _gen_test_result(attr, value, node2statecls):
    state = create_attribute_state_tree(attr, value, node2statecls)
    return (
        state,
        state.validate(_TestContext.gen_attr_context()),
        state.serialize(),
    )


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
    _TestContext.set_context(HTTPMethodConfig.POST)

    attr = Object(
        ('foo', Integer()),
        ('bar', String()),
    )

    assert_validate_output(attr, {
        'foo': 42,
        'bar': 'test',
    })

    assert_validate_output(attr, {
        'foo': 42,
        'bar': 'test',
        'unknown': 'whatever',
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

    _TestContext.set_context(HTTPMethodConfig.GET)

    assert_validate_output(attr, {
        'bar': 'test',
    })

    assert_not_validate_output(attr, {
        'foo': 42,
        'bar': 'test',
        'unknown': 'whatever',
    })


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


def test_appearance_options():
    s = String(appear_in_get=AppearanceConfig.REQUIRE)
    assert s.appear_in_get is AppearanceConfig.REQUIRE
    assert s.appear_in_patch is AppearanceConfig.FREE

    with pytest.raises(AssertionError):
        String(appear_in_get='whatever')

    attr = Integer()

    _TestContext.set_context(HTTPMethodConfig.POST)
    assert_not_validate_output(attr, None)

    _TestContext.set_context(HTTPMethodConfig.GET)
    assert_validate_output(attr, None)


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

    with pytest.raises(AssertionError):
        state.whatever


def test_object_path():
    attr = Object({
        'a': Object({
            'b': Object({
                'c': Integer,
            }),
        }),
    })

    state = gen_test_state_for_output(attr, {
        'a': {
            'b': {
                'c': 42,
            },
        },
    })

    assert list(state.a.b.c.bh_path) == ['a', 'b', 'c']
    assert list(state.bh_path) == []
