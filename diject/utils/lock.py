import asyncio
import threading
from types import TracebackType


class Lock:
    def __init__(self) -> None:
        self.__asyncio_lock = asyncio.Lock()
        self.__thread_lock = threading.Lock()

    def __enter__(self) -> None:
        self.acquire()

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc_val: Exception | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.release()

    async def __aenter__(self) -> None:
        await self.aacquire()

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc_val: Exception | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.arelease()

    def acquire(self) -> None:
        self.__thread_lock.acquire()

    def release(self) -> None:
        self.__thread_lock.release()

    async def aacquire(self) -> None:
        await self.__asyncio_lock.acquire()
        self.__thread_lock.acquire()

    async def arelease(self) -> None:
        self.__asyncio_lock.release()
        self.__thread_lock.release()
