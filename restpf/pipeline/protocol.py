# from restpf.attributes import create_ist_from_bh_object
from restpf.utils.helper_functions import async_call


class ContextRule:

    async def pre_validate_ist(self, intermediate_state_tree):
        '''
        return boolean for step (2).
        '''
        raise NotImplemented

    async def select_callbacks(self, attr_collection, intermediate_state_tree):
        '''
        return ordered [(node, callback), ...] for step (3).
        '''
        raise NotImplemented

    async def callback_kwargs(self, node, callback):
        '''
        return a dict.
        TODO: define available keys.
        '''
        raise NotImplemented

    async def build_ist(self, attr_collection, intermediate_state_tree):
        '''
        return an IST for step (4).
        '''
        raise NotImplemented

    async def post_validate_ist(self, intermediate_state_tree):
        '''
        return boolean for step (6).
        '''
        raise NotImplemented


class IntermediateStateTreeBuilder:

    async def build_ist(self, attr_collection):
        '''
        return an IST for step (1).
        '''
        raise NotImplemented


class IntermediateStateTreeCollector:

    async def collect_pre_ist(self, intermediate_state_tree):
        '''
        collect pre-generated IST for step (7).
        '''
        raise NotImplemented

    async def collect_post_ist(self, intermediate_state_tree):
        '''
        collect post-generated IST for step (7).
        '''
        raise NotImplemented


class Pipeline:

    '''
    attr_collection: instance of AttributeCollection

    Core: intermediate state tree (IST).
    IST is identical to the nested structure of attr_collection.

    Pipeline defines:

    1. Setup IST using input_state_setter.

    2. Pre-validate IST using context_rule.

    3. Conditional select and order callbacks to invoke,
    based on the rule provided by context_rule.

    4. Invoke callbacks selected by step (3), with kwargs return by
    callback_kwargs. context_rule.build_ist will be used to construct the IST
    based on return values of callbacks.

    5. Generate a new IST to capture the return value of callbacks.

    6. Post-validate the new IST using context_rule.

    7. pass both ISTs from step (1) and step (5) to output_state_collector.

    Case of GET/OPTIONS:

    input_state_setter is empty, since client send nothing
    in the HTTP body. Data carried in HTTP header and query string will be
    handled by:

    1. context_rule.
    2. passed as input argument to callback, or got injected as context-level
    global instance (like requests in flask library).

    Case of POST/PATCH/PUT:

    The content of HTTP body will be handled by input_state_setter to build the
    IST.
    '''

    def __init__(self,
                 attr_collection,
                 context_rule,
                 input_state_setter,
                 output_state_collector):

        self.attr_collection = attr_collection
        self.context_rule = context_rule
        self.input_state_setter = input_state_setter
        self.output_state_collector = output_state_collector

        self.input_generated_ist = {}
        self.input_generated_ist_is_valid = False

        self.callback_genreated_ist = {}
        self.callback_genreated_ist_is_valid = False

        self.output_generated_ist = {}
        self.output_generated_ist_is_valid = False

        self.selected_node_callback_pairs = []

    async def run(self):
        self.callback_genreated_ist = await async_call(
            self.input_state_setter.build_ist,
            self.attr_collection,
        )

        self.input_generated_ist_is_valid = await async_call(
            self.context_rule.pre_validate_ist,
            self.input_generated_ist,
        )
        if not self.input_generated_ist_is_valid:
            raise RuntimeError('TODO: error processor')

        self.selected_node_callback_pairs = await async_call(
            self.context_rule.select_callbacks,
            self.attr_collection, self.input_generated_ist,
        )
