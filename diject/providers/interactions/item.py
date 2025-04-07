import asyncio
from collections.abc import Iterator
from typing import Any

from diject.exceptions import DIErrorWrapper
from diject.providers.provider import Provider
from diject.utils.cast import any_as_provider
from diject.utils.string import create_class_repr


class ItemProvider(Provider):
    def __init__(self, provider: Provider, /, item: Any) -> None:
        super().__init__()
        self.__provider = provider
        self.__item = any_as_provider(item)

    def __repr__(self) -> str:
        return create_class_repr(self, self.__provider, self.__item)

    def __propagate_alias__(self, alias: str) -> None:
        for name, provider in self.__travers__():
            provider.__alias__ = f"{alias}{name}"

    def __travers_dependency__(self) -> Iterator[tuple[str, Provider]]:
        yield "{[]}", self.__provider
        yield "[]", self.__item

    def __provide_dependency__(self) -> Any:
        obj = self.__provider.__provide__()
        item = self.__item.__provide__()
        try:
            return obj[item]
        except Exception as exc:
            raise DIErrorWrapper(
                origin=exc,
                note=f"Error was encountered while getting item '{self}'",
            ) from exc

    async def __aprovide_dependency__(self) -> Any:
        obj, item = await asyncio.gather(
            self.__provider.__aprovide__(),
            self.__item.__aprovide__(),
        )
        try:
            return obj[item]
        except Exception as exc:
            raise DIErrorWrapper(
                origin=exc,
                note=f"Error was encountered while getting item '{self}'",
            ) from exc
