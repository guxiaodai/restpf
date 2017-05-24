from collections import deque

from restpf.utils.helper_functions import (
    method_named_args,
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
)


class ContextRule:

    HTTPMethod = None

    def __init__(self):
        self._callback_kwargs_processor = CallbackKwargsProcessor()
        self._callback_kwargs_registrar = CallbackKwargsRegistrar()

        self._callback_kwargs_processor.add_controller(
            self._callback_kwargs_registrar,
        )

    def _default_validator(self, state):
        context = AttributeContextOperator(self.HTTPMethod)
        return all(map(
            lambda x: x.validate(context),
            filter(
                bool,
                [
                    state.resource_id,
                    state.attributes,
                    state.relationships,
                ],
            ),
        ))

    async def validate_input_state(self, state):
        return self._default_validator(state)

    async def validate_output_state(self, state):
        return self._default_validator(state)

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

    async def select_callbacks(self, resource, state):
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
                getattr(state, key, None),
            )

        return ret

    async def callback_kwargs(self, attr, state):
        return self._callback_kwargs_processor.callback_kwargs(attr, state)


class ContextRuleWithInputBinding(type):

    @classmethod
    def _inject_methods(cls, attr2kwarg, resultcls):

        # build __init__.
        @method_named_args(*attr2kwarg.keys())
        def __init__(self):
            super(type(self), self).__init__()
            # register kwargs.
            for attr_name, kwarg_name in attr2kwarg.items():
                self._callback_kwargs_registrar.register(
                    kwarg_name, getattr(self, attr_name),
                )

        resultcls.__init__ = __init__

    def __new__(cls, name, bases, namespace):
        # get mapping: attr_name -> kwarg_name
        attr2kwarg = namespace.get('INPUT_ATTR2KWARG')

        # generate class first.
        if attr2kwarg:
            # inject base class.
            bases = bases + (ContextRule,)

        resultcls = type.__new__(cls, name, bases, namespace)

        if attr2kwarg:
            # only trigger when the INPUT_ATTR2KWARG is defined.
            cls._inject_methods(attr2kwarg, resultcls)

        return resultcls


class _ContextRuleBinder:

    @method_named_args('context_rule')
    def bind_context_rule(self):
        pass


class StateTreeBuilder(_ContextRuleBinder):

    def _get_id_state_for_input(self, resource):
        return create_attribute_state_tree_for_input(
            resource.id_obj,
            self.context_rule.raw_resource_id,
        )

    def _get_id_state_for_output(self, resource):
        return create_attribute_state_tree_for_output(
            resource.id_obj,
            self.context_rule.raw_resource_id,
        )

    async def build_input_state(self, resource):
        raise NotImplemented

    async def build_output_state(self, resource, raw_obj):
        raise NotImplemented


class RepresentationGenerator(_ContextRuleBinder):

    async def generate_representation(self, resource, output_state):
        return {}
