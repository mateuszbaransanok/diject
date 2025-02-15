from collections.abc import Callable, Iterator
from typing import Any, Generic, TypeVar

from diject.extensions.reset import ResetProtocol
from diject.extensions.scope import Scope
from diject.providers.pretenders.pretender import Pretender, PretenderBuilder, PretenderProvider
from diject.providers.provider import Provider
from diject.utils.empty import EMPTY, Empty
from diject.utils.exceptions import DIEmptyObjectError
from diject.utils.repr import create_class_repr

T = TypeVar("T")


class ObjectProvider(PretenderProvider[T], ResetProtocol):
    def __init__(self, obj: T) -> None:
        super().__init__()
        self.__origin = obj
        self.__object = obj

    def __repr__(self) -> str:
        return create_class_repr(self, self.__object)

    @property
    def __object__(self) -> T:
        return self.__object

    @__object__.setter
    def __object__(self, obj: T) -> None:
        self.__object = obj

    def __travers__(self) -> Iterator[tuple[str, Provider[Any]]]:
        yield from ()

    def __type__(self) -> Any:
        return type(self.__object)

    def __provide__(self, scope: Scope | None = None) -> T:
        if isinstance(self.__object, Empty):
            raise DIEmptyObjectError(f"{self} is not set")
        return self.__object

    async def __aprovide__(self, scope: Scope | None = None) -> T:
        return self.__provide__()

    def __reset__(self) -> None:
        self.__object = self.__origin

    async def __areset__(self) -> None:
        self.__object = self.__origin


class ObjectPretender(Pretender, Generic[T]):
    def __call__(self, obj: T | Empty = EMPTY) -> T:
        return ObjectProvider(obj)  # type: ignore[return-value]


class ObjectPretenderBuilder(PretenderBuilder):
    def __getitem__(self, object_type: Callable[..., T]) -> ObjectPretender[T]:
        return ObjectPretender()

    def __call__(self, obj: T) -> T:
        return ObjectProvider(obj)  # type: ignore[return-value]
