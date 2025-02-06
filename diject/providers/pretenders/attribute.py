from typing import Any, Iterator

from diject.extensions.scope import Scope
from diject.providers.pretenders.pretender import PretenderProvider
from diject.providers.provider import Provider
from diject.utils.repr import create_class_repr


class AttributeProvider(PretenderProvider[Any]):
    def __init__(self, provider: Provider[Any], /, name: str) -> None:
        super().__init__()
        self.__provider = provider
        self.__name = name

    def __repr__(self) -> str:
        return create_class_repr(self, self.__provider, self.__name)

    def __propagate_alias__(self, alias: str) -> None:
        self.__provider.__alias__ = f"{alias}^"

    def __travers__(self) -> Iterator[tuple[str, Provider[Any]]]:
        yield from ()

    def __provide__(self, scope: Scope | None = None) -> Any:
        obj = self.__provider.__provide__(scope)
        try:
            return getattr(obj, self.__name)
        except Exception as exc:
            exc.add_note(f"Error was encountered while providing {self}")
            raise

    async def __aprovide__(self, scope: Scope | None = None) -> Any:
        obj = await self.__provider.__aprovide__(scope)
        try:
            return getattr(obj, self.__name)
        except Exception as exc:
            exc.add_note(f"Error was encountered while providing {self}")
            raise
