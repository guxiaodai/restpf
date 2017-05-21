from restpf.resource.attributes import (
    HTTPMethodConfig,
)
from restpf.resource.attribute_states import (
    create_attribute_state_tree_for_input,
    create_attribute_state_tree_for_output,
)
from restpf.pipeline.protocol import (
    ContextRuleWithInputBinding,
    StateTreeBuilder,
    RepresentationGenerator,
    ResourceState,
    PipelineRunner,
    SingleResourcePipeline,
)


class GetSingleResourceContextRule(metaclass=ContextRuleWithInputBinding):

    HTTPMethod = HTTPMethodConfig.GET

    INPUT_ATTR2KWARG = {
        'raw_resource_id': 'resource_id',
    }


class GetSingleResourceStateTreeBuilder(StateTreeBuilder):

    def _get_id_state(self, resource, is_input):
        if is_input:
            creator = create_attribute_state_tree_for_input
        else:
            creator = create_attribute_state_tree_for_output

        return creator(
            resource.id_obj,
            self.context_rule.raw_resource_id,
        )

    def build_input_state(self, resource):
        return ResourceState(
            attributes=None,
            relationships=None,
            # for id validation.
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
            # no need to validate.
            resource_id=None,
        )


class GetSingleResourceRepresentationGenerator(RepresentationGenerator):

    def generate_representation(self, resource, output_state):
        return {
            'id': self.context_rule.raw_resource_id,
            'type': resource.name,
            'attributes': output_state.attributes.serialize(),
            'relationships': output_state.relationships.serialize(),
        }


class GetSingleResourcePipelineRunner(PipelineRunner):

    CONTEXT_RULE_CLS = GetSingleResourceContextRule
    STATE_TREE_BUILDER_CLS = GetSingleResourceStateTreeBuilder
    REPRESENTATION_GENERATOR_CLS = GetSingleResourceRepresentationGenerator
    PIPELINE_CLS = SingleResourcePipeline
