import pytest

from tests.utils.attr_config import *
from restpf.resource.definition import (
    Attributes,
    Resource,
)
from restpf.pipeline.single_resource.get import (
    GetSingleResourcePipelineRunner,
)


@pytest.mark.asyncio
async def test_simple_get():
    test = Resource(
        'test',
        Attributes({
            'foo': Integer,
            'bar': String,
        }),
        None,
    )

    @test.attributes.foo.GET
    def get_foo(resource_id):
        return resource_id.value * 10

    @test.attributes.bar.GET
    async def get_bar(resource_id):
        return str(resource_id.value)

    tp = GetSingleResourcePipelineRunner()
    tp.build_context_rule()
    tp.build_state_tree_builder(raw_resource_id=42)
    tp.build_representation_generator()
    tp.set_resource(test)

    pipeline = await tp.run_pipeline()

    expected = {
        'id': 42,
        'type': 'test',
        'attributes': {
            'foo': {
                'type': 'integer',
                'value': 420,
            },
            'bar': {
                'type': 'string',
                'value': '42',
            }
        },
        'relationships': {},
    }
    assert expected == pipeline.representation
