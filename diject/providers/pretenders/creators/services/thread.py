import threading
from collections.abc import Callable, Iterator
from typing import Any, Generic, ParamSpec, TypeVar, overload

from diject.extensions.reset import ResetProtocol
from diject.extensions.scope import Scope
from diject.extensions.status import Status, StatusProtocol
from diject.providers.pretenders.creators.services.service import (
    ServicePretender,
    ServiceProvider,
)
from diject.providers.pretenders.pretender import PretenderBuilder
from diject.utils.exceptions import DIAsyncError
from diject.utils.lock import Lock

T = TypeVar("T")
P = ParamSpec("P")


class ThreadData(Generic[T]):
    def __init__(
        self,
        data: tuple[Iterator[T] | T, T],
        on_close: Callable[[Iterator[T] | T], None],
    ) -> None:
        self.data = data
        self.on_close = on_close

    def __del__(self) -> None:
        obj, _ = self.data
        self.on_close(obj)


class ThreadProvider(ServiceProvider[T], StatusProtocol, ResetProtocol):
    def __init__(
        self,
        callable: Callable[..., Iterator[T] | T],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(callable, *args, **kwargs)
        self.__lock = Lock()
        self.__thread_data = threading.local()

    def __provide__(self, scope: Scope | None = None) -> T:
        with self.__lock:
            return self.__provide()

    async def __aprovide__(self, scope: Scope | None = None) -> T:
        async with self.__lock:
            try:
                return self.__provide()
            except DIAsyncError:
                raise DIAsyncError(f"'{self}' cannot provide asynchronous services")

    def __provide(self) -> T:
        if not hasattr(self.__thread_data, "objects"):
            self.__thread_data.objects = ThreadData(
                data=self.__create_object_and_instance__(),
                on_close=self.__close_object__,
            )

        _, instance = self.__thread_data.objects.data
        return instance

    def __status__(self) -> Status:
        return Status.STOPPED if hasattr(self.__thread_data, "objects") else Status.STARTED

    def __reset__(self, only_current_thread: bool = False) -> None:
        with self.__lock:
            if only_current_thread:
                if hasattr(self.__thread_data, "objects"):
                    delattr(self.__thread_data, "objects")
            else:
                del self.__thread_data
                self.__thread_data = threading.local()

    async def __areset__(self, only_current_thread: bool = False) -> None:
        async with self.__lock:
            if only_current_thread:
                if hasattr(self.__thread_data, "objects"):
                    delattr(self.__thread_data, "objects")
            else:
                del self.__thread_data
                self.__thread_data = threading.local()


class ThreadPretenderBuilder(PretenderBuilder):
    @overload
    def __getitem__(  # type: ignore[overload-overlap]
        self,
        callable: Callable[P, Iterator[T]],
    ) -> Callable[P, T]:
        pass

    @overload
    def __getitem__(self, callable: type[T]) -> type[T]:
        pass

    @overload
    def __getitem__(self, callable: Callable[P, T]) -> Callable[P, T]:
        pass

    def __getitem__(self, callable: Any) -> Any:
        return ServicePretender(
            provider_cls=ThreadProvider,
            callable=callable,
        )
