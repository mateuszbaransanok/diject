import types
import warnings
from abc import ABCMeta
from collections.abc import Iterator
from typing import Any, TypeVar

from diject.extensions.scope import Scope
from diject.providers.pretenders.object import ObjectProvider
from diject.providers.provider import Provider
from diject.utils.convert import obj_as_provider

TProvider = TypeVar("TProvider", bound=Provider[Any])


def _as_provider(name: str, key: str, value: Any) -> Any:
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
        value = obj_as_provider(value)

    if isinstance(value, Provider):
        value.__alias__ = f"{name}.{key}"

    return value


class MetaContainer(ABCMeta):
    def __new__(
        cls,
        name: str,
        parents: tuple[type, ...],
        attributes: dict[str, Any],
    ) -> "MetaContainer":
        __attributes = {key: _as_provider(name, key, value) for key, value in attributes.items()}
        return super().__new__(cls, name, parents, __attributes)

    def __setattr__(cls, key: str, value: Any) -> None:
        if hasattr(cls, key):
            obj = getattr(cls, key)
            if isinstance(obj, ObjectProvider):
                obj.__object__ = value
                return
            elif isinstance(obj, Provider):
                warnings.warn(
                    "Do not change already defined provider (except `di.Object`), "
                    "because this can lead to unpredictable behavior. "
                    "If you want to replace this provider for testing purposes, "
                    "use `di.Mock` or `di.patch`."
                )
        elif isinstance(value, Provider):
            warnings.warn(
                "All providers should be defined in the container body, "
                "no new providers should be defined dynamically."
            )

        super().__setattr__(key, value)


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

    def __setattr__(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            if isinstance(getattr(type(self), key, None), Provider):
                warnings.warn(
                    "Do not change already defined provider inside Container instance, "
                    "because this can lead to unpredictable behavior. "
                    "If you want to replace this provider for testing purposes, "
                    "use `di.Mock` or `di.patch`."
                )
        elif isinstance(value, Provider):
            warnings.warn(
                "All providers should be defined in the container body, "
                "no new providers should be defined dynamically."
            )

        super().__setattr__(key, value)

    def __type__(self) -> Any:
        return type(self)

    def __travers__(self) -> Iterator[tuple[str, Provider[Any]]]:
        container = type(self)
        for name in list(vars(container)):
            if not name.startswith("__"):
                value = getattr(container, name)
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
