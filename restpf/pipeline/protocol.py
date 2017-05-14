from collections import deque

from restpf.utils.helper_classes import (
    TreeState,
)
from restpf.utils.helper_functions import async_call


class ContextRule:

    HTTPMethod = None

    async def validate_input_state(self, state):
        return None

    async def validate_output_state(self, state):
        return None

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
                    (callback, attr, state),
                )

            for name, child_attr in attr.bh_named_children.items():
                child_state = getattr(state, name) if state else None
                queue.append(
                    (child_attr, child_state),
                )

        return ret

    # TODO: design bugfix. add mapping from attr collection to state.
    async def select_callbacks(self, resource, state):
        '''
        return ordered [(callback, attr, state), ...].
        '''

        ret = []
        # attributes.
        ret.extend(
            self._select_callbacks(
                resource.attributes_obj.get_registered_callback_and_options,
                resource.attributes_obj.attr_obj,
                state,
            ),
        )
        # TODO: relationships
        return ret

    async def callback_kwargs(self, attr, state):
        '''
        TODO
        Available keys:

        - resource_id
        - ...
        '''
        return {}

    async def load_data_from_state_builder(self, state_builder):
        pass


class StateTreeBuilder:

    async def build_input_state(self, resource):
        raise NotImplemented

    async def build_output_state(self, resource, raw_obj):
        raise NotImplemented


def _merge_output_of_callbacks(output_of_callbacks):

    def helper(ret, child_value, tree_state):
        if not tree_state:
            # leaf node.
            return child_value if child_value else ret

        ret = ret if ret else child_value
        if not isinstance(ret, dict):
            # none leaf node with wrong ret type.
            ret = {}

        for name, child in tree_state.children:
            ret[name] = helper(
                ret.get(name), child.value, child.next,
            )
        return ret

    # deal with root.
    root_gap = output_of_callbacks.root_gap
    ret = root_gap.value if root_gap else {}

    helper(ret, None, output_of_callbacks)
    return ret


class PipelineBase:

    '''
    Pipeline based on following instances:

    - `resource`
    - `context_rule`
    - `state_builder`
    - `output_state_creator`

    Steps of pipeline:

    1. create `intput_state`.
    2. validate `intput_state`.
    3. generate callback list.
    4. call callbacks and collect strucutred return values.
    5. create `output_state`.
    6. validate `output_state`.
    '''

    def __init__(self,
                 resource,
                 context_rule,
                 state_builder):

        self.resource = resource
        self.context_rule = context_rule
        self.state_builder = state_builder

    async def run(self):
        await async_call(
            self.context_rule.load_data_from_state_builder,
            self.state_builder,
        )

        intput_state = await async_call(
            self.state_builder.build_input_state,
            self.resource,
        )
        intput_state_is_valid = await async_call(
            self.context_rule.validate_input_state,
            intput_state,
        )
        if not intput_state_is_valid:
            raise RuntimeError('TODO: input state not valid')

        callback_and_options = list(await async_call(
            self.context_rule.select_callbacks,
            self.resource, intput_state,
        ))
        output_of_callbacks = TreeState()

        for callback, attr, state in callback_and_options:
            kwargs = await async_call(
                self.context_rule.callback_kwargs,
                attr, state,
            )
            ret = await async_call(
                callback,
                **kwargs,
            )
            output_of_callbacks.touch(attr.bh_path).value = ret

        merged_output_of_callbacks = _merge_output_of_callbacks(
            output_of_callbacks,
        )

        output_state = self.state_builder.build_output_state(
            self.resource, merged_output_of_callbacks,
        )
        output_state_is_valid = self.context_rule.validate_output_state(
            output_state,
        )
        if not output_state_is_valid:
            raise RuntimeError('TODO: output state not valid')

        self.output_state = output_state


class SingleResourcePipeline(PipelineBase):
    pass


class MultipleResourcePipeline(PipelineBase):
    pass


# TODO: relative resource pipeline.
