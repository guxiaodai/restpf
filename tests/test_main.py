# remove following code.
from restpf.main import entry_point


def test_entry_point():
    assert 42 == entry_point()
