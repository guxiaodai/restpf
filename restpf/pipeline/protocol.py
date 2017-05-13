from collections import deque

# from restpf.attributes import create_ist_from_bh_object
# from restpf.utils.helper_functions import async_call


class ContextRule:

    HTTPMethod = None

    async def validate_input_state(self, state):
        raise NotImplemented

    async def validate_output_state(self, state):
        raise NotImplemented

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
                    (callback, state),
                )

            for name, child_attr in attr.bh_named_children.items():
                child_state = getattr(state, name) if state else None
                queue.append(
                    (child_attr, child_state),
                )

        return ret

    async def select_callbacks(self, resource, state):
        '''
        return ordered [(callback, state), ...].
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

    async def callback_kwargs(self, state):
        '''
        TODO
        Available keys:

        - resource_id
        - ...
        '''
        raise NotImplemented


class StateTreeBuilder:

    async def build_input_state(self, resource):
        raise NotImplemented

    async def build_output_state(self, resource, raw_obj):
        raise NotImplemented


class Pipeline:

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
        pass
