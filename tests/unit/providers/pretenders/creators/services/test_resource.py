import asyncio
from collections.abc import AsyncIterator, Iterator
from unittest.mock import Mock

import pytest

import diject as di
from diject.utils.exceptions import DINotStartedError


def test_resource_provider__raise_error_when_not_started() -> None:
    provider = di.Resource[lambda: Mock()]()

    with pytest.raises(DINotStartedError):
        di.Provide[provider]()


def test_resource_provider__check_same_instance() -> None:
    provider = di.Resource[lambda: Mock()]()
    di.Provide[provider].start()

    value1 = di.Provide[provider]()
    value2 = di.Provide[provider]()

    assert value1 == value2


def test_resource_provider__check_generators() -> None:
    def _some_service() -> Iterator[Mock]:
        mock = Mock()
        mock("start")
        yield mock
        mock("shutdown")

    provider = di.Resource[_some_service]()
    di.Provide[provider].start()

    service: Mock = di.Provide[provider]()
    service.assert_called_with("start")

    di.Provide[provider].reset()
    service.assert_called_with("shutdown")


async def test_resource_provider__check_async_generator() -> None:
    async def _some_service() -> AsyncIterator[Mock]:
        mock = Mock()
        mock("start")
        yield mock
        mock("shutdown")

    provider = di.Resource[_some_service]()
    await di.Provide[provider].astart()

    service: Mock = await di.Provide[provider]
    service.assert_called_with("start")

    await di.Provide[provider].areset()
    service.assert_called_with("shutdown")


async def test_resource_provider__async_concurrent_providing() -> None:
    async def _some_service() -> AsyncIterator[Mock]:
        await asyncio.sleep(0.1)
        yield Mock()

    provider = di.Resource[_some_service]()
    await di.Provide[provider].astart()

    services: list[Mock] = await asyncio.gather(*(di.Provide[provider] for _ in range(100)))

    assert len(set(services)) == 1
