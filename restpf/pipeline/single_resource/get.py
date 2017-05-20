from restpf.utils.helper_functions import (
    init_named_args,
)
from restpf.resource.attributes import (
    HTTPMethodConfig,
)
from restpf.resource.attribute_states import (
    create_attribute_state_tree,
    node2statecls_default_input,
    node2statecls_default_output,
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
            mapping = node2statecls_default_input
        else:
            mapping = node2statecls_default_output

        return create_attribute_state_tree(
            resource.id_obj,
            self.raw_resource_id,
            mapping,
        )

    def build_input_state(self, resource):
        return ResourceState(
            attributes=None,
            relationships=None,
            resource_id=self._get_id_state(resource, True),
        )

    def build_output_state(self, resource, raw_obj):
        return ResourceState(
            attributes=create_attribute_state_tree(
                resource.attributes_obj.attr_obj,
                raw_obj.attributes,
                node2statecls_default_output,
            ),
            relationships=create_attribute_state_tree(
                resource.relationships_obj.attr_obj,
                raw_obj.relationships,
                node2statecls_default_output,
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
