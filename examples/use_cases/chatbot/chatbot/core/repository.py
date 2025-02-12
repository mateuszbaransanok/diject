from abc import ABC, abstractmethod


class Repository(ABC):
    @abstractmethod
    def find_chunks(self, query: str, n_results: int) -> list[str]:
        pass
