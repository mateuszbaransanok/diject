import asyncio
from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

from diject.providers.provider import Pretender, PretenderBuilder, Provider
from diject.utils.cast import any_as_provider
from diject.utils.string import create_class_repr

T = TypeVar("T")


class TupleProvider(Provider[tuple[T, ...]]):
    def __init__(self, items: tuple[T, ...]) -> None:
        super().__init__()
        self.__object = tuple(any_as_provider(item) for item in items)

    def __repr__(self) -> str:
        return create_class_repr(self, self.__object)

    @property
    def __object__(self) -> tuple[Provider[T], ...]:
        return self.__object

    def __travers__(self) -> Iterator[tuple[str, Provider]]:
        yield from ((str(i), v) for i, v in enumerate(self.__object))

    def __provide_dependency__(self) -> tuple[T, ...]:
        return tuple(item.__provide__() for item in self.__object)

    async def __aprovide_dependency__(self) -> tuple[T, ...]:
        return tuple(await asyncio.gather(*(item.__aprovide__() for item in self.__object)))


class TuplePretender(Pretender, Generic[T]):
    def __call__(self, items: tuple[T, ...]) -> tuple[T, ...]:
        return TupleProvider(items)  # type: ignore[return-value]


class TuplePretenderBuilder(PretenderBuilder[TupleProvider]):
    def __getitem__(self, tuple_type: Callable[..., T]) -> TuplePretender[T]:
        return TuplePretender()

    def __call__(self, items: tuple[T, ...]) -> tuple[T, ...]:
        return TupleProvider(items)  # type: ignore[return-value]

    @property
    def type(self) -> type[TupleProvider]:
        return TupleProvider
