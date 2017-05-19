import pytest

from restpf.utils.helper_functions import (
    async_call,
    bind_self_with_options,
    init_named_args,
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


def test_bind_self_with_options():

    class Test:

        def __init__(self, **options):
            bind_self_with_options(
                ['foo', 'bar'],
                self, options,
            )

    t = Test(foo=1, bar=2, whatever=3)
    assert 1 == t.foo
    assert 2 == t.bar


def test_init_named_args():

    class Test:

        @init_named_args('foo', 'bar')
        def __init__(self, a, b=1):
            self.pack = (a, b)

    t = Test(3, foo=1, b=4, bar=2)
    assert 1 == t.foo
    assert 2 == t.bar
    assert (3, 4) == t.pack
