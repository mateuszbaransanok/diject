from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any, Generic, TypeVar

from diject.extensions.reset import ResetProtocol
from diject.extensions.scope import Scope
from diject.extensions.status import Status, StatusProtocol
from diject.providers.pretenders.creators.services.service import (
    ServiceProvider,
)
from diject.utils.empty import Empty
from diject.utils.lock import Lock

T = TypeVar("T")


class SingletonData(Generic[T]):
    def __init__(self, obj: Iterator[T] | AsyncIterator[T] | T, instance: T) -> None:
        self.object = obj
        self.instance = instance


class SingletonProvider(ServiceProvider[T], StatusProtocol, ResetProtocol):
    def __init__(
        self,
        callable: Callable[..., Iterator[T] | AsyncIterator[T] | T],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(callable, *args, **kwargs)
        self.__lock = Lock()
        self.__data: SingletonData | Empty = Empty()

    def __provide__(self, scope: Scope | None = None) -> T:
        with self.__lock:
            if isinstance(self.__data, Empty):
                obj, instance = self.__create_object_and_instance__(scope)
                self.__data = SingletonData(obj, instance)
            else:
                instance = self.__data.instance

        return instance

    async def __aprovide__(self, scope: Scope | None = None) -> T:
        async with self.__lock:
            if isinstance(self.__data, Empty):
                obj, instance = await self.__acreate_object_and_instance__(scope)
                self.__data = SingletonData(obj, instance)
            else:
                instance = self.__data.instance

        return instance

    def __status__(self) -> Status:
        return Status.STOPPED if isinstance(self.__data, Empty) else Status.STARTED

    def __reset__(self) -> None:
        with self.__lock:
            if not isinstance(self.__data, Empty):
                try:
                    self.__close_object__(self.__data.object)
                finally:
                    self.__data = Empty()

    async def __areset__(self) -> None:
        async with self.__lock:
            if not isinstance(self.__data, Empty):
                try:
                    await self.__aclose_object__(self.__data.object)
                finally:
                    self.__data = Empty()
