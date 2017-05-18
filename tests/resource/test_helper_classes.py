from restpf.utils.helper_classes import (
    ContextOperator,
    TreeState,
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