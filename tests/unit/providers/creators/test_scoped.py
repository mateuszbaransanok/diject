from collections.abc import Iterator
from unittest.mock import Mock

import diject as di
from diject import ScopedProvider


class MockClass:
    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"{type(self).__qualname__}({self.value})"


class MockContainer(di.Container):
    scoped_scope = di.Scoped[lambda value: (yield MockClass(value))](value="scoped_scope")
    scoped1 = di.Scoped[MockClass](value="scoped1")
    scoped2 = di.Scoped[MockClass](value="scoped2")
    sequence: list = [scoped1, scoped1, scoped1, scoped2, scoped2, scoped2]


def test_scoped_provider__check_same_instance_within_scope() -> None:
    with di.inject():
        assert di.provide(MockContainer.scoped1) == di.provide(MockContainer.scoped1)
        assert len(set(di.provide(MockContainer.sequence))) == 2


def test_scoped_provider__check_diff_instance() -> None:
    with di.inject():
        value1 = di.provide(MockContainer.scoped1)

    with di.inject():
        value2 = di.provide(MockContainer.scoped1)

    assert value1 != value2


def test_scoped_provider__check_generators() -> None:
    def _some_service() -> Iterator[Mock]:
        mock = Mock()
        mock("start")
        yield mock
        mock("shutdown")

    class Container(di.Container):
        provider: ScopedProvider[Mock] = di.Scoped[_some_service]()

    with di.inject():
        service = di.provide(Container.provider)
        service.assert_called_with("start")

    service.assert_called_with("shutdown")
