from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, Generic, TypeVar

from diject.extensions.scope import Scope

T = TypeVar("T")


class Provider(Generic[T], ABC):
    def __init__(self) -> None:
        self.__alias = ""

    def __str__(self) -> str:
        return f"{self.__alias__} ({type(self).__qualname__})"

    @property
    def __has_alias__(self) -> bool:
        return bool(self.__alias)

    @property
    def __alias__(self) -> str:
        return self.__alias or type(self).__qualname__

    @__alias__.setter
    def __alias__(self, alias: str) -> None:
        if not self.__alias:
            self.__alias = alias
            self.__propagate_alias__(alias)

    def __propagate_alias__(self, alias: str) -> None:
        for name, provider in self.__travers__():
            provider.__alias__ = f"{alias}.{name}"

    @abstractmethod
    def __type__(self) -> Any:
        pass

    @abstractmethod
    def __travers__(self) -> Iterator[tuple[str, "Provider[Any]"]]:
        pass

    @abstractmethod
    def __provide__(self, scope: Scope | None = None) -> T:
        pass

    @abstractmethod
    async def __aprovide__(self, scope: Scope | None = None) -> T:
        pass
