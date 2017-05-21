from restpf.utils.helper_functions import (
    init_named_args,
)
from restpf.resource.attributes import (
    HTTPMethodConfig,
)
from restpf.resource.attribute_states import (
    create_attribute_state_tree_for_input,
    create_attribute_state_tree_for_output,
)
from restpf.pipeline.protocol import (
    ContextRule,
    StateTreeBuilder,
    RepresentationGenerator,
    ResourceState,
    PipelineRunner,
    SingleResourcePipeline,
)


class GetSingleResourceContextRule(ContextRule):

    HTTPMethod = HTTPMethodConfig.GET


class GetSingleResourceStateTreeBuilder(StateTreeBuilder):

    @init_named_args('raw_resource_id')
    def __init__(self):
        pass

    def _get_id_state(self, resource, is_input):
        if is_input:
            creator = create_attribute_state_tree_for_input
        else:
            creator = create_attribute_state_tree_for_output

        return creator(resource.id_obj, self.raw_resource_id)

    def build_input_state(self, resource):
        return ResourceState(
            attributes=None,
            relationships=None,
            resource_id=self._get_id_state(resource, True),
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
            resource_id=self._get_id_state(resource, False),
        )


class GetSingleResourceRepresentationGenerator(RepresentationGenerator):

    def generate_representation(self, resource, output_state):
        return {
            'id': output_state.resource_id.value,
            'type': resource.name,
            'attributes': output_state.attributes.serialize(),
            'relationships': output_state.relationships.serialize(),
        }


class GetSingleResourcePipelineRunner(PipelineRunner):

    CONTEXT_RULE_CLS = GetSingleResourceContextRule
    STATE_TREE_BUILDER_CLS = GetSingleResourceStateTreeBuilder
    REPRESENTATION_GENERATOR_CLS = GetSingleResourceRepresentationGenerator
    PIPELINE_CLS = SingleResourcePipeline
