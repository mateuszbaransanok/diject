from enum import StrEnum


class Status(StrEnum):
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"
