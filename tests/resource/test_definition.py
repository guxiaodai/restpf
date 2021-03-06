from tests.utils.attr_config import *

from restpf.resource.attributes import (
    String,
    Object,
    AttributeContextOperator,
    HTTPMethodConfig,
)
from restpf.resource.definition import (
    AttributeCollection,
    Attributes,
    Relationships,
    Resource,
)


def test_registration():
    ac = AttributeCollection(
        ('foo', String()),
        ('a', Object(
            ('b', Object(
                ('bar', String()),
            )),
        )),
    )

    register = ac.create_callback_registrar()

    @register.GET
    def callback_top_level():
        return 'top_level'

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

    callback, options = accessor([], HTTPMethodConfig.GET)
    assert None is options
    assert 'top_level' == callback()

    callback, options = accessor(['foo'], HTTPMethodConfig.GET)
    assert {'whatever': 42} == options
    assert 'foo.GET' == callback()

    callback, options = accessor(['foo'], HTTPMethodConfig.POST)
    assert None is options
    assert 'foo.POST' == callback()

    callback, options = accessor(['a', 'b'], HTTPMethodConfig.POST)
    assert None is options
    assert 'a.b' == callback()

    callback, options = accessor(['a', 'b', 'bar'], HTTPMethodConfig.PATCH)
    assert None is options
    assert 'a.b.bar' == callback()


def test_registration_by_dict():
    ac = AttributeCollection({
        'foo': String,
        'a': Object({
            'b': Object({
                'bar': String,
            }),
        }),
    })
    assert ac


def test_resource_definition():
    rd = Resource(
        'test',
        Attributes({
            'foo': String,
            'a': Object({
                'b': Object({
                    'bar': String,
                }),
            }),
        }),
        None,
    )
    assert rd.attributes.a.b.bar
    assert isinstance(rd.attributes_obj, Attributes)


def test_validate_on_empty_relationships():
    rel = Relationships()
    context = AttributeContextOperator(HTTPMethodConfig.POST)
    obj = create_attribute_state_tree_for_input(
        rel.attr_obj,
        {},
    )
    assert obj.validate(context)
