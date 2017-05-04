import pytest

from restpf.utils.helper_functions import (
    async_call,
)


@pytest.mark.asyncio
async def test_async_call():

    def not_async(a, b):
        return a + b

    async def is_async(a, b):
        return a + b

    assert 3 == await async_call(not_async, 1, b=2)
    assert 3 == await async_call(is_async, 1, 2)


@pytest.mark.asyncio
async def test_async_call_kwargs_subset_filtering():
    def func1(a, b, c=0):
        return a + b + c

    assert 6 == await async_call(func1, **{
        'a': 1,
        'b': 2,
        'c': 3,
    })

    assert 3 == await async_call(func1, **{
        'a': 1,
        'b': 2,
    })

    assert 3 == await async_call(func1, **{
        'a': 1,
        'b': 2,
        'e': 3,
    })

    with pytest.raises(RuntimeError):
        await async_call(func1, **{'a': 1})
