from restpf.resource.attributes import (
    Bool,
    Integer,
    Float,
    String,

    Array,
    Tuple,
    Object,
)


def test_bool():
    attr = Bool('test')

    assert attr.validate(True)
    assert attr.validate(False)
    assert not attr.validate(42)
    assert not attr.validate([True])

    value = attr.construct(True)
    assert value.serialize() == {
        'type': 'bool',
        'value': True
    }


def test_array():
    attr = Array('test', Integer)

    assert attr.validate([1, 2, 3])
    assert attr.validate([True, False])
    assert attr.validate([])
    assert not attr.validate(42)
    assert not attr.validate(['42'])

    value = attr.construct([1, 2, 3])
    assert value.serialize() == {
        'type': 'array',
        'element_type': 'integer',
        'value': [1, 2, 3],
    }


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
