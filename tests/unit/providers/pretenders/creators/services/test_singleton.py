import asyncio
from collections.abc import AsyncIterator, Iterator
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


async def test_singleton_provider__check_async_generator() -> None:
    async def _some_service() -> AsyncIterator[Mock]:
        mock = Mock()
        mock("start")
        yield mock
        mock("shutdown")

    provider = di.Singleton[_some_service]()

    service: Mock = await di.Provide[provider]
    service.assert_called_with("start")

    await di.Provide[provider].areset()
    service.assert_called_with("shutdown")


async def test_singleton_provider__async_concurrent_providing() -> None:
    async def _some_service() -> AsyncIterator[Mock]:
        await asyncio.sleep(0.1)
        yield Mock()

    provider = di.Singleton[_some_service]()

    services: list[Mock] = await asyncio.gather(*(di.Provide[provider] for _ in range(100)))

    assert len(set(services)) == 1
