import asyncio
from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

from diject.providers.provider import Pretender, PretenderBuilder, Provider
from diject.utils.cast import any_as_provider
from diject.utils.string import create_class_repr, to_safe_string

KT = TypeVar("KT")
VT = TypeVar("VT")


class DictProvider(Provider[dict[KT, VT]]):
    def __init__(self, dictionary: dict[KT, VT]) -> None:
        super().__init__()
        self.__object = {key: any_as_provider(value) for key, value in dictionary.items()}

    def __repr__(self) -> str:
        return create_class_repr(self, self.__object)

    @property
    def __object__(self) -> dict[KT, Provider[VT]]:
        return self.__object.copy()

    def __travers__(self) -> Iterator[tuple[str, Provider]]:
        yield from ((to_safe_string(key), value) for key, value in self.__object.items())

    def __provide_dependency__(self) -> dict[KT, VT]:
        return {key: value.__provide__() for key, value in self.__object.items()}

    async def __aprovide_dependency__(self) -> dict[KT, VT]:
        values = await asyncio.gather(*(value.__aprovide__() for value in self.__object.values()))
        return {key: value for key, value in zip(self.__object, values, strict=True)}


class DictPretender(Pretender, Generic[KT, VT]):
    def __call__(self, dictionary: dict[KT, VT]) -> dict[KT, VT]:
        return DictProvider(dictionary)  # type: ignore[return-value]


class DictPretenderBuilder(PretenderBuilder[DictProvider]):
    def __getitem__(
        self,
        dict_type: tuple[Callable[..., KT], Callable[..., VT]],
    ) -> DictPretender[KT, VT]:
        return DictPretender()

    def __call__(self, dictionary: dict[KT, VT]) -> dict[KT, VT]:
        return DictProvider(dictionary)  # type: ignore[return-value]

    @property
    def type(self) -> type[DictProvider]:
        return DictProvider
