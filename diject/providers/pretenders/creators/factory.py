from typing import Final, TypeVar

from diject.extensions.scope import Scope
from diject.providers.pretenders.creators.creator import CreatorPretenderBuilder, CreatorProvider

T = TypeVar("T")


class FactoryProvider(CreatorProvider[T]):
    def __provide__(self, scope: Scope | None = None) -> T:
        return self.__create__(scope)

    async def __aprovide__(self, scope: Scope | None = None) -> T:
        return await self.__acreate__(scope)


Factory: Final = CreatorPretenderBuilder(FactoryProvider)
