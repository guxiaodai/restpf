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

import inspect

from restpf.utils.constants import (
    HTTPMethodConfig,
    CallbackRegistrarOptions,
)
from restpf.utils.helper_classes import (
    TreeState,
)
from .attributes import (
    Attribute,
    Object,
    Integer,
    String,
    AppearanceConfig,
)


class CallbackRegistrar:

    _AVAILABLE_CONTEXT = dict(map(
        lambda method: (method.value, method),
        HTTPMethodConfig,
    ))

    def __init__(self, callback_info, attr_obj):
        self._callback_info = callback_info
        self._attr_obj = attr_obj

        self.context = None
        self.attr_path = []
        self.options = None
        self.callback = None

    def register(self):
        if self.context is None:
            raise RuntimeError('context not set')

        self._callback_info.register_callback(self)

    def __getattr__(self, name):
        if self.context is None:
            context = self._AVAILABLE_CONTEXT.get(name)

            if context is None:
                next_attr_obj = self._attr_obj.bh_named_child(name)
                if next_attr_obj is None:
                    raise RuntimeError('Invalid attribute: ' + name)

                self.attr_path.append(name)
                self._attr_obj = next_attr_obj
            else:
                self.context = context

            return self
        else:
            raise RuntimeError(
                'Context has been set, cannot get more attribute.',
            )

    def __call__(self, callback=None, **kwargs):
        '''
        Meaningful options:

        - before_all: If is set, this callback(s) will be executed before all
        other callbacks. For a resource, at most one callback can be labeled as
        before_all.
        - run_after: Assign a callback that was registered. Then this callback
        is guaranteed to be executed after that callback.
        - after_all: Similar to before_all, but for the last execution.
        '''

        if callback:
            if callable(callback):
                self.callback = callback
                self.register()
                return callback
            else:
                raise RuntimeError('callback is not callable.')

        else:
            self.options = kwargs

            def _closure(callback):
                self.callback = callback
                self.register()
                return callback

            return _closure


class CallbackInformation:

    def __init__(self, attr_obj):
        '''
        (['next', [..., ]] 'value') => (callback, options)
        '''
        self._registered_callback = TreeState()

    def _locate_registered_callback_tree(self, path):
        return self._registered_callback.touch(path, default={})

    def _set_callback_and_options(self, path, context, callback, options):
        assert isinstance(context, HTTPMethodConfig)

        obj = self._locate_registered_callback_tree(path)
        obj.value[context] = (callback, options)

    def get_registered_callback_and_options(self, path, context):
        assert isinstance(context, HTTPMethodConfig)

        obj = self._locate_registered_callback_tree(path)
        return obj.value.get(context, (None, None))

    def register_callback(self, callback_registrar):
        self._set_callback_and_options(
            callback_registrar.attr_path,
            callback_registrar.context,
            callback_registrar.callback,
            callback_registrar.options,
        )


class SpecialHooksCallbackInformation(CallbackInformation):

    def _set_callback_and_options(self, path, context, callback, options):
        if not path:
            raise RuntimeError('must attach to special_hooks member.')

        options = options or {}
        for item in [
            CallbackRegistrarOptions.BEFORE_ALL,
            CallbackRegistrarOptions.AFTER_ALL,
        ]:
            if path[0] == item.value:
                options[item.value] = True

        super()._set_callback_and_options(path, context, callback, options)


class AttributeCollection:

    COLLECTION_NAME = None

    def __init__(self, *named_element_attrs):
        self._attr_obj = Object(*named_element_attrs)
        if not self._check_attr_obj(self._attr_obj):
            raise RuntimeError('TODO: AttributeCollection.__init__')

        self._callback_info = CallbackInformation(self._attr_obj)

    def _check_attr_obj(self, attr_obj):
        return True

    @property
    def attr_obj(self):
        return self._attr_obj

    @property
    def collection_name(self):
        return self.COLLECTION_NAME

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

    def _check_attr_obj(self, attr_obj):
        if not isinstance(attr_obj, Object):
            # stop condition.
            return isinstance(attr_obj, Attribute)
        else:
            # loop over every pair.
            for node in attr_obj.bh_children:
                if not self._check_attr_obj(node):
                    return False
            return True


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

    def _check_attr_obj(self, attr_obj):
        # TODO
        return True


class SpecialHooks(AttributeCollection):

    COLLECTION_NAME = 'special_hooks'

    def __init__(self):
        super().__init__({
            CallbackRegistrarOptions.BEFORE_ALL.value: Integer,
            CallbackRegistrarOptions.AFTER_ALL.value: Integer,
        })
        self._callback_info = SpecialHooksCallbackInformation(self._attr_obj)


# TODO: refactor class attribute definitions.
class Resource:

    def __init__(self,
                 name,
                 attributes,
                 relationships=None,
                 id_attr=Integer,
                 id_appear_in_post=AppearanceConfig.PROHIBITE):

        self.name = name

        self.id_obj = self._generate_id_obj(
            id_attr, id_appear_in_post,
        )
        self._attributes = attributes
        self._relationships = relationships or Relationships()
        self._special_hooks = SpecialHooks()

    def _generate_id_obj(self, id_attr, id_appear_in_post):
        if id_attr not in (Integer, String) and \
                not isinstance(id_attr, (Integer, String)):
            raise RuntimeError('_generate_id_obj')

        if inspect.isclass(id_attr):
            return id_attr(
                appear_in_get=AppearanceConfig.REQUIRE,
                appear_in_post=id_appear_in_post,
                appear_in_patch=AppearanceConfig.REQUIRE,
                appear_in_put=AppearanceConfig.REQUIRE,
            )
        else:
            return id_attr

    @property
    def attributes_obj(self):
        return self._attributes

    @property
    def relationships_obj(self):
        return self._relationships

    @property
    def special_hooks_obj(self):
        return self._special_hooks

    def __getattribute__(self, name):
        if name in ('attributes', 'relationships', 'special_hooks'):
            # for callback registrater.
            obj = super().__getattribute__(f'_{name}')
            return obj.create_callback_registrar()
        else:
            return super().__getattribute__(name)
