import pytest

from restpf.resource.attributes import (
    String,
    Object,
    HTTPMethodConfig,
)
from restpf.resource.definition import (
    Attributes,
    Resource,
)
from restpf.pipeline.protocol import (
    ContextRule,
    ResourceState,
    _merge_output_of_callbacks,
)
from restpf.utils.helper_functions import async_call
from restpf.utils.helper_classes import (
    TreeState,
)


@pytest.mark.asyncio
async def test_resource_definition():
    class TestContext(ContextRule):
        HTTPMethod = HTTPMethodConfig.GET

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

    @rd.attributes.GET
    def f1():
        return 1

    @rd.attributes.foo.GET
    def f2():
        return 2

    @rd.attributes.a.b.GET
    def f3():
        return 3

    @rd.attributes.a.b.bar.GET
    def f4():
        return 4

    ct = TestContext()
    ret = await async_call(
        ct.select_callbacks,
        rd, ResourceState(None, None, None),
    )

    assert list(range(1, 5)) == list(map(lambda x: x[0](), ret))


def test_merge_tree_state():
    ts = TreeState()
    ts.touch([]).value = {
        'a': {
            'b': 'should be override',
            'c': 2,
        },
        'd': 'should be override',
    }
    ts.touch(['a', 'b']).value = 1
    ts.touch(['d']).value = 3

    expected = {
        'a': {
            'b': 1,
            'c': 2,
        },
        'd': 3,
    }
    assert expected == _merge_output_of_callbacks(ts)
