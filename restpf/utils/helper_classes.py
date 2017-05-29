import collections.abc as abc
import operator
import copy

from .helper_functions import method_named_args


class ContextOperator:

    '''
    {
        '<op proxy>': {
            '<context 1>': '<op name 1>',
            '<context 2>': '<op name 2>',
            ...
        },
        ...
    }
    '''

    OPERATION_MAPPING = {}

    def __init__(self, context):
        self._co_operation2proxy = {}
        assert isinstance(self.OPERATION_MAPPING, abc.Mapping)

        for op_name, context2proxy in self.OPERATION_MAPPING.items():
            assert isinstance(context2proxy, abc.Mapping)
            op_proxy = context2proxy.get(context)
            if op_proxy:
                assert isinstance(op_proxy, str) and op_proxy.isidentifier()
                self._co_operation2proxy[op_name] = op_proxy

    def __getattribute__(self, name):
        op_proxy = super().__getattribute__('_co_operation2proxy').get(name)
        if op_proxy is None:
            return super().__getattribute__(name)
        else:
            return operator.attrgetter(op_proxy)


class LinkedPath:

    def __init__(self):
        self.empty = True

    def set_name_and_parent(self, name, parent):
        self.empty = False
        self.name = name
        self.parent = parent

    def __iter__(self):
        node = self
        path = []

        while not node.empty:
            path.append(node.name)
            node = node.parent

        return reversed(path)


class TreeState:

    _NEXT = '__next'
    _VALUE = '__value'
    _TOP_LEVEL = '__top_level'

    def __init__(self, obj=None, in_gap=False):
        self._obj = obj if obj else dict()
        self._in_gap = in_gap

    def touch(self, path=None, default=None):
        path = list([] if path is None else path)
        if not path:
            path = [self._TOP_LEVEL]

        obj = self._obj
        last_gap = None

        for name in path:
            if name not in obj:
                obj[name] = {
                    self._VALUE: copy.copy(default),
                    self._NEXT: {},
                }
            last_gap = obj[name]
            obj = obj[name][self._NEXT]

        return TreeState(obj=last_gap, in_gap=True)

    @property
    def next(self):
        assert self._in_gap

        next_obj = self._obj[self._NEXT]
        if next_obj:
            return TreeState(obj=next_obj, in_gap=False)
        else:
            return None

    @property
    def root_gap(self):
        assert not self._in_gap

        gap_obj = self._obj.get(self._TOP_LEVEL)
        if gap_obj:
            return TreeState(
                obj=gap_obj,
                in_gap=True,
            )
        else:
            return None

    @property
    def children(self):
        assert not self._in_gap

        ret = []
        for key, value in self._obj.items():
            if key == self._TOP_LEVEL:
                continue
            ret.append(
                (key, TreeState(obj=value, in_gap=True)),
            )
        return ret

    def _value_get(self):
        assert self._in_gap
        return self._obj[self._VALUE]

    def _value_set(self, value):
        assert self._in_gap
        self._obj[self._VALUE] = value

    value = property(_value_get, _value_set)


class ProxyStateOperator:

    PROXY_ATTRS = []

    def _cache_hierarchy_proxy_attrs(self):
        ret = {}

        for _cls in type(self).__mro__:
            PROXY_ATTRS = getattr(_cls, 'PROXY_ATTRS', None)
            if PROXY_ATTRS is None:
                continue

            for attr in PROXY_ATTRS:
                if isinstance(attr, str):
                    name = attr
                    default = None
                elif isinstance(attr, abc.Sequence) and len(attr) == 2:
                    name, default = attr
                else:
                    raise RuntimeError("wrong format of PROXY_ATTRS.")

                ret[name] = default

        return ret

    def bind_proxy_state(self, state):
        # cache PROXY_ATTRS.
        self.PROXY_ATTRS = self._cache_hierarchy_proxy_attrs()
        # bind state.
        self._pso_proxy_state = state
        # __getattribute__ works now.
        # bind default value.
        for name, default in self.PROXY_ATTRS.items():
            if getattr(self, name) is None:
                setattr(self, name, default)

    def __getattribute__(self, name):
        use_default = False
        try:
            PROXY_ATTRS = object.__getattribute__(
                self, 'PROXY_ATTRS',
            )
            _pso_proxy_state = object.__getattribute__(
                self, '_pso_proxy_state',
            )
        except AttributeError:
            use_default = True

        if use_default or name not in PROXY_ATTRS:
            return object.__getattribute__(self, name)
        else:
            return getattr(_pso_proxy_state, name, None)

    def __setattr__(self, name, value):
        if name in self.PROXY_ATTRS:
            setattr(self._pso_proxy_state, name, value)
        else:
            object.__setattr__(self, name, value)


class StateCreator(type):

    # return a simple namespace with parameters of __init__ defined in ATTRS.
    def __new__(cls, name, bases, namespace):
        resultcls = type.__new__(cls, name, (), namespace)

        @method_named_args(*namespace.get('ATTRS'))
        def __init__(self):
            pass

        resultcls.__init__ = __init__
        return resultcls
