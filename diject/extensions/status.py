from enum import StrEnum
from typing import Protocol, runtime_checkable


class Status(StrEnum):
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"


@runtime_checkable
class StatusProtocol(Protocol):
    def __status__(self) -> Status:
        pass
