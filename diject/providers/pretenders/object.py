from typing import Any, Final, Iterator, TypeVar

from diject.extensions.scope import Scope
from diject.providers.pretenders.pretender import PretenderBuilder, PretenderProvider
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


class ObjectPretenderBuilder(PretenderBuilder):
    def __call__(self, obj: T, /) -> T:
        return ObjectProvider(obj)  # type: ignore[return-value]


Object: Final = ObjectPretenderBuilder()
