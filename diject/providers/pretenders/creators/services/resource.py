import logging
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any, Generic, TypeVar

from diject.extensions.reset import ResetProtocol
from diject.extensions.scope import Scope
from diject.extensions.start import StartProtocol
from diject.extensions.status import Status, StatusProtocol
from diject.providers.pretenders.creators.services.service import (
    ServiceProvider,
)
from diject.utils.empty import EMPTY, Empty
from diject.utils.exceptions import DINotStartedError
from diject.utils.lock import Lock

T = TypeVar("T")

LOG = logging.getLogger(__name__)


class ResourceData(Generic[T]):
    def __init__(
        self,
        obj: Iterator[T] | AsyncIterator[T] | T | Empty = EMPTY,
        instance: T | Empty = EMPTY,
        start_error: Exception | None = None,
    ) -> None:
        if (
            (obj is EMPTY and instance is not EMPTY)
            or (obj is not EMPTY and instance is EMPTY)
            or (obj is not EMPTY and instance is not EMPTY and start_error is not None)
        ):
            raise ValueError("Provide `obj` and `instance`, or `start_error` or nothing")

        self.__object = obj
        self.__instance = instance
        self.__start_error = start_error

    @property
    def object(self) -> Iterator[T] | AsyncIterator[T] | T:
        if isinstance(self.__object, Empty):
            raise ValueError("Object is not set")
        return self.__object

    @property
    def instance(self) -> T:
        if isinstance(self.__instance, Empty):
            raise ValueError("Instance is not set")
        return self.__instance

    @property
    def start_error(self) -> Exception | None:
        return self.__start_error

    def is_started(self) -> bool:
        return not isinstance(self.__object, Empty)


class ResourceProvider(ServiceProvider[T], StatusProtocol, StartProtocol, ResetProtocol):
    def __init__(
        self,
        callable: Callable[..., Iterator[T] | AsyncIterator[T] | T],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(callable, *args, **kwargs)
        self.__lock = Lock()
        self.__data = ResourceData[T]()

    def __provide__(self, scope: Scope | None = None) -> T:
        with self.__lock:
            return self.__provide()

    async def __aprovide__(self, scope: Scope | None = None) -> T:
        async with self.__lock:
            return self.__provide()

    def __provide(self) -> T:
        if not self.__data.is_started():
            raise DINotStartedError(
                f"The resource '{self}' is not started; ensure the resource provider "
                "has started without any errors"
            ) from self.__data.start_error

        return self.__data.instance

    def __status__(self) -> Status:
        if self.__data.is_started():
            return Status.STARTED
        if self.__data.start_error is None:
            return Status.STOPPED
        else:
            return Status.ERROR

    def __start__(self) -> None:
        with self.__lock:
            if not self.__data.is_started():
                LOG.debug("Start %s", self)
                try:
                    obj, instance = self.__create_object_and_instance__()
                except Exception as exc:
                    self.__data = ResourceData(
                        start_error=exc,
                    )
                    raise
                else:
                    self.__data = ResourceData(
                        obj=obj,
                        instance=instance,
                    )

    async def __astart__(self) -> None:
        async with self.__lock:
            if not self.__data.is_started():
                LOG.debug("Async start %s", self)
                try:
                    obj, instance = await self.__acreate_object_and_instance__()
                except Exception as exc:
                    self.__data = ResourceData(
                        start_error=exc,
                    )
                    raise
                else:
                    self.__data = ResourceData(
                        obj=obj,
                        instance=instance,
                    )

    def __reset__(self) -> None:
        with self.__lock:
            if self.__data.is_started():
                LOG.debug("Shutdown %s", self)

                try:
                    self.__close_object__(self.__data.object)
                finally:
                    self.__data = ResourceData()

    async def __areset__(self) -> None:
        async with self.__lock:
            if self.__data.is_started():
                LOG.debug("Async shutdown %s", self)

                try:
                    await self.__aclose_object__(self.__data.object)
                finally:
                    self.__data = ResourceData()
