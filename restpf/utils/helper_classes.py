import collections.abc as abc
import operator
import copy


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
        return self._obj[self._NEXT]

    def _value_get(self):
        assert self._in_gap
        return self._obj[self._VALUE]

    def _value_set(self, value):
        assert self._in_gap
        self._obj[self._VALUE] = value

    value = property(_value_get, _value_set)
