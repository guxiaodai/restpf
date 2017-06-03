import pytest

from tests.utils.attr_config import *
from restpf.resource.definition import (
    Attributes,
    Resource,
)
from restpf.pipeline.single_resource.delete import (
    DeleteSingleResourcePipelineRunner,
)


@pytest.mark.asyncio
async def test_simple_delete():
    test = Resource(
        'test',
        Attributes({
            'foo': Integer,
            'bar': String,
        }),
        None,
    )

    @test.special_hooks.before_all.DELETE
    def foo(resource_id):
        assert 42 == resource_id.value

    tp = DeleteSingleResourcePipelineRunner()
    tp.build_pipeline_state(raw_resource_id=42)
    tp.build_context_rule()
    tp.build_state_tree_builder()
    tp.build_representation_generator()
    tp.set_resource(test)

    await tp.run_pipeline()
