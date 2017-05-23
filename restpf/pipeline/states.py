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


class CallbackKwargsRegistrar:

    def __init__(self):
        self._registered_kwargs = {}

    def register(self, name, value):
        assert name.isidentifier()
        self._registered_kwargs[name] = value

    def callback_kwargs(self, attr, state):
        ret = {
            # for callback kwargs registration.
            'callback_kwargs': self,

            'attr': attr,
            'state': state,
        }
        ret.update(self._registered_kwargs)
        return ret
