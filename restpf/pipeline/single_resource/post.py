from restpf.utils.helper_classes import (
    StateCreator,
)
from restpf.resource.attributes import (
    HTTPMethodConfig,
    AttributeContextOperator,
)
from restpf.resource.attribute_states import (
    create_attribute_state_tree_for_input,
    create_attribute_state_tree_for_output,
)
from restpf.pipeline.protocol import (
    ContextRule,
    CallbackKwargsStateVariableMapper,
    CallbackKwargsVariableCollector,
    StateTreeBuilder,
    RepresentationGenerator,
    PipelineRunner,
    SingleResourcePipeline,
)


class PostSingleResourcePipelineState(metaclass=StateCreator):

    ATTRS = [
        'raw_resource_id',
        'raw_attributes',
        'raw_relationships',
    ]


class PostSingleResourceCallbackKwargsStateVariableMapper(
    CallbackKwargsStateVariableMapper,
):
    ATTR2KWARG = {
        # raw submitted..
        'raw_resource_id': 'raw_resource_id',
        'raw_attributes': 'raw_attributes',
        'raw_relationships': 'raw_relationships',
        # parsed submitted.
        'input_resource_id': 'submitted_resource_id',
    }


class PostSingleResourceCallbackKwargsVariableCollector(
    CallbackKwargsVariableCollector,
):
    VARIABLES = [
        'generated_resource_id',
    ]

    def preprocessor_generated_resource_id(self, value):
        state = create_attribute_state_tree_for_output(
            self.resource.id_obj, value,
        )
        if not state.validate(AttributeContextOperator(HTTPMethodConfig.GET)):
            raise RuntimeError('generated_resource_id is wrong.')

        return state


class PostSingleResourceContextRule(ContextRule):

    HTTPMethod = HTTPMethodConfig.POST


class PostSingleResourceStateTreeBuilder(StateTreeBuilder):

    PROXY_ATTRS = [
        'raw_attributes',
        'raw_relationships',
    ]

    def build_input_state(self, resource):
        self.input_attributes = create_attribute_state_tree_for_input(
            resource.attributes_obj.attr_obj,
            self.raw_attributes,
        )
        self.input_relationships = create_attribute_state_tree_for_input(
            resource.relationships_obj.attr_obj,
            self.raw_relationships,
        )
        self.input_resource_id = self._get_id_state_for_input(resource)

    def build_output_state(self, resource):
        self.output_attributes = None
        self.output_relationships = None
        self.output_resource_id = None


class PostSingleResourceRepresentationGenerator(RepresentationGenerator):

    def generate_representation(self, resource):
        # no return.
        return None


class PostSingleResourcePipelineRunner(PipelineRunner):

    CALLBACK_KWARGS_CONTROLLER_CLSES = [
        PostSingleResourceCallbackKwargsStateVariableMapper,
        PostSingleResourceCallbackKwargsVariableCollector,
    ]
    CONTEXT_RULE_CLS = PostSingleResourceContextRule

    STATE_TREE_BUILDER_CLS = PostSingleResourceStateTreeBuilder
    REPRESENTATION_GENERATOR_CLS = PostSingleResourceRepresentationGenerator

    PIPELINE_CLS = SingleResourcePipeline
    PIPELINE_STATE_CLS = PostSingleResourcePipelineState
