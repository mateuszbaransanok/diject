import re

from diject import __version__


def test_version() -> None:
    assert re.match(r"\d+\.\d+\.\d+", __version__)
