from typing import Iterator
from unittest.mock import Mock

import diject as di


def test_singleton_provider__check_same_instance() -> None:
    provider = di.Singleton[lambda: Mock()]()

    value1 = di.Provide[provider]()
    value2 = di.Provide[provider]()

    assert value1 == value2


def test_singleton_provider__check_generators() -> None:
    def _some_service() -> Iterator[Mock]:
        mock = Mock()
        mock("start")
        yield mock
        mock("shutdown")

    provider = di.Singleton[_some_service]()

    service: Mock = di.Provide[provider]()
    service.assert_called_with("start")

    di.Provide[provider].reset()
    service.assert_called_with("shutdown")
