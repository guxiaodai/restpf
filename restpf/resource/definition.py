"""
Defines classes for building resource structure.

Example:

foo = Resource(
    'foo',
    Attributes(
        Boolean('normal_user'),
        String('username'),
        ...
    ),
    Relationships(
        ...
    ),
})

foo.noraml_user
foo.username
"""

from restpf.utils.constants import ALL_HTTP_METHODS
from .attributes import Object, create_ist_from_bh_object


class CallbackRegistrar:

    _AVAILABLE_CONTEXT = set(ALL_HTTP_METHODS)

    def __init__(self, callback_info, attr_obj):
        self._callback_info = callback_info
        self._attr_obj = attr_obj

        self.context = None
        self.attr_path = []
        self.options = None
        self.callback = None

    def register(self):
        if not self.attr_path:
            raise RuntimeError('empty path')
        if self.context is None:
            raise RuntimeError('context not set')

        self._callback_info.register_callback(self)

    def __getattr__(self, name):
        if self.context is None:

            if name not in self._AVAILABLE_CONTEXT:
                next_attr_obj = self._attr_obj.bh_named_child(name)
                if next_attr_obj is None:
                    raise RuntimeError('Invalid attribute: ' + name)

                self.attr_path.append(name)
                self._attr_obj = next_attr_obj
            else:
                self.context = name

            return self
        else:
            raise RuntimeError(
                'Context has been set, cannot get more attribute.',
            )

    def __call__(self, callback=None, **kwargs):
        if callback:
            if callable(callback):
                self.callback = callback
                self.register()
            else:
                raise RuntimeError('callback is not callable.')
        else:
            self.options = kwargs

            def _closure(callback):
                self.callback = callback
                self.register()

            return _closure


class CallbackInformation:

    _REGISTERED_CALLBACK_KEY_VALUE = 'value'
    _REGISTERED_CALLBACK_KEY_NEXT = 'next'

    def __init__(self, attr_obj):
        # [attr path] => (callback, options)
        self._registered_callback = create_ist_from_bh_object(
            attr_obj,
            lambda x: {
                self._REGISTERED_CALLBACK_KEY_VALUE: {},
                self._REGISTERED_CALLBACK_KEY_NEXT: x,
            },
        )

    def _locate_registered_callback_tree(self, path):
        pre_obj = None
        cur_obj = self._registered_callback
        for name in path:
            pre_obj = cur_obj
            cur_obj = cur_obj[name][self._REGISTERED_CALLBACK_KEY_NEXT]

        return pre_obj[path[-1]][self._REGISTERED_CALLBACK_KEY_VALUE]

    def _set_callback_and_options(self, path, context, callback, options):
        obj = self._locate_registered_callback_tree(path)
        obj[context] = (callback, options)

    def get_registered_callback_and_options(self, path, context):
        obj = self._locate_registered_callback_tree(path)
        return obj.get(context)

    def register_callback(self, callback_registrar):
        self._set_callback_and_options(
            callback_registrar.attr_path,
            callback_registrar.context,
            callback_registrar.callback,
            callback_registrar.options,
        )


class AttributeCollection:

    COLLECTION_NAME = None

    def __init__(self, *attrs):
        self._attr_obj = Object(self.COLLECTION_NAME, *attrs)
        self._callback_info = CallbackInformation(self._attr_obj)

    def create_callback_registrar(self):
        return CallbackRegistrar(self._callback_info, self._attr_obj)

    def get_registered_callback_and_options(self, path, context):
        return self._callback_info.get_registered_callback_and_options(
            path, context,
        )


class Attributes(AttributeCollection):

    """
    Attributes is a special case of Object.

    Usage:

    Resource(
        ...
        Attributes(
            String('name'),
            Integer('age'),
            ...
        ),
        ...
    )
    """

    COLLECTION_NAME = 'attributes'


class Relationships(AttributeCollection):

    """
    Attributes is a special case of Object.

    Usage:

    Resource(
        ...
        Relationships(
            OneToOneRelationship('foo'),
            OneToMoreRelationship('bar'),
            ...
        ),
        ...
    )
    """

    COLLECTION_NAME = 'relationships'


class ResourceDefinition:

    """
    ResourceDefinition do not make any assumption on the attribute structure.
    It accepts any number of Attribute and AttributeCollection. User of this
    class should explicity mark the attribute like `type`, `id`.
    """

    def __init__(self, resource_type, *option_containers):
        self.resource_type = resource_type


class Resource(ResourceDefinition):

    """
    Special kinds of ResourceDefinition, with fixed attribute structure.
    """
