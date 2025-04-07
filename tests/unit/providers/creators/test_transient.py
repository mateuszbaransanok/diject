from collections.abc import Iterator
from unittest.mock import Mock

import diject as di


class MockClass:
    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"{type(self).__qualname__}({self.value})"


class MockContainer(di.Container):
    transient_scope = di.Transient[lambda value: (yield MockClass(value))](value="transient_scope")
    transient1 = di.Transient[MockClass](value="transient1")
    transient2 = di.Transient[MockClass](value="transient2")
    sequence = [transient1, transient1, transient1, transient2, transient2, transient2]


def test_transient_provider__check_diff_instances_without_scope() -> None:
    assert di.provide(MockContainer.transient1) != di.provide(MockContainer.transient1)


def test_transient_provider__check_diff_instances_within_scope() -> None:
    with di.inject():
        assert di.provide(MockContainer.transient1) != di.provide(MockContainer.transient1)
        assert len(set(di.provide(MockContainer.sequence))) == 6


def test_transient_provider__check_generators() -> None:
    def _some_service() -> Iterator[Mock]:
        mock = Mock()
        mock("start")
        yield mock
        mock("shutdown")

    class Container(di.Container):
        provider = di.Transient[_some_service]()

    with di.inject():
        service: Mock = di.provide(Container.provider)
        service.assert_called_with("start")

    service.assert_called_with("shutdown")
