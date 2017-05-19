import pytest

from tests.utils.attr_config import *

from restpf.utils.helper_functions import (
    async_call,
)
from restpf.utils.helper_classes import (
    TreeState,
)
from restpf.resource.definition import (
    Attributes,
    Resource,
)
from restpf.pipeline.protocol import (
    ContextRule,
    StateTreeBuilder,
    PipelineBase,
    ResourceState,
    _merge_output_of_callbacks,
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

    assert 'attributes' in ret
    assert list(range(1, 5)) == list(map(lambda x: x[0](), ret['attributes']))


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


@pytest.mark.asyncio
async def test_pipeline():

    class TestContextRule(ContextRule):
        HTTPMethod = HTTPMethodConfig.POST

    class TestStateBuilder(StateTreeBuilder):

        async def build_input_state(self, resource):
            attributes = create_attribute_state_tree(
                resource.attributes_obj.attr_obj,
                # input.
                {
                    'foo': 42,
                    'bar': 'some name',
                },
                node2statecls_input,
            )
            resource_id = create_attribute_state_tree(
                resource.id_node,
                None,
                node2statecls_input,
            )
            return ResourceState(attributes, None, resource_id)

        async def build_output_state(self, resource, raw_obj):
            attributes = create_attribute_state_tree(
                resource.attributes_obj.attr_obj,
                # output.
                raw_obj.attributes,
                node2statecls_output,
            )

            assert not raw_obj.resource_id
            resource_id = create_attribute_state_tree(
                resource.id_node,
                42,
                node2statecls_output,
            )
            return ResourceState(attributes, None, resource_id)

    class TestPipeline(PipelineBase):
        pass

    resource = Resource(
        'test',
        Attributes({
            'foo': Integer,
            'bar': String,
        }),
        None,
    )

    @resource.attributes.foo.POST
    def process_foo(state):
        return state.value + 10

    @resource.attributes.bar.POST
    def process_bar(state):
        return state.value + ' suffix'

    pipeline = TestPipeline(resource, TestContextRule(), TestStateBuilder())
    await pipeline.run()

    expected = {
        'foo': {
            'type': 'integer',
            'value': 52,
        },
        'bar': {
            'type': 'string',
            'value': 'some name suffix',
        },
    }
    assert expected == pipeline.output_state.attributes.serialize()
