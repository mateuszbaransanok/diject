import asyncio
import threading
from types import TracebackType


class Lock:
    def __init__(self) -> None:
        self._thread_lock = threading.Lock()
        self._thread_data = threading.local()

    @property
    def _async_lock(self) -> asyncio.Lock:
        if not hasattr(self._thread_data, "async_lock"):
            self._thread_data.async_lock = asyncio.Lock()
        return self._thread_data.async_lock

    def __enter__(self) -> None:
        self.acquire()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.release()

    async def __aenter__(self) -> None:
        await self.aacquire()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.arelease()

    def acquire(self) -> None:
        self._thread_lock.acquire()

    async def aacquire(self) -> None:
        await self._async_lock.acquire()
        self._thread_lock.acquire()

    def release(self) -> None:
        self._thread_lock.release()

    async def arelease(self) -> None:
        self._async_lock.release()
        self._thread_lock.release()
