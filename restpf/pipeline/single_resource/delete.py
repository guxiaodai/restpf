from restpf.utils.helper_classes import (
    StateCreator,
)
from restpf.resource.attributes import (
    HTTPMethodConfig,
)

from restpf.pipeline.protocol import (
    ContextRule,
    CallbackKwargsStateVariableMapper,
    StateTreeBuilder,
    RepresentationGenerator,
    ResourceState,
    PipelineRunner,
    SingleResourcePipeline,
)


class DeleteSingleResourcePipelineState(metaclass=StateCreator):

    ATTRS = [
        'raw_resource_id',
    ]


class DeleteSingleResourceCallbackKwargsStateVariableMapper(
    CallbackKwargsStateVariableMapper
):
    ATTR2KWARG = {
        'raw_resource_id': 'resource_id',
    }


class DeleteSingleResourceContextRule(ContextRule):

    HTTPMethod = HTTPMethodConfig.DELETE


class DeleteSingleResourceStateTreeBuilder(StateTreeBuilder):

    def build_input_state(self, resource):
        return ResourceState(
            attributes=None,
            relationships=None,
            # for id validation.
            resource_id=self._get_id_state_for_input(resource),
        )

    def build_output_state(self, resource, raw_obj):
        return ResourceState(
            attributes=None,
            relationships=None,
            resource_id=None,
        )


class DeleteSingleResourceRepresentationGenerator(RepresentationGenerator):

    def generate_representation(self, resource, output_state):
        return None


class DeleteSingleResourcePipelineRunner(PipelineRunner):

    CALLBACK_KWARGS_CONTROLLER_CLSES = [
        DeleteSingleResourceCallbackKwargsStateVariableMapper,
    ]
    CONTEXT_RULE_CLS = DeleteSingleResourceContextRule

    STATE_TREE_BUILDER_CLS = DeleteSingleResourceStateTreeBuilder
    REPRESENTATION_GENERATOR_CLS = DeleteSingleResourceRepresentationGenerator

    PIPELINE_CLS = SingleResourcePipeline
    PIPELINE_STATE_CLS = DeleteSingleResourcePipelineState
