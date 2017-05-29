import pytest

from tests.utils.attr_config import *
from restpf.resource.definition import (
    Attributes,
    Resource,
)
from restpf.pipeline.single_resource.post import (
    PostSingleResourcePipelineRunner,
)


def build_shared_resource():
    return Resource(
        'test',
        Attributes({
            'foo': Integer,
            'a': Object({
                'b': Object({
                    'c': Integer,
                }),
                'd': Integer,
            }),
        }),
    )


@pytest.mark.asyncio
async def test_simple_post():
    test = build_shared_resource()

    called = []

    @test.attributes.a.POST(before_all=True)
    def a(submitted_resource_id, state, var_collector):
        called.append('a')

        assert submitted_resource_id is None
        assert 1 == state.b.c.value
        assert 2 == state.d.value

        var_collector.generated_resource_id = 999

    @test.attributes.a.b.c.POST
    def c(generated_resource_id, state):
        called.append('c')

        assert 999 == generated_resource_id
        assert 1 == state.value

    tp = PostSingleResourcePipelineRunner()
    tp.build_pipeline_state(
        raw_resource_id=None,
        raw_attributes={
            'foo': 42,
            'a': {
                'b': {
                    'c': {
                        'type': 'integer',
                        'value': 1,
                    },
                },
                'd': 2,
            }
        },
        raw_relationships={},
    )
    tp.build_context_rule()
    tp.build_state_tree_builder()
    tp.build_representation_generator()
    tp.set_resource(test)

    await tp.run_pipeline()

    # no order required.
    assert ['a', 'c'] == called
    assert 999 == tp.pipeline_state.var_collector['generated_resource_id']
