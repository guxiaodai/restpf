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

from .attributes import Object


def extract_tree_structure_from_attr_obj(attr_obj, value_binder=lambda x: x):
    tree = {}
    for name, element_attr in attr_obj.bh_named_children.items():

        if isinstance(element_attr, Object):
            child_value = extract_tree_structure_from_attr_obj(
                element_attr, value_binder,
            )
        else:
            child_value = None

        tree[name] = value_binder(child_value)
    return tree


class CallbackRegistrar:

    def __init__(self, callback_info, attr_obj):
        self._callback_info = callback_info
        self._attr_obj = attr_obj

        self.attr_path = []
        self.options = None
        self.callback = None

    def register(self):
        if not self.attr_path:
            raise RuntimeError('empty path')

        self._callback_info.register_callback(self)

    def __getattr__(self, name):
        next_attr_obj = self._attr_obj.bh_named_child(name)
        if next_attr_obj is None:
            raise RuntimeError('Invalid attribute: ' + name)

        self.attr_path.append(name)
        self._attr_obj = next_attr_obj
        return self

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
        self._registered_callback = extract_tree_structure_from_attr_obj(
            attr_obj,
            lambda x: {
                self._REGISTERED_CALLBACK_KEY_VALUE: None,
                self._REGISTERED_CALLBACK_KEY_NEXT: x,
            },
        )

    def _locate_registered_callback_tree(self, path):
        pre_obj = None
        cur_obj = self._registered_callback

        for name in path:
            pre_obj = cur_obj
            cur_obj = cur_obj[name][self._REGISTERED_CALLBACK_KEY_NEXT]

        return pre_obj

    def _set_callback_and_options(self, path, callback, options):
        obj = self._locate_registered_callback_tree(path)
        last_name = path[-1]

        obj[last_name][self._REGISTERED_CALLBACK_KEY_VALUE] = (
            callback, options,
        )

    def get_registered_callback_and_options(self, path):
        obj = self._locate_registered_callback_tree(path)
        last_name = path[-1]

        return obj[last_name][self._REGISTERED_CALLBACK_KEY_VALUE]

    def register_callback(self, callback_registrar):
        self._set_callback_and_options(
            callback_registrar.attr_path,
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

    def get_registered_callback_and_options(self, path):
        return self._callback_info.get_registered_callback_and_options(path)


class AttributeCollectionState:

    def __init__(self, attr_collection):
        '''
        attr_collection: instance of AttributeCollection
        '''
        self._attr_collection = attr_collection
        self._state_tree = extract_tree_structure_from_attr_obj(
            attr_collection._attr_obj,
        )


class Attributes(AttributeCollection):
    COLLECTION_NAME = 'attributes'

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


class AttributesState(AttributeCollectionState):
    pass


class ResourceDefinition:

    def __init__(self, resource_type, *option_containers):
        self.resource_type = resource_type
