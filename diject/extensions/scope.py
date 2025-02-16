from collections.abc import Iterator
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T", contravariant=True)


@runtime_checkable
class ScopeProtocol(Protocol[T]):
    def __close__(self, data: T) -> None:
        pass

    async def __aclose__(self, data: T) -> None:
        pass


class Scope(Generic[T]):
    def __init__(self) -> None:
        self.__scopes: dict[ScopeProtocol[T], Any] = {}

    def __setitem__(self, scope: ScopeProtocol[T], value: Any) -> None:
        self.__scopes[scope] = value

    def __getitem__(self, scope: ScopeProtocol[T]) -> Any:
        return self.__scopes[scope]

    def __contains__(self, scope: ScopeProtocol[T]) -> bool:
        return scope in self.__scopes

    def items(self) -> Iterator[tuple[ScopeProtocol[T], T]]:
        yield from self.__scopes.items()
