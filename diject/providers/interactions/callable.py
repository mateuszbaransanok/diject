import asyncio
import itertools
from collections.abc import Iterator
from typing import Any

from diject.exceptions import DIErrorWrapper
from diject.providers.collections.dict import DictProvider
from diject.providers.collections.tuple import TupleProvider
from diject.providers.provider import Provider
from diject.utils.string import create_class_repr


class CallableProvider(Provider):
    def __init__(self, callable: Provider, /, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.__callable = callable
        self.__args = TupleProvider(args)
        self.__kwargs = DictProvider(kwargs)

    def __repr__(self) -> str:
        return create_class_repr(
            self, self.__callable, *self.__args.__object__, **self.__kwargs.__object__
        )

    def __propagate_alias__(self, alias: str) -> None:
        for name, provider in self.__travers__():
            provider.__alias__ = f"{alias}{name}"

    def __travers__(self) -> Iterator[tuple[str, Provider]]:
        yield "{()}", self.__callable
        yield from (
            (f"({name})", provider)
            for name, provider in itertools.chain(
                self.__args.__travers__(),
                self.__kwargs.__travers__(),
            )
        )

    def __provide_dependency__(self) -> Any:
        obj = self.__callable.__provide__()
        args = self.__args.__provide__()
        kwargs = self.__kwargs.__provide__()
        try:
            return obj(*args, **kwargs)
        except Exception as exc:
            raise DIErrorWrapper(
                origin=exc,
                note=f"Error was encountered while creating '{self}'",
            ) from exc

    async def __aprovide_dependency__(self) -> Any:
        obj, args, kwargs = await asyncio.gather(
            self.__callable.__aprovide__(),
            self.__args.__aprovide__(),
            self.__kwargs.__aprovide__(),
        )
        try:
            return obj(*args, **kwargs)
        except Exception as exc:
            raise DIErrorWrapper(
                origin=exc,
                note=f"Error was encountered while creating '{self}'",
            ) from exc
