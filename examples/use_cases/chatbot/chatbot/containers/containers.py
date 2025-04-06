import diject as di
from chatbot.core.chat_service import ChatService
from chatbot.core.repository import Repository
from chatbot.gateways.databases.in_memory.in_memory_database import InMemoryDatabase
from chatbot.gateways.databases.in_memory.in_memory_repository import InMemoryRepository
from chatbot.gateways.databases.postgres.postgres_database import PostgresDatabase
from chatbot.gateways.databases.postgres.postgres_repository import PostgresRepository
from chatbot.gateways.llm_providers.azure_llm_provider import AzureLlmProvider


class Databases(di.Container):
    in_memory = di.Singleton[InMemoryDatabase]()

    postgres = di.Singleton[PostgresDatabase](
        url="<url>",
    )


class LlmProviders(di.Container):
    azure = di.Singleton[AzureLlmProvider](
        api_key="<secret>",
    )


class Repositories(di.Container):
    with di.Selector["postgres"] as GroupSelector:
        repository = GroupSelector[Repository]()

    with GroupSelector == "in_memory" as Option:
        Option[repository] = di.Singleton[InMemoryRepository]()

    with GroupSelector == "postgres" as Option:
        Option[repository] = di.Scoped[PostgresRepository]()


class Services(di.Container):
    chat_service = di.Transient[ChatService](
        repository=Repositories.repository,
        model=LlmProviders.azure,
        n_chunks=5,
    )
