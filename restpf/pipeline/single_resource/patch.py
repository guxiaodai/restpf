from restpf.resource.attributes import (
    HTTPMethodConfig,
)
from restpf.pipeline.protocol import (
    ContextRule,
    CallbackKwargsStateVariableMapper,
    RepresentationGenerator,
    PipelineRunner,
    SingleResourcePipeline,
)

from .post import (
    PostSingleResourcePipelineState,
    PostSingleResourceStateTreeBuilder,
)


class PatchSingleResourcePipelineState(
    PostSingleResourcePipelineState,
):
    pass


class PatchSingleResourceCallbackKwargsStateVariableMapper(
    CallbackKwargsStateVariableMapper,
):
    ATTR2KWARG = {
        # raw submitted..
        'raw_resource_id': 'raw_resource_id',
        'raw_attributes': 'raw_attributes',
        'raw_relationships': 'raw_relationships',
        # parsed submitted.
        'input_resource_id': 'resource_id',
    }


class PatchSingleResourceContextRule(ContextRule):

    HTTPMethod = HTTPMethodConfig.PATCH


class PatchSingleResourceStateTreeBuilder(
    PostSingleResourceStateTreeBuilder,
):
    pass


class PatchSingleResourceRepresentationGenerator(RepresentationGenerator):

    def generate_representation(self, resource):
        # no return.
        return None


class PatchSingleResourcePipelineRunner(PipelineRunner):

    CALLBACK_KWARGS_CONTROLLER_CLSES = [
        PatchSingleResourceCallbackKwargsStateVariableMapper,
    ]
    CONTEXT_RULE_CLS = PatchSingleResourceContextRule

    STATE_TREE_BUILDER_CLS = PatchSingleResourceStateTreeBuilder
    REPRESENTATION_GENERATOR_CLS = PatchSingleResourceRepresentationGenerator

    PIPELINE_CLS = SingleResourcePipeline
    PIPELINE_STATE_CLS = PatchSingleResourcePipelineState
