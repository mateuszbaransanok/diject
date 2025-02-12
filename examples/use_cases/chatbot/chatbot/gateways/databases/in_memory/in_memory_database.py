from chatbot.core.database import Database
from chatbot.gateways.databases.in_memory.in_memory_repository import InMemoryRepository


class InMemoryDatabase(Database):
    def __init__(self) -> None:
        print("__init__", "InMemoryDatabase")

    def get_repository(self) -> InMemoryRepository:
        return InMemoryRepository()
