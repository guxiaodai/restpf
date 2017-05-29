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
    # ContextRuleWithInputBinding,
    ContextRule,
    CallbackKwargsStateVariableMapper,
    StateTreeBuilder,
    RepresentationGenerator,
    ResourceState,
    PipelineRunner,
    SingleResourcePipeline,
)


class GetSingleResourceCallbackKwargsStateVariableMapper(
    CallbackKwargsStateVariableMapper
):
    PROXY_ATTRS = [
        'raw_resource_id',
    ]
    ATTR2KWARG = {
        'raw_resource_id': 'resource_id',
    }


class GetSingleResourceContextRule(ContextRule):

    HTTPMethod = HTTPMethodConfig.GET


class GetSingleResourceStateTreeBuilder(StateTreeBuilder):

    def build_input_state(self, resource):
        return ResourceState(
            attributes=None,
            relationships=None,
            # for id validation.
            resource_id=self._get_id_state_for_input(resource),
        )

    def build_output_state(self, resource, raw_obj):
        return ResourceState(
            attributes=create_attribute_state_tree_for_output(
                resource.attributes_obj.attr_obj,
                raw_obj.attributes,
            ),
            relationships=create_attribute_state_tree_for_output(
                resource.relationships_obj.attr_obj,
                raw_obj.relationships,
            ),
            # no need to validate.
            resource_id=None,
        )


class GetSingleResourceRepresentationGenerator(RepresentationGenerator):

    def generate_representation(self, resource, output_state):
        return {
            'id': self.raw_resource_id,
            'type': resource.name,
            'attributes': output_state.attributes.serialize(),
            'relationships': output_state.relationships.serialize(),
        }


class GetSingleResourcePipelineState(metaclass=StateCreator):

    ATTRS = [
        'raw_resource_id',
    ]


class GetSingleResourcePipelineRunner(PipelineRunner):

    CALLBACK_KWARGS_CONTROLLER_CLSES = [
        GetSingleResourceCallbackKwargsStateVariableMapper,
    ]
    CONTEXT_RULE_CLS = GetSingleResourceContextRule

    STATE_TREE_BUILDER_CLS = GetSingleResourceStateTreeBuilder
    REPRESENTATION_GENERATOR_CLS = GetSingleResourceRepresentationGenerator

    PIPELINE_CLS = SingleResourcePipeline
    PIPELINE_STATE_CLS = GetSingleResourcePipelineState
