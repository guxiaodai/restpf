from collections import deque

from restpf.utils.helper_classes import (
    ProxyStateOperator,
)
from restpf.resource.attributes import (
    AttributeContextOperator,
)
from restpf.resource.attribute_states import (
    create_attribute_state_tree_for_input,
    create_attribute_state_tree_for_output,
)

from .states import (
    CallbackKwargsProcessor,
    CallbackKwargsRegistrar,
    _INPUT_STATE_NAMES,
    _INTERNAL_STATE_NAMES,
    _OUTPUT_STATE_NAMES,
)


class ContextRule(ProxyStateOperator):

    HTTPMethod = None

    PROXY_ATTRS = [
        *_INPUT_STATE_NAMES,
        *_OUTPUT_STATE_NAMES,
    ]

    def __init__(self):
        self._callback_kwargs_processor = CallbackKwargsProcessor()
        self._callback_kwargs_registrar = CallbackKwargsRegistrar()

        self._callback_kwargs_processor.add_controller(
            self._callback_kwargs_registrar,
        )

    def _default_validator(self, names):
        context = AttributeContextOperator(self.HTTPMethod)
        return all(map(
            lambda x: x.validate(context),
            filter(
                bool,
                map(
                    lambda name: getattr(self, name),
                    names,
                )
            ),
        ))

    async def validate_input_state(self):
        return self._default_validator(_INPUT_STATE_NAMES)

    async def validate_output_state(self):
        return self._default_validator(_OUTPUT_STATE_NAMES)

    def _select_callbacks(self, query, root_attr, root_state):
        queue = deque()
        queue.append(
            (root_attr, root_state),
        )

        ret = []

        while queue:
            attr, state = queue.popleft()
            callback, options = query(attr.bh_path, self.HTTPMethod)

            if callback and (state or root_state is None):
                ret.append(
                    (
                        callback,
                        # TODO: replace hardcoded value.
                        {
                            'attr': attr,
                            'state': state,
                            'options': options,
                        },
                    ),
                )

            for name, child_attr in attr.bh_named_children.items():
                child_state = getattr(state, name) if state else None
                queue.append(
                    (child_attr, child_state),
                )

        return ret

    async def select_callbacks(self, resource):
        '''
        return ordered collection_name -> [(callback, attr, state), ...].
        '''

        ret = {}
        for key in ['special_hooks', 'attributes', 'relationships']:
            if getattr(resource, key) is None:
                continue

            attr_collection = getattr(resource, f'{key}_obj')

            ret[key] = self._select_callbacks(
                getattr(
                    attr_collection,
                    'get_registered_callback_and_options',
                ),
                getattr(attr_collection, 'attr_obj'),
                # TODO: too dirty, fix it.
                getattr(self, f'input_{key}', None),
            )

        return ret

    def attach_callback_kwargs_controller(self, controller):
        self._callback_kwargs_processor.add_controller(controller)

    async def callback_kwargs(self, attr, state):
        return self._callback_kwargs_processor.callback_kwargs(attr, state)


class StateTreeBuilder(ProxyStateOperator):

    PROXY_ATTRS = [
        *_INPUT_STATE_NAMES,
        *_INTERNAL_STATE_NAMES,
        *_OUTPUT_STATE_NAMES,

        'raw_resource_id',
    ]

    def _get_id_state_for_input(self, resource):
        return create_attribute_state_tree_for_input(
            resource.id_obj,
            self.raw_resource_id,
        )

    def _get_id_state_for_output(self, resource):
        return create_attribute_state_tree_for_output(
            resource.id_obj,
            self.raw_resource_id,
        )

    async def build_input_state(self, resource):
        raise NotImplemented

    async def build_output_state(self, resource):
        raise NotImplemented


class RepresentationGenerator(ProxyStateOperator):

    PROXY_ATTRS = [
        *_OUTPUT_STATE_NAMES,

        'raw_resource_id',
    ]

    async def generate_representation(self, resource):
        return {}
