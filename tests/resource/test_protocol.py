import pytest

from restpf.pipeline.protocol import call_function_with_kwargs


def test_call_func():
    def func1(a, b, c=0):
        return a + b + c

    assert 6 == call_function_with_kwargs(func1, {
        'a': 1,
        'b': 2,
        'c': 3,
    })

    assert 3 == call_function_with_kwargs(func1, {
        'a': 1,
        'b': 2,
    })

    assert 3 == call_function_with_kwargs(func1, {
        'a': 1,
        'b': 2,
        'e': 3,
    })

    with pytest.raises(RuntimeError):
        call_function_with_kwargs(func1, {'a': 1})
