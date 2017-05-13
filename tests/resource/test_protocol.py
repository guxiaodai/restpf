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
)
from restpf.utils.helper_functions import async_call


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
        rd, None,
    )

    assert list(range(1, 5)) == list(map(lambda x: x[0](), ret))
