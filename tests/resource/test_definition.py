from restpf.resource.attributes import (
    String,
    Object,
)
from restpf.resource.definition import (
    AttributeCollection,
)


def test_registration():
    ac = AttributeCollection(
        String('foo'),
        Object(
            'a',
            Object(
                'b',
                String('bar'),
            ),
        ),
    )

    register = ac.create_callback_registrar()

    @register.foo(whatever=42)
    def callback_foo():
        return 'foo'

    register = ac.create_callback_registrar()

    @register.a.b
    def callback_a_b():
        return 'a.b'

    register = ac.create_callback_registrar()

    @register.a.b.bar
    def callback_a_b_bar():
        return 'a.b.bar'

    accessor = ac.registered_callback_and_options

    callback, options = accessor(['foo'])
    assert {'whatever': 42} == options
    assert 'foo' == callback()

    callback, options = accessor(['a', 'b'])
    assert None is options
    assert 'a.b' == callback()

    callback, options = accessor(['a', 'b', 'bar'])
    assert None is options
    assert 'a.b.bar' == callback()
