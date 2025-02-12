from enum import StrEnum


class Status(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    CORRUPTED = "corrupted"
