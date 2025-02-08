from typing import Protocol, runtime_checkable


@runtime_checkable
class ResetProtocol(Protocol):
    def __reset__(self) -> None:
        pass

    async def __areset__(self) -> None:
        pass
