from restpf.attributes import create_ist_from_bh_object


class ContextRule:
    pass


class IntermediateStateTreeBuilder:
    pass


class IntermediateStateTreeCollector:
    pass


class Pipeline:

    '''
    attr_collection: instance of AttributeCollection

    Core: intermediate state tree (IST).
    IST is identical to the nested structure of attr_collection.

    There's a pipline for resource operation:

    1. initialize empty IST based on attr_collection.
    2. setup IST using input_state_setter.
    3. pre-validate IST using context_rule.
    4. conditional select and order callbacks to invoke,
    based on the rule provided by context_rule.
    5. invoke callbacks selected by step (4).
    6. generate a new IST to capture the return value of callbacks.
    7. post-validate the new IST using context_rule.
    8. pass both ISTs from step (2) and step (6) to output_state_collector.

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

        self._attr_collection = attr_collection
        self._intermediate_state_tree = create_ist_from_bh_object(
            attr_collection._attr_obj,
        )
