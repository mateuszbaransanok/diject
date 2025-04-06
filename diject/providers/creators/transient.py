from typing import TypeVar, cast

from diject.injector import Injector
from diject.providers.creators.creator import CreatorProvider
from diject.utils.context import ContextList

T = TypeVar("T")


class TransientProvider(CreatorProvider[T]):
    def __provide_dependency__(self) -> T:
        context = Injector.get_context()

        if context is None:
            return self.__create__(allow_generator=False).instance

        if self in context.store:
            data = cast("ContextList", context.store[self])
        else:
            data = ContextList()
            context.store[self] = data

        obj = self.__create__()
        data.states.append(obj)
        return obj.instance

    async def __aprovide_dependency__(self) -> T:
        context = Injector.get_context()

        if context is None:
            obj = await self.__acreate__(allow_generator=False)
            return obj.instance

        async with context.async_lock:
            if self in context.store:
                data = cast("ContextList", context.store[self])
            else:
                data = ContextList()
                context.store[self] = data

        obj = self.__create__()
        data.states.append(obj)
        return obj.instance
