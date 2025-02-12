from chatbot.core.repository import Repository


class InMemoryRepository(Repository):
    def __init__(self) -> None:
        print("__init__", "InMemoryRepository")

    def find_chunks(self, query: str, n_results: int) -> list[str]:
        return list(reversed(list(query)[:n_results]))
