import collections.abc as abc
import operator


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
