from restpf.utils.helper_classes import (
    StateCreator,
)
from restpf.resource.attributes import (
    HTTPMethodConfig,
)
from restpf.resource.attribute_states import (
    create_attribute_state_tree_for_output,
)

from restpf.pipeline.protocol import (
    ContextRule,
    CallbackKwargsStateVariableMapper,
    StateTreeBuilder,
    RepresentationGenerator,
    PipelineRunner,
    SingleResourcePipeline,
)


class GetSingleResourcePipelineState(metaclass=StateCreator):

    ATTRS = [
        'raw_resource_id',
    ]


class GetSingleResourceCallbackKwargsStateVariableMapper(
    CallbackKwargsStateVariableMapper
):
    ATTR2KWARG = {
        # raw submitted..
        'raw_resource_id': 'raw_resource_id',
        # parsed submitted.
        'input_resource_id': 'resource_id',
    }


class GetSingleResourceContextRule(ContextRule):

    HTTPMethod = HTTPMethodConfig.GET


class GetSingleResourceStateTreeBuilder(StateTreeBuilder):

    def build_input_state(self, resource):
        self.input_attributes = None
        self.input_relationships = None
        self.input_resource_id = self._get_id_state_for_input(resource)

    def build_output_state(self, resource):
        self.output_attributes = create_attribute_state_tree_for_output(
            resource.attributes_obj.attr_obj,
            self.internal_attributes,
        )
        self.output_relationships = create_attribute_state_tree_for_output(
            resource.relationships_obj.attr_obj,
            self.internal_relationships,
        )
        # no need to validate.
        self.output_resource_id = None


class GetSingleResourceRepresentationGenerator(RepresentationGenerator):

    def generate_representation(self, resource):
        return {
            'id': self.input_resource_id.value,
            'type': resource.name,
            'attributes': self.output_attributes.serialize(),
            'relationships': self.output_relationships.serialize(),
        }


class GetSingleResourcePipelineRunner(PipelineRunner):

    CALLBACK_KWARGS_CONTROLLER_CLSES = [
        GetSingleResourceCallbackKwargsStateVariableMapper,
    ]
    CONTEXT_RULE_CLS = GetSingleResourceContextRule

    STATE_TREE_BUILDER_CLS = GetSingleResourceStateTreeBuilder
    REPRESENTATION_GENERATOR_CLS = GetSingleResourceRepresentationGenerator

    PIPELINE_CLS = SingleResourcePipeline
    PIPELINE_STATE_CLS = GetSingleResourcePipelineState
