from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T", contravariant=True)


@runtime_checkable
class ScopeProtocol(Protocol[T]):
    def __close__(self, data: T) -> None:
        pass

    async def __aclose__(self, data: T) -> None:
        pass
