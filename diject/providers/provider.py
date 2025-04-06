import asyncio
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from diject.utils.lock import Lock
from diject.utils.status import Status
from diject.utils.string import create_class_repr, to_safe_string

if TYPE_CHECKING:
    from diject.providers.interactions.attribute import AttributeProvider
    from diject.providers.interactions.callable import CallableProvider
    from diject.providers.interactions.item import ItemProvider

T = TypeVar("T")


class Provider(Generic[T], ABC):
    def __init__(self) -> None:
        self.__lock = Lock()
        self.__alias = ""
        self.__status = Status.IDLE

    def __str__(self) -> str:
        if self.__alias__:
            return f"{self.__alias__} ({type(self).__qualname__})"
        return type(self).__qualname__

    def __call__(self, *args: Any, **kwargs: Any) -> "CallableProvider":
        from diject.providers.interactions.callable import CallableProvider

        callable_provider = CallableProvider(self, *args, **kwargs)

        if self.__alias__:
            callable_provider.__alias__ = f"{self.__alias__}()"

        return callable_provider

    def __getattr__(self, name: str) -> "AttributeProvider":
        if name.startswith("__"):
            return super().__getattribute__(name)  # type: ignore[no-any-return]
        from diject.providers.interactions.attribute import AttributeProvider

        attribute_provider = AttributeProvider(self, name)

        if self.__alias__:
            attribute_provider.__alias__ = f"{self.__alias__}.{name}"

        return attribute_provider

    def __getitem__(self, key: Any) -> "ItemProvider":
        from diject.providers.interactions.item import ItemProvider

        item_provider = ItemProvider(self, key)

        if self.__alias__:
            item_provider.__alias__ = f"{self.__alias__}[{to_safe_string(key)}]"

        return item_provider

    @property
    def __lock__(self) -> Lock:
        return self.__lock

    @property
    def __alias__(self) -> str:
        return self.__alias

    @__alias__.setter
    def __alias__(self, alias: str) -> None:
        if not self.__alias:
            self.__alias = alias
            self.__propagate_alias__(alias)

    @property
    def __status__(self) -> Status:
        return self.__status

    @__status__.setter
    def __status__(self, status: Status) -> None:
        self.__status = status

    def __propagate_alias__(self, alias: str) -> None:
        for name, provider in self.__travers__():
            provider.__alias__ = f"{alias}.{name}"

    @abstractmethod
    def __travers__(self) -> Iterator[tuple[str, "Provider"]]:
        pass

    def __provide__(self) -> T:
        try:
            dependency = self.__provide_dependency__()
        except Exception:
            self.__status = Status.CORRUPTED
            raise
        else:
            self.__status = Status.RUNNING
            return dependency

    async def __aprovide__(self) -> T:
        try:
            dependency = await self.__aprovide_dependency__()
        except Exception:
            self.__status = Status.CORRUPTED
            raise
        else:
            self.__status = Status.RUNNING
            return dependency

    def __start__(self) -> None:
        with self.__lock:
            if self.__status is not Status.RUNNING:
                self.__start_dependency__()
                self.__status = Status.RUNNING

    async def __astart__(self) -> None:
        async with self.__lock:
            if self.__status is not Status.RUNNING:
                await self.__astart_dependency__()
                self.__status = Status.RUNNING

    def __shutdown__(self) -> None:
        with self.__lock:
            if self.__status is not Status.IDLE:
                self.__shutdown_dependency__()
                for name, provider in self.__travers__():
                    provider.__shutdown__()
                self.__status = Status.IDLE

    async def __ashutdown__(self) -> None:
        async with self.__lock:
            if self.__status is not Status.IDLE:
                await self.__ashutdown_dependency__()
                self.__status = Status.IDLE

    @abstractmethod
    def __provide_dependency__(self) -> T:
        pass

    @abstractmethod
    async def __aprovide_dependency__(self) -> T:
        pass

    def __start_dependency__(self) -> None:
        for name, provider in self.__travers__():
            provider.__start__()

    async def __astart_dependency__(self) -> None:
        await asyncio.gather(*(provider.__astart__() for name, provider in self.__travers__()))

    def __shutdown_dependency__(self) -> None:
        pass

    async def __ashutdown_dependency__(self) -> None:
        pass


class Pretender:
    def __repr__(self) -> str:
        return create_class_repr(self)


class PretenderBuilder(Generic[T], ABC):
    def __repr__(self) -> str:
        return create_class_repr(self)

    @property
    @abstractmethod
    def type(self) -> type[T]:
        pass
