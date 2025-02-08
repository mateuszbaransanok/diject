from unittest.mock import Mock

import diject as di


def test_factory_provider__check_arguments() -> None:
    func = Mock()
    provider = di.Factory[func]("pos", kwarg="kw", dep=[di.Factory[str](1)])  # type: ignore[misc]

    value: Mock = di.Provide[provider]()

    func.assert_called_with("pos", kwarg="kw", dep=["1"])
    assert func() == value


def test_factory_provider__check_different_instances() -> None:
    provider = di.Factory[lambda: Mock()]()

    value1: Mock = di.Provide[provider]()
    value2: Mock = di.Provide[provider]()

    assert value1 != value2
