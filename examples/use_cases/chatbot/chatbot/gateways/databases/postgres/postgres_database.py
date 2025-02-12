from chatbot.core.database import Database
from chatbot.gateways.databases.postgres.postgres_repository import PostgresRepository


class PostgresDatabase(Database):
    def __init__(self, url: str) -> None:
        self._url = url
        print("__init__", "PostgresDatabase")

    def get_repository(self) -> PostgresRepository:
        return PostgresRepository()
