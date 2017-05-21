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

    @test.attributes.a.POST
    def a(resource_id, state):
        called.append('a')

        assert resource_id is None
        assert 1 == state.b.c.value
        assert 2 == state.d.value

    @test.attributes.a.b.c.POST
    def c(state):
        called.append('c')

        assert 1 == state.value

    tp = PostSingleResourcePipelineRunner()
    tp.build_context_rule(
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
    tp.build_state_tree_builder()
    tp.build_representation_generator()
    tp.set_resource(test)

    await tp.run_pipeline()
    # no order required.
    assert set(['a', 'c']) == set(called)
