import asyncio
from functools import wraps
from collections import defaultdict

from restpf.utils.helper_classes import (
    ProxyStateOperator,
)
from restpf.utils.helper_functions import (
    method_named_args,
    async_call,
    parallel_groups_of_callbacks,
)
from restpf.utils.helper_classes import TreeState

from .states import (
    _INPUT_STATE_NAMES,
    _INTERNAL_STATE_NAMES,
    _OUTPUT_STATE_NAMES,
)

from .states import DefaultPipelineState               # noqa
from .states import CallbackKwargsStateVariableMapper  # noqa
from .states import CallbackKwargsVariableCollector    # noqa

from .operations import ContextRule                    # noqa
from .operations import StateTreeBuilder               # noqa
from .operations import RepresentationGenerator        # noqa


def _meta_build(method):
    METHOD_PREFIX = 'build_'

    attr_name = method.__name__[len(METHOD_PREFIX):]
    cls_name = attr_name.upper() + '_CLS'

    @wraps(method)
    def _wrapper(self, *args, **kwargs):
        setattr(
            self, attr_name,
            getattr(self, cls_name)(*args, **kwargs),
        )
        # post operations.
        method(self)

    return _wrapper


class PipelineRunner:

    CALLBACK_KWARGS_CONTROLLER_CLSES = []
    CONTEXT_RULE_CLS = None

    STATE_TREE_BUILDER_CLS = None
    REPRESENTATION_GENERATOR_CLS = None

    PIPELINE_CLS = None
    PIPELINE_STATE_CLS = DefaultPipelineState

    @_meta_build
    def build_pipeline_state(self):
        pass

    @_meta_build
    def build_context_rule(self):
        # attach callback controller.
        for controller_cls in self.CALLBACK_KWARGS_CONTROLLER_CLSES:
            # init and bind to state.
            controller = controller_cls()
            controller.bind_proxy_state(self.pipeline_state)
            # attach.
            self.context_rule.attach_callback_kwargs_controller(controller)

    @_meta_build
    def build_state_tree_builder(self):
        pass

    @_meta_build
    def build_representation_generator(self):
        pass

    def set_resource(self, resource):
        self.resource = resource

    async def run_pipeline(self):
        pipeline = self.PIPELINE_CLS(
            pipeline_state=self.pipeline_state,
            resource=self.resource,
            context_rule=self.context_rule,
            state_builder=self.state_tree_builder,
            rep_generator=self.representation_generator,
        )
        await pipeline.run()
        return pipeline


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

    return helper(ret, None, output_of_callbacks)


class PipelineBase(ProxyStateOperator):

    '''
    Pipeline based on following instances:

    - `resource`
    - `context_rule`
    - `state_builder`
    - `output_state_creator`

    Steps of pipeline:

    1. create `input_state`.
    2. validate `input_state`.
    3. generate callback list.
    4. call callbacks and collect strucutred return values.
    5. create `output_state`.
    6. validate `output_state`.
    '''

    PROXY_ATTRS = [
        *_INPUT_STATE_NAMES,
        *_INTERNAL_STATE_NAMES,
        *_OUTPUT_STATE_NAMES,

        'merged_output_of_callbacks',
        'output_state',
        'representation',
    ]

    @method_named_args(
        'pipeline_state',
        'resource',
        'context_rule',
        'state_builder',
        'rep_generator',
    )
    def __init__(self):
        self.bind_proxy_state(self.pipeline_state)

        self.context_rule.bind_proxy_state(self.pipeline_state)
        self.state_builder.bind_proxy_state(self.pipeline_state)
        self.rep_generator.bind_proxy_state(self.pipeline_state)

    async def _build_input_state(self):
        await async_call(
            self.state_builder.build_input_state,
            self.resource,
        )

        input_state_is_valid = await async_call(
            self.context_rule.validate_input_state,
        )
        if not input_state_is_valid:
            raise RuntimeError('TODO: input state not valid')

    async def _invoke_callbacks(self):
        COLLECTION_NAME_KEY = '_collection_name'

        name2selected = await async_call(
            self.context_rule.select_callbacks,
            self.resource,
        )

        callback2options = {}
        parallel_groups_of_callbacks_input = []

        for collection_name, callback_and_options in name2selected.items():
            for callback, options in callback_and_options:
                # patch options.
                options[COLLECTION_NAME_KEY] = collection_name
                # keep mapping.
                callback2options[callback] = options

                parallel_groups_of_callbacks_input.append(
                    (callback, options.get('options') or {}),
                )

        name2raw_obj = defaultdict(TreeState)

        for callback_group in parallel_groups_of_callbacks(
            parallel_groups_of_callbacks_input,
        ):
            names = []
            paths = []
            async_callbacks = []

            for callback in callback_group:
                options = callback2options[callback]

                kwargs = await async_call(
                    self.context_rule.callback_kwargs,
                    **options,
                )

                names.append(options.get(COLLECTION_NAME_KEY))
                paths.append(options.get('attr').bh_path)

                async_callbacks.append(async_call(callback, **kwargs))

            for name, path, ret in zip(
                names, paths, await asyncio.gather(*async_callbacks),
            ):
                if name == 'special_hooks':
                    # do not capture the return of special_hooks.
                    continue

                name2raw_obj[name].touch(path).value = ret

        # TODO: too dirty, fix it.
        for name, tree_state in name2raw_obj.items():
            setattr(
                self, f'internal_{name}',
                _merge_output_of_callbacks(tree_state),
            )

    async def _build_output_state(self):
        await async_call(
            self.state_builder.build_output_state,
            self.resource,
        )
        output_state_is_valid = await async_call(
            self.context_rule.validate_output_state,
        )
        if not output_state_is_valid:
            raise RuntimeError('TODO: output state not valid')

    async def _generate_representation(self):
        self.representation = None
        if self.rep_generator:
            self.representation = await async_call(
                self.rep_generator.generate_representation,
                self.resource,
            )

    async def run(self):
        await self._build_input_state()
        await self._invoke_callbacks()
        await self._build_output_state()
        await self._generate_representation()


class SingleResourcePipeline(PipelineBase):
    pass


class MultipleResourcePipeline(PipelineBase):
    pass


# TODO: relative resource pipeline.
