from collections.abc import AsyncIterator, Iterator
from concurrent.futures.thread import ThreadPoolExecutor
from random import random
from time import sleep
from unittest.mock import Mock

import pytest

import diject as di
from diject.utils.exceptions import DIAsyncError


def test_thread_provider__check_same_instance() -> None:
    provider = di.Thread[lambda: Mock()]()

    value1 = di.Provide[provider]()
    value2 = di.Provide[provider]()

    assert value1 == value2


def test_thread_provider__check_generators() -> None:
    def _some_service() -> Iterator[Mock]:
        mock = Mock()
        mock("start")
        yield mock
        mock("shutdown")

    provider = di.Thread[_some_service]()

    service: Mock = di.Provide[provider]()
    service.assert_called_with("start")

    di.Provide[provider].reset()
    service.assert_called_with("shutdown")


async def test_thread_provider__check_async_generator__raise_error() -> None:
    async def _some_service() -> AsyncIterator[None]:
        yield

    provider = di.Thread[_some_service]()

    with pytest.raises(DIAsyncError):
        await di.Provide[provider]


def test_thread_provider__concurrent_providing() -> None:
    def _some_service() -> Iterator[Mock]:
        mock = Mock()
        sleep(random() * 0.1)
        yield mock
        mock.shutdown = True

    provider = di.Thread[_some_service]()

    with ThreadPoolExecutor(max_workers=3) as pool:
        output_mocks = set(pool.map(lambda p: di.Provide[p](), [provider] * 100))

    assert len(output_mocks) == 3

    for output_mock in output_mocks:
        assert getattr(output_mock, "shutdown", False)
