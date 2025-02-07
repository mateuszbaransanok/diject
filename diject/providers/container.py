import types
from abc import ABCMeta
from typing import Any, Iterator, TypeVar

from diject.extensions.scope import Scope
from diject.providers.provider import Provider
from diject.utils.convert import obj_as_provider

TProvider = TypeVar("TProvider", bound=Provider[Any])


class MetaContainer(ABCMeta):
    def __new__(
        cls,
        name: str,
        parents: tuple[type, ...],
        attributes: dict[str, Any],
    ) -> "MetaContainer":
        for key, value in attributes.items():
            if not (
                key.startswith("__")
                or isinstance(value, (classmethod, staticmethod, property))
                or (
                    isinstance(value, types.FunctionType)
                    and value.__qualname__.startswith(f"{name}.")
                    and not value.__qualname__.startswith(f"{name}.<lambda>")
                )
                or isinstance(value, Provider)
                or (isinstance(value, type) and issubclass(value, Container))
            ):
                attributes[key] = obj_as_provider(value)

        __container = super().__new__(cls, name, parents, attributes)

        for key, value in attributes.items():
            if isinstance(value, Provider):
                value.__alias__ = f"{name}.{key}"

        return __container


class Container(Provider["Container"], metaclass=MetaContainer):
    def __init__(self) -> None:
        super().__init__()
        self.__is_providable = False
        self.__scope: Scope | None = None

    def __getattribute__(self, name: str) -> Any:
        obj = super().__getattribute__(name)
        if (
            not name.startswith("__")
            and not name.startswith("_Container__")
            and self.__is_providable
        ):
            if isinstance(obj, Provider):
                return obj.__provide__(self.__scope)
            elif isinstance(obj, type) and issubclass(obj, Container):
                return obj().__provide__(self.__scope)
        return obj

    def __travers__(self) -> Iterator[tuple[str, Provider[Any]]]:
        for name in list(vars(type(self))):
            if not name.startswith("__"):
                value = getattr(self, name)
                if isinstance(value, Provider):
                    yield name, value
                elif isinstance(value, type) and issubclass(value, Container):
                    yield name, value()

    def __provide__(self, scope: Scope | None = None) -> "Container":
        container = type(self)()
        container.__is_providable = True
        container.__scope = scope
        return container

    async def __aprovide__(self, scope: Scope | None = None) -> "Container":
        return self.__provide__(scope)
