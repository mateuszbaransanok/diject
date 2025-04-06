from typing import TypeVar, cast

from diject.injector import Injector
from diject.providers.creators.creator import CreatorProvider
from diject.utils.context import ContextItem

T = TypeVar("T")


class ScopedProvider(CreatorProvider[T]):
    def __provide_dependency__(self) -> T:
        context = Injector.get_context()

        if context is None:
            return self.__create__(allow_generator=False).instance

        if self in context.store:
            data = cast("ContextItem", context.store[self])
        else:
            data = ContextItem()
            context.store[self] = data

        if data.state is None:
            data.state = self.__create__()

        return data.state.instance

    async def __aprovide_dependency__(self) -> T:
        context = Injector.get_context()

        if context is None:
            obj = await self.__acreate__(allow_generator=False)
            return obj.instance

        async with context.async_lock:
            if self in context.store:
                data = cast("ContextItem", context.store[self])
            else:
                data = ContextItem()
                context.store[self] = data

        async with data.async_lock:
            if data.state is None:
                data.state = await self.__acreate__()

        return data.state.instance
