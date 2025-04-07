import asyncio
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from diject.providers.provider import Provider
from diject.utils.state import State

T = TypeVar("T")


@dataclass
class ContextItem(Generic[T]):
    state: State[T] | None = None
    async_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def close(self) -> None:
        if self.state is not None:
            self.state.close()
            self.state = None

    async def aclose(self) -> None:
        if self.state is not None:
            await self.state.aclose()
            self.state = None


@dataclass
class ContextList(Generic[T]):
    states: list[State[T]] = field(default_factory=list)

    def close(self) -> None:
        for data in self.states:
            data.close()
        self.states.clear()

    async def aclose(self) -> None:
        await asyncio.gather(*(data.aclose() for data in self.states))
        self.states.clear()


@dataclass
class Context(Generic[T]):
    store: dict[Provider, ContextItem[T] | ContextList[T]] = field(default_factory=dict)
    async_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def close(self) -> None:
        for data in self.store.values():
            data.close()
        self.store.clear()

    async def aclose(self) -> None:
        await asyncio.gather(*(data.aclose() for data in self.store.values()))
        self.store.clear()
