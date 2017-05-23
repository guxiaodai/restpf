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
    RepresentationGenerator,
    PipelineBase,
    ResourceState,
    _merge_output_of_callbacks,
    PipelineRunner,
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
                node2statecls_default_input,
            )
            resource_id = create_attribute_state_tree(
                resource.id_obj,
                None,
                node2statecls_default_input,
            )
            return ResourceState(attributes, None, resource_id)

        async def build_output_state(self, resource, raw_obj):
            attributes = create_attribute_state_tree(
                resource.attributes_obj.attr_obj,
                # output.
                raw_obj.attributes,
                node2statecls_default_output,
            )

            assert not raw_obj.resource_id
            resource_id = create_attribute_state_tree(
                resource.id_obj,
                42,
                node2statecls_default_output,
            )
            return ResourceState(attributes, None, resource_id)

    class TestRepGen(RepresentationGenerator):

        def generate_representation(self, resource, output_state):

            return {
                'id': output_state.resource_id.serialize(),
                'attributes': output_state.attributes.serialize(),
            }

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

    called = []

    @resource.special_hooks.before_all.POST
    def run_before_all(callback_kwargs):
        called.append(1)
        callback_kwargs.register('whatever', 42)

    @resource.special_hooks.after_all.POST
    def run_after_all(whatever):
        called.append(4)
        assert 42 == whatever

    @resource.attributes.foo.POST
    def process_foo(state):
        called.append(2)
        return state.value + 10

    @resource.attributes.bar.POST
    def process_bar(state):
        called.append(3)
        return state.value + ' suffix'

    class TestPipelineRunner(PipelineRunner):

        CONTEXT_RULE_CLS = TestContextRule
        STATE_TREE_BUILDER_CLS = TestStateBuilder
        REPRESENTATION_GENERATOR_CLS = TestRepGen
        PIPELINE_CLS = TestPipeline

    tp = TestPipelineRunner()
    tp.build_context_rule()
    tp.build_state_tree_builder()
    tp.build_representation_generator()
    tp.set_resource(resource)

    pipeline = await tp.run_pipeline()

    assert 4 == len(called)
    assert 1 == called[0]
    assert 4 == called[-1]

    expected = {
        'id': {
            'type': 'integer',
            'value': 42,
        },
        'attributes': {
            'foo': {
                'type': 'integer',
                'value': 52,
            },
            'bar': {
                'type': 'string',
                'value': 'some name suffix',
            },
        },
    }
    assert expected == pipeline.representation
