import inspect
import collections.abc as abc
from functools import wraps


def to_iterable(element):
    assert element

    if not isinstance(element, abc.Iterable):
        element = (element,)
    return element


_extract_kwargs_subset_cache = {}


def _extract_kwargs_subset(func, kwargs):

    if func in _extract_kwargs_subset_cache:
        params_all, params_without_default = _extract_kwargs_subset_cache[func]

    else:
        sig_parameters = inspect.signature(func).parameters

        params_all = set(sig_parameters)
        params_without_default = set(filter(
            lambda k: sig_parameters[k].default is inspect.Parameter.empty,
            params_all,
        ))

        _extract_kwargs_subset_cache[func] = (
            params_all, params_without_default,
        )

    kwargs_keys = set(kwargs)

    if not params_without_default <= kwargs_keys:
        raise RuntimeError('Missing keys')

    intersection = params_all & kwargs_keys
    kwargs_subset = {key: kwargs[key] for key in intersection}

    return kwargs_subset


async def async_call(func, *args, **kwargs):
    if not args:
        # turn on kwargs filtering.
        kwargs = _extract_kwargs_subset(func, kwargs)

    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)


def bind_self_with_options(names, self, options):
    for name in names:
        setattr(self, name, options.get(name))


def init_named_args(*names):

    def _decorator(init):

        @wraps(init)
        def _wrapper(self, *args, **kwargs):
            bind_self_with_options(names, self, kwargs)
            # remove from kwargs.
            for name in names:
                kwargs.pop(name, None)
            # pass to original init.
            init(self, *args, **kwargs)

        return _wrapper

    return _decorator
