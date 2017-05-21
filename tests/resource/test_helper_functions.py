import pytest

from restpf.utils.helper_functions import (
    async_call,
    bind_self_with_options,
    method_named_args,
    parallel_groups_of_callbacks,
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


def test_method_named_args():

    class Test:

        @method_named_args('foo', 'bar')
        def __init__(self, a, b=1):
            self.pack = (a, b)

    t = Test(3, foo=1, b=4, bar=2)
    assert 1 == t.foo
    assert 2 == t.bar
    assert (3, 4) == t.pack


def testparallel_groups_of_callbacks():

    def a():
        pass

    async def b():
        pass

    def c():
        pass

    def d():
        pass

    # with root.
    groups = parallel_groups_of_callbacks([
        (a, {'before_all': True}),
        (b, {}),
        (c, {}),
        (d, {}),
    ])
    assert 2 == len(groups)
    assert set([a]) == set(groups[0])
    assert set([b, c, d]) == set(groups[1])

    # without root.
    groups = parallel_groups_of_callbacks([
        (a, {}),
        (b, {}),
        (c, {}),
        (d, {}),
    ])
    assert 1 == len(groups)
    assert set([a, b, c, d]) == set(groups[0])

    # chaining.
    groups = parallel_groups_of_callbacks([
        (a, {}),
        (b, {'run_after': a}),
        (c, {'run_after': b}),
        (d, {}),
    ])
    assert 3 == len(groups)
    assert set([a, d]) == set(groups[0])
    assert set([b]) == set(groups[1])
    assert set([c]) == set(groups[2])

    # multiple RUN_AFTER.
    groups = parallel_groups_of_callbacks([
        (a, {}),
        (b, {}),
        (c, {'run_after': [a, b]}),
        (d, {}),
    ])
    assert 2 == len(groups)
    assert set([a, b, d]) == set(groups[0])
    assert set([c]) == set(groups[1])

    # indirect dependency.
    groups = parallel_groups_of_callbacks([
        (a, {}),
        (b, {}),
        (c, {'run_after': b}),
        (d, {'run_after': [a, b, c]}),
    ])
    assert 3 == len(groups)
    assert set([a, b]) == set(groups[0])
    assert set([c]) == set(groups[1])
    assert set([d]) == set(groups[2])

    # after_all.
    groups = parallel_groups_of_callbacks([
        (a, {}),
        (b, {}),
        (c, {}),
        (d, {'after_all': True}),
    ])
    assert 2 == len(groups)
    assert set([a, b, c]) == set(groups[0])
    assert set([d]) == set(groups[1])
