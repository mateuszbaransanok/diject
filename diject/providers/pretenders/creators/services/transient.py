import asyncio
import logging
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any, Generic, TypeVar

from diject.extensions.scope import Scope, ScopeProtocol
from diject.providers.pretenders.creators.services.service import (
    ServiceProvider,
)
from diject.utils.exceptions import DIScopeError
from diject.utils.lock import Lock

T = TypeVar("T")

LOG = logging.getLogger(__name__)


class TransientData(Generic[T]):
    def __init__(self) -> None:
        self.lock = Lock()
        self.data: list[tuple[Iterator[T] | AsyncIterator[T] | T, T]] = []


class TransientProvider(ServiceProvider[T], ScopeProtocol[TransientData]):
    def __init__(
        self,
        callable: Callable[..., Iterator[T] | AsyncIterator[T] | T],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(callable, *args, **kwargs)
        self.__lock = Lock()

    def __provide__(self, scope: Scope | None = None) -> T:
        if scope is None:
            raise DIScopeError(f"'{self}' has to be called within scope")

        with self.__lock:
            if self not in scope:
                scope[self] = TransientData()

        obj, instance = self.__create_object_and_instance__(scope)

        scope[self].data.append((obj, instance))

        return instance

    async def __aprovide__(self, scope: Scope | None = None) -> T:
        if scope is None:
            raise DIScopeError(f"'{self}' has to be called within scope")

        async with self.__lock:
            if self not in scope:
                scope[self] = TransientData()

        obj, instance = await self.__acreate_object_and_instance__(scope)

        scope[self].data.append((obj, instance))

        return instance

    def __close__(self, transient_data: TransientData) -> None:
        with transient_data.lock:
            try:
                for obj, instance in transient_data.data:
                    self.__close_object__(obj)
            except Exception as exc:
                LOG.error("Provider was reset incorrectly due to an error: %s", exc)
                raise
            finally:
                transient_data.data.clear()

    async def __aclose__(self, transient_data: TransientData) -> None:
        async with transient_data.lock:
            try:
                await asyncio.gather(
                    *(self.__aclose_object__(obj) for obj, instance in transient_data.data)
                )
            except Exception as exc:
                LOG.error("Provider was reset incorrectly due to an error: %s", exc)
                raise
            finally:
                transient_data.data.clear()
