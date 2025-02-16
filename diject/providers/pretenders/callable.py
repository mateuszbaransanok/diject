import asyncio
from collections.abc import Iterator
from typing import Any, get_type_hints

from diject.extensions.scope import Scope
from diject.providers.pretenders.pretender import PretenderProvider
from diject.providers.provider import Provider
from diject.utils.convert import any_as_provider
from diject.utils.repr import create_class_repr


class CallableProvider(PretenderProvider[Any]):
    def __init__(self, provider: Provider[Any], /, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.__provider = provider
        self.__args = tuple(any_as_provider(arg) for arg in args)
        self.__kwargs = {kw: any_as_provider(arg) for kw, arg in kwargs.items()}

    def __repr__(self) -> str:
        return create_class_repr(self, self.__provider, self.__args, self.__kwargs)

    def __propagate_alias__(self, alias: str) -> None:
        self.__provider.__alias__ = f"{alias}^"
        for name, provider in self.__travers__():
            provider.__alias__ = f"{alias}({name})"

    def __type__(self) -> Any:
        provide_type = self.__provider.__type__()
        try:
            return get_type_hints(provide_type).get("return", Any)
        except TypeError:
            return Any

    def __travers__(self) -> Iterator[tuple[str, Provider[Any]]]:
        for i, arg in enumerate(self.__args):
            yield str(i), arg

        for kw, arg in self.__kwargs.items():
            yield kw, arg

    def __provide__(self, scope: Scope | None = None) -> Any:
        obj = self.__provider.__provide__(scope)
        args = tuple(arg.__provide__(scope) for arg in self.__args)
        kwargs = {kw: arg.__provide__(scope) for kw, arg in self.__kwargs.items()}
        try:
            return obj(*args, **kwargs)
        except Exception as exc:
            exc.add_note(f"Error was encountered while providing {self}")
            raise

    async def __aprovide__(self, scope: Scope | None = None) -> Any:
        obj = await self.__provider.__aprovide__(scope)
        args = await asyncio.gather(*(arg.__aprovide__(scope) for arg in self.__args))
        values = await asyncio.gather(*(arg.__aprovide__(scope) for arg in self.__kwargs.values()))
        kwargs = {kw: arg for kw, arg in zip(self.__kwargs, values, strict=True)}
        try:
            return obj(*args, **kwargs)
        except Exception as exc:
            exc.add_note(f"Error was encountered while providing {self}")
            raise
