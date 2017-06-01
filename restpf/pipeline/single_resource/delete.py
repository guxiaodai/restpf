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
        self.input_attributes = None
        self.input_relationships = None
        self.input_resource_id = self._get_id_state_for_input(resource)

    def build_output_state(self, resource):
        self.output_attributes = None
        self.output_relationships = None
        self.output_resource_id = None


class DeleteSingleResourceRepresentationGenerator(RepresentationGenerator):

    def generate_representation(self, resource):
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
