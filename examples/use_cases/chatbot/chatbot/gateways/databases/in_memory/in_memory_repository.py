from chatbot.core.repository import Repository
from chatbot.gateways.databases.in_memory.in_memory_database import InMemoryDatabase


class InMemoryRepository(Repository):
    def __init__(self, database: InMemoryDatabase) -> None:
        self._database = database
        print("__init__", "InMemoryRepository")

    def find_chunks(self, query: str, n_results: int) -> list[str]:
        return list(reversed(list(query)[:n_results]))
