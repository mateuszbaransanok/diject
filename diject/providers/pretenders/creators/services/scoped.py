from typing import Any, AsyncIterator, Callable, Final, Generic, Iterator, Type, TypeVar

from diject.extensions.scope import Scope, ScopeProtocol
from diject.providers.pretenders.creators.services.service import (
    ServicePretenderBuilder,
    ServiceProvider,
)
from diject.utils.exceptions import DIScopeError
from diject.utils.lock import Lock

T = TypeVar("T")


class ScopedData(Generic[T]):
    def __init__(self) -> None:
        self.lock = Lock()
        self.data: tuple[Iterator[T] | AsyncIterator[T] | T, T] | None = None


class ScopedProvider(ServiceProvider[T], ScopeProtocol[ScopedData[T]]):
    def __init__(
        self,
        callable: (
            Callable[..., Iterator[T]]
            | Callable[..., AsyncIterator[T]]
            | Type[T]
            | Callable[..., T]
        ),
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
            if self in scope:
                scoped_data = scope[self]
            else:
                scoped_data = ScopedData()
                scope[self] = scoped_data

        with scoped_data.lock:
            if scoped_data.data is None:
                obj, instance = self.__create_object_and_instance__(scope)
                scoped_data.data = obj, instance
            else:
                obj, instance = scoped_data.data

        return instance

    async def __aprovide__(self, scope: Scope | None = None) -> T:
        if scope is None:
            raise DIScopeError(f"'{self}' has to be called within scope")

        with self.__lock:
            if self in scope:
                scoped_data = scope[self]
            else:
                scoped_data = ScopedData()
                scope[self] = scoped_data

        with scoped_data.lock:
            if scoped_data.data is None:
                obj, instance = await self.__acreate_object_and_instance__(scope)
                scoped_data.data = obj, instance
            else:
                obj, instance = scoped_data.data

        return instance

    def __reset__(self, scoped_data: ScopedData) -> None:
        if scoped_data.data is not None:
            obj, instance = scoped_data.data
            try:
                self.__close_object__(obj)
            finally:
                scoped_data.data = None

    async def __areset__(self, scoped_data: ScopedData) -> None:
        if scoped_data.data is not None:
            obj, instance = scoped_data.data
            try:
                await self.__aclose_object__(obj)
            finally:
                scoped_data.data = None


Scoped: Final = ServicePretenderBuilder(ScopedProvider)
