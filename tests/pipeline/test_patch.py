import pytest

from tests.utils.attr_config import *
from restpf.resource.definition import (
    Attributes,
    Resource,
)
from restpf.pipeline.single_resource.patch import (
    PatchSingleResourcePipelineRunner,
)


def build_shared_resource():
    return Resource(
        'test',
        Attributes({
            'foo': Integer,
            'bar': Float,
        }),
    )


@pytest.mark.asyncio
async def test_simple_patch():
    test = build_shared_resource()
    called = []

    @test.attributes.foo.PATCH
    def foo(resource_id, state):
        called.append(foo)

        assert 42 == resource_id
        assert 1 == state.value

    tp = PatchSingleResourcePipelineRunner()
    tp.build_pipeline_state(
        raw_resource_id=42,
        raw_attributes={
            'foo': 1,
        },
        raw_relationships={},
    )
    tp.build_context_rule()
    tp.build_state_tree_builder()
    tp.build_representation_generator()
    tp.set_resource(test)

    await tp.run_pipeline()
    assert [foo] == called
