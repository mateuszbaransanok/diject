from typing import Any, Final, Generic, Iterator, Type, TypeVar

from diject.extensions.scope import Scope
from diject.providers.pretenders.pretender import Pretender, PretenderBuilder, PretenderProvider
from diject.providers.provider import Provider
from diject.utils.repr import create_class_repr

T = TypeVar("T")


class ObjectProvider(PretenderProvider[T]):
    def __init__(self, obj: T) -> None:
        super().__init__()
        self.__obj = obj

    def __repr__(self) -> str:
        return create_class_repr(self, self.__obj)

    def __travers__(self) -> Iterator[tuple[str, Provider[Any]]]:
        yield from ()

    def __provide__(self, scope: Scope | None = None) -> T:
        return self.__obj

    async def __aprovide__(self, scope: Scope | None = None) -> T:
        return self.__obj


class ObjectPretender(Pretender, Generic[T]):
    def __init__(self, object_type: Type[T]) -> None:
        self.__object_type = object_type

    def __repr__(self) -> str:
        return create_class_repr(self, self.__object_type)

    def __call__(self, obj: T) -> T:
        return ObjectProvider(obj)  # type: ignore[return-value]


class ObjectPretenderBuilder(PretenderBuilder):
    def __getitem__(self, object_type: Type[T]) -> ObjectPretender[T]:
        return ObjectPretender(object_type)

    def __call__(self, obj: T) -> T:
        return ObjectProvider(obj)  # type: ignore[return-value]


Object: Final = ObjectPretenderBuilder()
