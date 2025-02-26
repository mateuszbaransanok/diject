from typing import Protocol, runtime_checkable

from diject.utils.status import Status


@runtime_checkable
class StatusProtocol(Protocol):
    def __status__(self) -> Status:
        pass
