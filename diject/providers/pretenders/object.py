from typing import Any, Callable, Final, Generic, Iterator, TypeVar

from diject.extensions.scope import Scope
from diject.providers.pretenders.pretender import Pretender, PretenderBuilder, PretenderProvider
from diject.providers.provider import Provider
from diject.utils.empty import EMPTY, Empty
from diject.utils.exceptions import DIEmptyObjectError
from diject.utils.repr import create_class_repr

T = TypeVar("T")


class ObjectProvider(PretenderProvider[T]):
    def __init__(self, obj: T) -> None:
        super().__init__()
        self.__obj = obj

    def __repr__(self) -> str:
        return create_class_repr(self, self.__obj)

    @property
    def __object__(self) -> T:
        return self.__obj

    @__object__.setter
    def __object__(self, obj: T) -> None:
        self.__obj = obj

    def __travers__(self) -> Iterator[tuple[str, Provider[Any]]]:
        yield from ()

    def __provide__(self, scope: Scope | None = None) -> T:
        if isinstance(self.__obj, Empty):
            raise DIEmptyObjectError(f"{self} is not set")
        return self.__obj

    async def __aprovide__(self, scope: Scope | None = None) -> T:
        return self.__provide__()


class ObjectPretender(Pretender, Generic[T]):
    def __call__(self, obj: T | Empty = EMPTY) -> T:
        return ObjectProvider(obj)  # type: ignore[return-value]


class ObjectPretenderBuilder(PretenderBuilder):
    def __getitem__(self, object_type: Callable[..., T]) -> ObjectPretender[T]:
        return ObjectPretender()

    def __call__(self, obj: T) -> T:
        return ObjectProvider(obj)  # type: ignore[return-value]


Object: Final = ObjectPretenderBuilder()
