from chatbot.core.llm_provider import LlmProvider
from chatbot.core.repository import Repository


class ChatService:
    def __init__(
        self,
        repository: Repository,
        model: LlmProvider,
        n_chunks: int,
    ) -> None:
        self._repository = repository
        self._model = model
        self._n_chunks = n_chunks
        print("__init__", "ChatService")

    def chat(self, message: str) -> str:
        chunks = self._repository.find_chunks(
            query=message,
            n_results=self._n_chunks,
        )
        text = "-".join(chunks) + "_" + message
        return self._model.complete(text)
