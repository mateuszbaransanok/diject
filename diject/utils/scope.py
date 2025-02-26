from collections.abc import Iterator
from typing import Any, Generic, TypeVar

from diject.protocols.scope_protocol import ScopeProtocol

T = TypeVar("T")


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
