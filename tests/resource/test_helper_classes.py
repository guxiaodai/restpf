from restpf.utils.helper_classes import (
    ContextOperator,
    TreeState,
    ProxyStateOperator,
)


def test_context_operator():

    class TestCO(ContextOperator):

        OPERATION_MAPPING = {
            'name': {
                'get': 'get_name',
                'post': 'post_name',
            },
        }

    class Ins:

        def __init__(self):
            self.get_name = 1
            self.post_name = 2

    ins = Ins()

    context = TestCO('get')
    assert 1 == context.name(ins)

    context = TestCO('post')
    assert 2 == context.name(ins)


def test_tree_state():
    ts = TreeState()
    v = ts.touch(['a', 'b', 'c'])

    assert v.value is None
    v.value = 42

    assert 42 == ts.touch(['a', 'b', 'c']).value

    ts.touch().value = 'test'
    assert 'test' == ts.touch().value


def test_proxy_state_operator():
    import types

    class TestBase(ProxyStateOperator):

        PROXY_ATTRS = ['a', 'b', 'c']

    state = types.SimpleNamespace()
    t = TestBase()
    t.bind_proxy_state(state)

    t.a = 42
    assert 42 == t.a
    assert 42 == state.a

    class TestDerived(TestBase):

        PROXY_ATTRS = ['d']

    state = types.SimpleNamespace()
    t = TestDerived()
    t.bind_proxy_state(state)
    assert set(['a', 'b', 'c', 'd']) == set(t.PROXY_ATTRS.keys())

    class TestDefault(ProxyStateOperator):

        PROXY_ATTRS = [
            ('foo', 42),
            'bar',
        ]

    state = types.SimpleNamespace()
    t = TestDefault()
    t.bind_proxy_state(state)
    assert 42 == state.foo
