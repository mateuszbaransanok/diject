from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any, TypeVar

from diject.injector import Injector
from diject.providers.creators.creator import CreatorProvider
from diject.utils.context import Context
from diject.utils.state import State

T = TypeVar("T")


class SingletonProvider(CreatorProvider[T]):
    def __init__(
        self,
        callable: Callable[..., AsyncIterator[T] | Iterator[T] | T],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(callable, *args, **kwargs)
        self.__state: State[T] | None = None
        self.__context: Context[T] | None = None

    def __provide_dependency__(self) -> T:
        with self.__lock__:
            self.__start_dependency__()
            return self.__state.instance  # type: ignore[union-attr]

    async def __aprovide_dependency__(self) -> T:
        async with self.__lock__:
            await self.__astart_dependency__()
            return self.__state.instance  # type: ignore[union-attr]

    def __start_dependency__(self) -> None:
        if self.__state is None:
            with Injector(reuse_context=False, close_context=False) as self.__context:
                self.__state = self.__create__()

    async def __astart_dependency__(self) -> None:
        if self.__state is None:
            async with Injector(reuse_context=False, close_context=False) as self.__context:
                self.__state = await self.__acreate__()

    def __shutdown_dependency__(self) -> None:
        if self.__state is not None:
            self.__state.close()
            self.__state = None

        if self.__context is not None:
            self.__context.close()
            self.__context = None

    async def __ashutdown_dependency__(self) -> None:
        if self.__state is not None:
            await self.__state.aclose()
            self.__state = None

        if self.__context is not None:
            await self.__context.aclose()
            self.__context = None
