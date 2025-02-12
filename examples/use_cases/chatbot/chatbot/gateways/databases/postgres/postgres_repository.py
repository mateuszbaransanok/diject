from chatbot.core.repository import Repository


class PostgresRepository(Repository):
    def __init__(self) -> None:
        print("__init__", "PostgresRepository")

    def find_chunks(self, query: str, n_results: int) -> list[str]:
        return list(query)[:n_results]
