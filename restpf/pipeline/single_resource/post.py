from restpf.resource.attributes import (
    HTTPMethodConfig,
)
from restpf.resource.attribute_states import (
    create_attribute_state_tree_for_input,
)
from restpf.pipeline.protocol import (
    ContextRuleWithInputBinding,
    StateTreeBuilder,
    RepresentationGenerator,
    ResourceState,
    PipelineRunner,
    SingleResourcePipeline,
)


class PostSingleResourceContextRule(metaclass=ContextRuleWithInputBinding):

    HTTPMethod = HTTPMethodConfig.POST

    INPUT_ATTR2KWARG = {
        'raw_resource_id': 'resource_id',
        'raw_attributes': 'raw_attributes',
        'raw_relationships': 'raw_relationships',
    }


class PostSingleResourceStateTreeBuilder(StateTreeBuilder):

    def build_input_state(self, resource):
        return ResourceState(
            attributes=create_attribute_state_tree_for_input(
                resource.attributes_obj.attr_obj,
                self.context_rule.raw_attributes,
            ),
            relationships=create_attribute_state_tree_for_input(
                resource.relationships_obj.attr_obj,
                self.context_rule.raw_relationships,
            ),
            resource_id=self._get_id_state_for_input(resource),
        )

    def build_output_state(self, resource, raw_obj):
        return ResourceState(
            attributes=None,
            relationships=None,
            resource_id=None,
        )


class PostSingleResourceRepresentationGenerator(RepresentationGenerator):

    def generate_representation(self, resource, output_state):
        # no return.
        return None


class PostSingleResourcePipelineRunner(PipelineRunner):

    CONTEXT_RULE_CLS = PostSingleResourceContextRule
    STATE_TREE_BUILDER_CLS = PostSingleResourceStateTreeBuilder
    REPRESENTATION_GENERATOR_CLS = PostSingleResourceRepresentationGenerator
    PIPELINE_CLS = SingleResourcePipeline
