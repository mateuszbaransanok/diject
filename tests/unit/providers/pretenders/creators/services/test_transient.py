import asyncio
import time
from collections.abc import AsyncIterator, Iterator
from unittest.mock import Mock

import pytest

import diject as di
from diject import TransientProvider
from diject.utils.exceptions import DIScopeError


class MockClass:
    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"{type(self).__qualname__}({self.value})"


async def create_async_mock_class(value: str) -> AsyncIterator[MockClass]:
    await asyncio.sleep(0.01)
    yield MockClass(value)


def create_sync_mock_class(value: str) -> Iterator[MockClass]:
    time.sleep(0.01)
    yield MockClass(value)


class MockContainer(di.Container):
    transient1 = di.Transient[MockClass](value="transient1")
    transient2 = di.Transient[MockClass](value="transient2")
    sequence = [transient1, transient1, transient1, transient2, transient2, transient2]

    async_transient = di.Transient[create_async_mock_class](value="async_transient")
    async_sequence = [async_transient] * 10

    sync_transient = di.Transient[create_sync_mock_class](value="sync_transient")
    sync_sequence = [sync_transient] * 10


def test_transient_provider__check_diff_instances_within_scope() -> None:
    with di.Provide[MockContainer] as container:
        assert container.transient1 != container.transient1
        assert len(set(container.sequence)) == 6


def test_transient_provider__check_generators() -> None:
    def _some_service() -> Iterator[Mock]:
        mock = Mock()
        mock("start")
        yield mock
        mock("shutdown")

    provider: TransientProvider[Mock] = di.Transient[_some_service]()

    with di.Provide[provider] as service:
        service.assert_called_with("start")

    service.assert_called_with("shutdown")


async def test_transient_provider__check_async_generator() -> None:
    async def _some_service() -> AsyncIterator[Mock]:
        mock = Mock()
        mock("start")
        yield mock
        mock("shutdown")

    provider: TransientProvider[Mock] = di.Transient[_some_service]()

    async with di.Provide[provider] as service:
        service.assert_called_with("start")

    service.assert_called_with("shutdown")


async def test_transient_provider__require_to_be_provided_within_scope() -> None:
    with pytest.raises(DIScopeError):
        di.Provide[MockContainer.transient1]()


async def test_transient_provider__fast_async_concurrent_providing() -> None:
    start_time = time.perf_counter()

    async with di.Provide[MockContainer.async_sequence] as async_sequence:
        assert len(set(async_sequence)) == 10

    duration = time.perf_counter() - start_time
    assert 0.01 <= duration < 0.013


def test_transient_provider__slow_sync_sequential_providing() -> None:
    start_time = time.perf_counter()

    with di.Provide[MockContainer.sync_sequence] as sync_sequence:
        assert len(set(sync_sequence)) == 10

    duration = time.perf_counter() - start_time
    assert 0.1 <= duration < 0.13
