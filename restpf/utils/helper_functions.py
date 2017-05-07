import inspect
import collections.abc as abc


def to_iterable(element):
    assert element

    if not isinstance(element, abc.Iterable):
        element = (element,)
    return element


_async_call_func_param_cache = {}


def _async_call_extract_kwargs_subset(func, kwargs):

    if func in _async_call_func_param_cache:
        params_all, params_without_default = _async_call_func_param_cache[func]

    else:
        sig_parameters = inspect.signature(func).parameters

        params_all = set(sig_parameters)
        params_without_default = set(filter(
            lambda k: sig_parameters[k].default is inspect.Parameter.empty,
            params_all,
        ))

        _async_call_func_param_cache[func] = (
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
        kwargs = _async_call_extract_kwargs_subset(func, kwargs)

    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)
