import asyncio
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any, ParamSpec, TypeVar, overload
from unittest import mock

from diject.exceptions import DIErrorWrapper, DITypeError
from diject.injector import Injector
from diject.providers.provider import Provider
from diject.providers.selector import SelectorProvider
from diject.tools.patch import Patch
from diject.utils.status import Status

P = ParamSpec("P")
T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")
TProvider = TypeVar("TProvider", bound=Provider)


# ALIAS --------------------------------------------------------------------------------------------
def alias(obj: Any, /) -> str:
    if not isinstance(obj, Provider):
        raise DITypeError(f"Object {type(obj).__qualname__} is not Provider")
    return obj.__alias__


# STATUS -------------------------------------------------------------------------------------------
def status(obj: Any, /) -> Status:
    if not isinstance(obj, Provider):
        raise DITypeError(f"Object {type(obj).__qualname__} is not Provider")
    return obj.__status__


# TRAVERS ------------------------------------------------------------------------------------------
@overload
def travers(
    obj: Any,
    *,
    types: type[TProvider] | tuple[type[TProvider], ...],
    recursive: bool = False,
    only_selected: bool = False,
) -> Iterator[tuple[str, TProvider]]:
    pass


@overload
def travers(
    obj: Any,
    *,
    recursive: bool = False,
    only_selected: bool = False,
) -> Iterator[tuple[str, TProvider]]:
    pass


def travers(
    obj: Any,
    *,
    types: Any = None,
    recursive: bool = False,
    only_selected: bool = False,
) -> Any:
    if not isinstance(obj, Provider):
        raise DITypeError(f"Object {type(obj).__qualname__} is not Provider")

    try:
        yield from _travers(
            provider=obj,
            types=types or Provider,
            recursive=recursive,
            only_selected=only_selected,
            cache=set(),
        )
    except DIErrorWrapper as exc:
        raise exc.origin from exc.caused_by


def _travers(
    *,
    provider: Provider,
    types: type | tuple[type, ...],
    recursive: bool,
    only_selected: bool,
    cache: set[Provider],
) -> Any:
    if isinstance(provider, SelectorProvider):
        travers_generator = provider.__travers__(only_selected=only_selected)
    else:
        travers_generator = provider.__travers__()

    for sub_name, sub_provider in travers_generator:
        yield from travers_provider(
            name=sub_name,
            provider=sub_provider,
            types=types,
            recursive=recursive,
            only_selected=only_selected,
            cache=cache,
        )


def travers_provider(
    *,
    name: str,
    provider: Provider,
    types: type | tuple[type, ...],
    recursive: bool,
    only_selected: bool,
    cache: set[Provider],
) -> Any:
    if provider in cache:
        return

    cache.add(provider)

    if isinstance(provider, types):
        yield name, provider

    if recursive:
        yield from _travers(
            provider=provider,
            types=types,
            recursive=recursive,
            only_selected=only_selected,
            cache=cache,
        )


@overload
async def atravers(
    obj: Any,
    *,
    types: type[TProvider] | tuple[type[TProvider], ...],
    recursive: bool = False,
    only_selected: bool = False,
) -> AsyncIterator[tuple[str, TProvider]]:
    pass


@overload
async def atravers(
    obj: Any,
    *,
    recursive: bool = False,
    only_selected: bool = False,
) -> AsyncIterator[tuple[str, TProvider]]:
    pass


async def atravers(
    obj: Any,
    *,
    types: Any = None,
    recursive: bool = False,
    only_selected: bool = False,
) -> Any:
    if not isinstance(obj, Provider):
        raise DITypeError(f"Object {type(obj).__qualname__} is not Provider")

    async for name, provider in _atravers(
        provider=obj,
        types=types,
        recursive=recursive,
        only_selected=only_selected,
        lock=asyncio.Lock(),
        cache=set(),
    ):
        yield name, provider


async def _atravers(
    *,
    provider: Provider,
    types: type | tuple[type, ...],
    recursive: bool,
    only_selected: bool,
    lock: asyncio.Lock,
    cache: set[Provider],
) -> AsyncIterator[tuple[str, Provider]]:
    if isinstance(provider, SelectorProvider):
        async for sub_name, sub_provider in provider.__atravers__(only_selected=only_selected):
            async for _sub_name, _sub_provider in atravers_provider(
                name=sub_name,
                provider=sub_provider,
                types=types,
                recursive=recursive,
                only_selected=only_selected,
                lock=lock,
                cache=cache,
            ):
                yield _sub_name, _sub_provider
    else:
        for sub_name, sub_provider in provider.__travers__():
            async for _sub_name, _sub_provider in atravers_provider(
                name=sub_name,
                provider=sub_provider,
                types=types,
                recursive=recursive,
                only_selected=only_selected,
                lock=lock,
                cache=cache,
            ):
                yield _sub_name, _sub_provider


async def atravers_provider(
    *,
    name: str,
    provider: Provider,
    types: type | tuple[type, ...],
    recursive: bool,
    only_selected: bool,
    lock: asyncio.Lock,
    cache: set[Provider],
) -> Any:
    async with lock:
        if provider in cache:
            return

        cache.add(provider)

    if isinstance(provider, types):
        yield name, provider

    if recursive:
        async for sub_name, sub_provider in _atravers(
            provider=provider,
            types=types,
            recursive=recursive,
            only_selected=only_selected,
            lock=lock,
            cache=cache,
        ):
            yield sub_name, sub_provider


# PROVIDE ------------------------------------------------------------------------------------------
@overload
def provide(obj: Provider[T], /) -> T:
    pass


@overload
def provide(obj: T, /) -> T:
    pass


def provide(obj: Any, /) -> Any:
    if not isinstance(obj, Provider):
        raise DITypeError(f"Object {type(obj).__qualname__} is not Provider")

    try:
        return obj.__provide__()
    except DIErrorWrapper as exc:
        raise exc.origin from exc.caused_by


@overload
async def aprovide(obj: Provider[T], /) -> T:
    pass


@overload
async def aprovide(obj: T, /) -> T:
    pass


async def aprovide(obj: Any, /) -> Any:
    if not isinstance(obj, Provider):
        raise DITypeError(f"Object {type(obj).__qualname__} is not Provider")

    try:
        return await obj.__aprovide__()
    except DIErrorWrapper as exc:
        raise exc.origin from exc.caused_by


# START --------------------------------------------------------------------------------------------
def start(obj: Any, /) -> None:
    if not isinstance(obj, Provider):
        raise DITypeError(f"Object {type(obj).__qualname__} is not Provider")

    try:
        obj.__start__()
    except DIErrorWrapper as exc:
        raise exc.origin from exc.caused_by


async def astart(obj: Any, /) -> None:
    if not isinstance(obj, Provider):
        raise DITypeError(f"Object {type(obj).__qualname__} is not Provider")

    try:
        await obj.__astart__()
    except DIErrorWrapper as exc:
        raise exc.origin from exc.caused_by


# SHUTDOWN -----------------------------------------------------------------------------------------
def shutdown(obj: Any, /) -> None:
    if not isinstance(obj, Provider):
        raise DITypeError(f"Object {type(obj).__qualname__} is not Provider")

    try:
        obj.__shutdown__()
    except DIErrorWrapper as exc:
        raise exc.origin from exc.caused_by


async def ashutdown(obj: Any, /) -> None:
    if not isinstance(obj, Provider):
        raise DITypeError(f"Object {type(obj).__qualname__} is not Provider")

    try:
        await obj.__ashutdown__()
    except DIErrorWrapper as exc:
        raise exc.origin from exc.caused_by


# INJECTOR -----------------------------------------------------------------------------------------
@overload
def inject(
    func: Callable[P, T], *, reuse_context: bool = True,
) -> Callable[P, T] | Callable[..., T]:
    pass


@overload
def inject(*, reuse_context: bool = True) -> Injector:
    pass


def inject(func: Any | None = None, *, reuse_context: bool = True) -> Any:
    injector = Injector(reuse_context=reuse_context)

    if func is None:
        return injector
    return injector(func)


# PATCH --------------------------------------------------------------------------------------------
def patch(
    provider: Any,
    *,
    return_value: Any = mock.DEFAULT,
    side_effect: Any = None,
    **mock_kwargs: mock.Mock,
) -> Patch:
    return Patch(
        provider=provider,
        return_value=return_value,
        side_effect=side_effect,
        **mock_kwargs,
    )
