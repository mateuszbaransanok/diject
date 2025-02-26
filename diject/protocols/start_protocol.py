from typing import Protocol, runtime_checkable


@runtime_checkable
class StartProtocol(Protocol):
    def __start__(self) -> None:
        pass

    async def __astart__(self) -> None:
        pass
