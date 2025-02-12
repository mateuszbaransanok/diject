from abc import ABC, abstractmethod

from chatbot.core.repository import Repository


class Database(ABC):
    @abstractmethod
    def get_repository(self) -> Repository:
        pass
