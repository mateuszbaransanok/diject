from unittest.mock import Mock

import pytest

import diject as di
from diject.exceptions import DIObjectError


def test_object() -> None:
    mock = Mock()
    obj_provider: Mock = di.Object(mock)

    actual: Mock = di.provide(obj_provider)

    assert actual is mock


def test_object__default_empty__raise_error() -> None:
    obj_provider: Mock = di.Object()

    with pytest.raises(DIObjectError):
        di.provide(obj_provider)


def test_object__set_empty_value() -> None:
    obj_provider = di.Object[int]()
    obj_provider.__object__ = 1  # type: ignore[attr-defined]

    actual = di.provide(obj_provider)

    assert actual == 1


def test_object__override_value() -> None:
    obj_provider = di.Object(0)
    obj_provider.__object__ = 1  # type: ignore[attr-defined]

    actual = di.provide(obj_provider)

    assert actual == 1


def test_object__override_and_reset() -> None:
    obj_provider = di.Object(0)
    obj_provider.__object__ = 1  # type: ignore[attr-defined]
    di.shutdown(obj_provider)

    actual = di.provide(obj_provider)

    assert actual == 0
