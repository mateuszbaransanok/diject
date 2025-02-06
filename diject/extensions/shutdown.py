from typing import Protocol, runtime_checkable


@runtime_checkable
class ShutdownProtocol(Protocol):
    def __shutdown__(self) -> None:
        pass

    async def __ashutdown__(self) -> None:
        pass
