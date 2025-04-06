import asyncio
import warnings
from abc import ABCMeta
from collections.abc import AsyncIterator, Iterator
from typing import Any, TypeVar, overload

from diject import functions
from diject.exceptions import DIContainerError, DIErrorWrapper
from diject.providers.object import ObjectProvider
from diject.providers.provider import Provider
from diject.utils.cast import any_as_provider

TProvider = TypeVar("TProvider", bound=Provider)


class MetaContainer(ABCMeta):
    def __new__(
        cls,
        name: str,
        parents: tuple[type, ...],
        attributes: dict[str, Any],
    ) -> "MetaContainer":
        for _key, _value in attributes.items():
            if not (
                _key.startswith("__")
                or isinstance(_value, (classmethod, staticmethod, Provider))
                or (isinstance(_value, type) and issubclass(_value, Container))
            ):
                attributes[_key] = _value = any_as_provider(_value)

            if isinstance(_value, Provider):
                _value.__alias__ = f"{name}.{_key}"

        return super().__new__(cls, name, parents, attributes)

    def __call__(cls) -> None:
        raise DIContainerError("Container cannot be instantiated")

    def __setattr__(cls, name: str, value: Any) -> None:
        if obj := getattr(cls, name, None):
            if isinstance(obj, ObjectProvider):
                obj.__object__ = value
            elif isinstance(obj, Provider):
                warnings.warn(
                    "Do not change already defined provider (except `di.Object`), "
                    "because this can lead to unpredictable behavior. "
                    "If you want to replace this provider for testing purposes, use `di.patch`.",
                )
        elif isinstance(value, Provider):
            warnings.warn(
                "All providers should be defined in the container body, "
                "no new providers should be defined dynamically.",
            )
        else:
            super().__setattr__(name, value)


class Container(metaclass=MetaContainer):
    @classmethod
    @overload
    def travers(
        cls,
        types: type[TProvider] | tuple[type[TProvider], ...],
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> Iterator[tuple[str, TProvider]]:
        pass

    @classmethod
    @overload
    def travers(
        cls,
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> Iterator[tuple[str, Provider]]:
        pass

    @classmethod
    def travers(
        cls,
        types: type[TProvider] | tuple[type[TProvider], ...] | None = None,
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> Any:
        """Traverses the provider and its sub-providers, yielding their names and types.

        Args:
            types: The types of providers to traverse.
            recursive: Whether to traverse recursively.
            only_public: Whether to include only public providers inside Container.
            only_selected: Whether to include only selected providers.

        Yields:
            tuple[str, Provider]: The name and provider of each item found.

        """
        try:
            yield from cls.__travers__(
                types=types or Provider,
                recursive=recursive,
                only_public=only_public,
                only_selected=only_selected,
                cache=set(),
            )
        except DIErrorWrapper as exc:
            raise exc.origin from exc.caused_by

    @classmethod
    def __travers__(
        cls,
        *,
        types: type[TProvider] | tuple[type[TProvider], ...],
        recursive: bool,
        only_public: bool,
        only_selected: bool,
        cache: set[Provider],
    ) -> Iterator[tuple[str, Provider]]:
        for name, obj in cls.__iter(only_public=only_public):
            if isinstance(obj, Provider):
                yield from functions.travers_provider(
                    name=name,
                    provider=obj,
                    types=types,
                    recursive=recursive,
                    only_selected=only_selected,
                    cache=cache,
                )
            elif recursive and isinstance(obj, type) and issubclass(obj, Container):
                yield from obj.__travers__(
                    types=types,
                    recursive=recursive,
                    only_public=only_public,
                    only_selected=only_selected,
                    cache=cache,
                )

    @classmethod
    @overload
    async def atravers(
        cls,
        types: type[TProvider] | tuple[type[TProvider], ...],
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> AsyncIterator[tuple[str, TProvider]]:
        pass

    @classmethod
    @overload
    async def atravers(
        cls,
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> AsyncIterator[tuple[str, Provider]]:
        pass

    @classmethod
    async def atravers(
        cls,
        types: type[TProvider] | tuple[type[TProvider], ...] | None = None,
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> Any:
        """Traverses the provider and its sub-providers, yielding their names and types.

        Args:
            types: The types of providers to traverse.
            recursive: Whether to traverse recursively.
            only_public: Whether to include only public providers inside Container.
            only_selected: Whether to include only selected providers.

        Yields:
            tuple[str, Provider]: The name and provider of each item found.

        """
        try:
            async for name, provider in cls.__atravers__(
                types=types or Provider,
                recursive=recursive,
                only_public=only_public,
                only_selected=only_selected,
                lock=asyncio.Lock(),
                cache=set(),
            ):
                yield name, provider
        except DIErrorWrapper as exc:
            raise exc.origin from exc.caused_by

    @classmethod
    async def __atravers__(
        cls,
        *,
        types: type[TProvider] | tuple[type[TProvider], ...],
        recursive: bool,
        only_public: bool,
        only_selected: bool,
        lock: asyncio.Lock,
        cache: set[Provider],
    ) -> AsyncIterator[tuple[str, Provider]]:
        for name, obj in cls.__iter(only_public=only_public):
            if isinstance(obj, Provider):
                async for _name, _provider in functions.atravers_provider(
                    name=name,
                    provider=obj,
                    types=types,
                    recursive=recursive,
                    only_selected=only_selected,
                    lock=lock,
                    cache=cache,
                ):
                    yield _name, _provider
            elif recursive and isinstance(obj, type) and issubclass(obj, Container):
                async for _name, _provider in obj.__atravers__(
                    types=types,
                    recursive=recursive,
                    only_public=only_public,
                    only_selected=only_selected,
                    lock=lock,
                    cache=cache,
                ):
                    yield _name, _provider

    @classmethod
    def start(cls) -> None:
        """Start the providers.

        This method initiates the provider by calling its internal start method
        (if it supports the StartProtocol). It also ensures that all necessary
        initialization tasks are completed for the provider.
        """
        try:
            cls.__start__()
        except DIErrorWrapper as exc:
            raise exc.origin from exc.caused_by

    @classmethod
    def __start__(cls) -> None:
        for name, obj in cls.__iter(only_public=True):
            if (
                isinstance(obj, Provider)
                or (isinstance(obj, type) and issubclass(obj, Container))
            ):
                obj.__start__()

    @classmethod
    async def astart(cls) -> None:
        """Start the providers.

        This method initiates the provider by calling its internal start method
        (if it supports the StartProtocol). It also ensures that all necessary
        initialization tasks are completed for the provider.
        """
        try:
            await cls.__astart__()
        except DIErrorWrapper as exc:
            raise exc.origin from exc.caused_by

    @classmethod
    async def __astart__(cls) -> None:
        await asyncio.gather(
            *(
                obj.__astart__()
                for name, obj in cls.__iter(only_public=True)
                if (
                    isinstance(obj, Provider)
                    or (isinstance(obj, type) and issubclass(obj, Container))
                )
            ),
        )

    @classmethod
    def shutdown(cls) -> None:
        """Reset the providers.

        This method performs a graceful shutdown of the provider, calling its internal
        reset method recursively if it supports the ResetProtocol. It ensures all
        resources are released properly.
        """
        try:
            cls.__shutdown__()
        except DIErrorWrapper as exc:
            raise exc.origin from exc.caused_by

    @classmethod
    def __shutdown__(cls) -> None:
        for name, obj in cls.__iter(only_public=True):
            if (
                isinstance(obj, Provider)
                or (isinstance(obj, type) and issubclass(obj, Container))
            ):
                obj.__shutdown__()

    @classmethod
    async def ashutdown(cls) -> None:
        """Shutdown the providers.

        This method initiates the provider by calling its internal shutdown method
        (if it supports the ShutdownProtocol). It also ensures that all necessary
        initialization tasks are completed for the provider.
        """
        try:
            await cls.__ashutdown__()
        except DIErrorWrapper as exc:
            raise exc.origin from exc.caused_by

    @classmethod
    async def __ashutdown__(cls) -> None:
        await asyncio.gather(
            *(
                obj.__ashutdown__()
                for name, obj in cls.__iter(only_public=True)
                if (
                    isinstance(obj, Provider)
                    or (isinstance(obj, type) and issubclass(obj, Container))
                )
            ),
        )

    @classmethod
    def __iter(cls, *, only_public: bool = False) -> Iterator[tuple[str, Any]]:
        for name in list(vars(cls)):
            if not ((only_public and name.startswith("_")) or name.startswith("__")):
                yield name, getattr(cls, name)
