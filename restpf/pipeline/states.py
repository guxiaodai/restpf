from restpf.utils.helper_classes import (
    StateCreator,
    ProxyStateOperator,
)
from restpf.utils.helper_functions import (
    namedtuple_with_default,
)


_COLLECTION_NAMES = tuple(map(
    lambda k: (k, {}),
    ('attributes', 'relationships', 'resource_id'),
))

ResourceState = namedtuple_with_default(
    'ResourceState',
    *_COLLECTION_NAMES,
)
RawOutputStateContainer = namedtuple_with_default(
    'RawOutputStateContainer',
    *_COLLECTION_NAMES,
)


class CallbackKwargsProcessor:

    def __init__(self):
        self._controllers = []

    def add_controller(self, controller):
        self._controllers.append(controller)

    def callback_kwargs(self, attr, state):
        # from arguments.
        ret = {
            'attr': attr,
            'state': state,
        }
        # from controllers.
        for controller in self._controllers:
            controller.update(ret)

        return ret


class CallbackKwargsRegistrar:

    def __init__(self):
        self._registered_kwargs = {}

    def register(self, name, value):
        assert name.isidentifier()
        self._registered_kwargs[name] = value

    def update(self, ret):
        # bind registrar.
        ret['callback_kwargs'] = self
        # bind registered variables.
        ret.update(self._registered_kwargs)


class CallbackKwargsStateVariableMapper(ProxyStateOperator):

    ATTR2KWARG = {}

    @classmethod
    def _get_proxy_attrs(cls):
        return cls.ATTR2KWARG.keys()

    def update(self, ret):
        for name in self.PROXY_ATTRS:
            kwarg_name = self.ATTR2KWARG[name]
            ret[kwarg_name] = getattr(self, name)


class DefaultPipelineState(metaclass=StateCreator):

    ATTRS = []
