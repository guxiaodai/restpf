import collections.abc as abc


def to_iterable(element):
    assert element

    if not isinstance(element, abc.Iterable):
        element = (element,)
    return element
