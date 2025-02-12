from collections.abc import Callable, Iterator
from types import EllipsisType
from typing import Generic, TypeVar

from diject.exceptions import DIObjectError
from diject.providers.provider import Pretender, PretenderBuilder, Provider
from diject.utils.status import Status
from diject.utils.string import create_class_repr

T = TypeVar("T")


class ObjectProvider(Provider[T]):
    def __init__(self, obj: T) -> None:
        super().__init__()
        self.__origin = obj
        self.__object: T | EllipsisType = ...

    def __repr__(self) -> str:
        return create_class_repr(self, self.__object__)

    @property
    def __object__(self) -> T:
        if self.__object is ...:
            return self.__origin
        return self.__object

    @__object__.setter
    def __object__(self, obj: T) -> None:
        with self.__lock__:
            if self.__object is not ...:
                raise DIObjectError(f"{self} is already set")
            self.__object = obj
            self.__status__ = Status.RUNNING

    def __travers__(self) -> Iterator[tuple[str, Provider]]:
        yield from ()

    def __provide_dependency__(self) -> T:
        with self.__lock__:
            return self.__provide()

    async def __aprovide_dependency__(self) -> T:
        async with self.__lock__:
            return self.__provide()

    def __provide(self) -> T:
        if self.__object is ...:
            if self.__origin is ...:
                raise DIObjectError(f"{self} is not set")
            self.__object = self.__origin
        return self.__object

    def __shutdown_dependency__(self) -> None:
        self.__object = ...

    async def __ashutdown_dependency__(self) -> None:
        self.__object = ...


class ObjectPretender(Pretender, Generic[T]):
    def __call__(self, obj: T | EllipsisType = ...) -> T:
        return ObjectProvider(obj)  # type: ignore[return-value]


class ObjectPretenderBuilder(PretenderBuilder[ObjectProvider]):
    def __getitem__(self, object_type: Callable[..., T]) -> ObjectPretender[T]:
        return ObjectPretender()

    def __call__(self, obj: T | EllipsisType = ...) -> T:
        return ObjectProvider(obj)  # type: ignore[return-value]

    @property
    def type(self) -> type[ObjectProvider]:
        return ObjectProvider
