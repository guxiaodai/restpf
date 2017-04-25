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

    @register.foo.GET(whatever=42)
    def callback_foo_GET():
        return 'foo.GET'

    register = ac.create_callback_registrar()

    @register.foo.POST
    def callback_foo_POST():
        return 'foo.POST'

    register = ac.create_callback_registrar()

    @register.a.b.POST
    def callback_a_b():
        return 'a.b'

    register = ac.create_callback_registrar()

    @register.a.b.bar.PATCH
    def callback_a_b_bar():
        return 'a.b.bar'

    accessor = ac.get_registered_callback_and_options

    callback, options = accessor(['foo'], 'GET')
    assert {'whatever': 42} == options
    assert 'foo.GET' == callback()

    callback, options = accessor(['foo'], 'POST')
    assert None is options
    assert 'foo.POST' == callback()

    callback, options = accessor(['a', 'b'], 'POST')
    assert None is options
    assert 'a.b' == callback()

    callback, options = accessor(['a', 'b', 'bar'], 'PATCH')
    assert None is options
    assert 'a.b.bar' == callback()
