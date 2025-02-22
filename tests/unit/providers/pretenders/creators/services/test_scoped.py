import asyncio
from collections.abc import AsyncIterator, Iterator
from unittest.mock import Mock

import pytest

import diject as di
from diject import ScopedProvider
from diject.utils.exceptions import DIScopeError


class MockClass:
    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"{type(self).__qualname__}({self.value})"


async def create_async_mock_class(value: str) -> AsyncIterator[MockClass]:
    await asyncio.sleep(0.1)
    yield MockClass(value)


class MockContainer(di.Container):
    scoped1 = di.Scoped[MockClass](value="scoped1")
    scoped2 = di.Scoped[MockClass](value="scoped2")
    sequence = [scoped1, scoped1, scoped1, scoped2, scoped2, scoped2]

    async_scoped = di.Scoped[create_async_mock_class](value="async_scoped")
    async_sequence = [async_scoped] * 100


def test_scoped_provider__check_same_instance_within_scope() -> None:
    with di.Provide[MockContainer] as container:
        assert container.scoped1 == container.scoped1
        assert len(set(container.sequence)) == 2


def test_scoped_provider__check_diff_instance() -> None:
    with di.Provide[MockContainer] as container:
        value1 = container.scoped1

    with di.Provide[MockContainer] as container:
        value2 = container.scoped1

    assert value1 != value2


def test_scoped_provider__check_generators() -> None:
    def _some_service() -> Iterator[Mock]:
        mock = Mock()
        mock("start")
        yield mock
        mock("shutdown")

    provider: ScopedProvider[Mock] = di.Scoped[_some_service]()

    with di.Provide[provider] as service:
        service.assert_called_with("start")

    service.assert_called_with("shutdown")


async def test_scoped_provider__check_async_generator() -> None:
    async def _some_service() -> AsyncIterator[Mock]:
        mock = Mock()
        mock("start")
        yield mock
        mock("shutdown")

    provider: ScopedProvider[Mock] = di.Scoped[_some_service]()

    async with di.Provide[provider] as service:
        service.assert_called_with("start")

    service.assert_called_with("shutdown")


async def test_scoped_provider__require_to_be_provided_within_scope() -> None:
    with pytest.raises(DIScopeError):
        di.Provide[MockContainer.scoped1]()


async def test_scoped_provider__async_concurrent_providing() -> None:
    async with di.Provide[MockContainer.async_sequence] as async_sequence:
        assert len(set(async_sequence)) == 1
