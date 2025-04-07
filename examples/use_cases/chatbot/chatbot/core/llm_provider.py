from abc import ABC, abstractmethod


class LlmProvider(ABC):
    @abstractmethod
    def complete(self, text: str) -> str:
        pass
