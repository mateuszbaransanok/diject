import asyncio
from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

from diject.providers.provider import Pretender, PretenderBuilder, Provider
from diject.utils.cast import any_as_provider
from diject.utils.string import create_class_repr

T = TypeVar("T")


class ListProvider(Provider[list[T]]):
    def __init__(self, items: list[T]) -> None:
        super().__init__()
        self.__object = [any_as_provider(item) for item in items]

    def __repr__(self) -> str:
        return create_class_repr(self, self.__object)

    @property
    def __object__(self) -> list[Provider[T]]:
        return self.__object.copy()

    def __travers__(self) -> Iterator[tuple[str, Provider]]:
        yield from ((str(i), v) for i, v in enumerate(self.__object))

    def __provide_dependency__(self) -> list[T]:
        return [item.__provide__() for item in self.__object]

    async def __aprovide_dependency__(self) -> list[T]:
        return await asyncio.gather(*(item.__aprovide__() for item in self.__object))


class ListPretender(Pretender, Generic[T]):
    def __call__(self, items: list[T]) -> list[T]:
        return ListProvider(items)  # type: ignore[return-value]


class ListPretenderBuilder(PretenderBuilder[ListProvider]):
    def __getitem__(self, list_type: Callable[..., T]) -> ListPretender[T]:
        return ListPretender()

    def __call__(self, items: list[T]) -> list[T]:
        return ListProvider(items)  # type: ignore[return-value]

    @property
    def type(self) -> type[ListProvider]:
        return ListProvider
