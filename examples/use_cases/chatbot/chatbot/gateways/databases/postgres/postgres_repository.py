from chatbot.core.repository import Repository
from chatbot.gateways.databases.postgres.postgres_database import PostgresDatabase


class PostgresRepository(Repository):
    def __init__(self, database: PostgresDatabase) -> None:
        self._database = database
        print("__init__", "PostgresRepository")

    def find_chunks(self, query: str, n_results: int) -> list[str]:
        return list(query)[:n_results]
