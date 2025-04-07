from collections.abc import Iterator
from typing import Any

from diject.exceptions import DIErrorWrapper
from diject.providers.provider import Provider
from diject.utils.string import create_class_repr


class AttributeProvider(Provider):
    def __init__(self, provider: Provider, /, name: str) -> None:
        super().__init__()
        self.__provider = provider
        self.__name = name

    def __repr__(self) -> str:
        return create_class_repr(self, self.__provider, self.__name)

    def __propagate_alias__(self, alias: str) -> None:
        for name, provider in self.__travers__():
            provider.__alias__ = f"{alias}{name}"

    def __travers_dependency__(self) -> Iterator[tuple[str, Provider]]:
        yield f"{{{self.__name}}}", self.__provider

    def __provide_dependency__(self) -> Any:
        obj = self.__provider.__provide__()
        try:
            return getattr(obj, self.__name)
        except Exception as exc:
            raise DIErrorWrapper(
                origin=exc,
                note=f"Error was encountered while getting attribute '{self}'",
            ) from exc

    async def __aprovide_dependency__(self) -> Any:
        obj = await self.__provider.__aprovide__()
        try:
            return getattr(obj, self.__name)
        except Exception as exc:
            raise DIErrorWrapper(
                origin=exc,
                note=f"Error was encountered while getting attribute '{self}'",
            ) from exc
