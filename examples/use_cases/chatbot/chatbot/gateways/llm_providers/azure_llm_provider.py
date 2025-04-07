from chatbot.core.llm_provider import LlmProvider


class AzureLlmProvider(LlmProvider):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        print("__init__", "AzureLlmProvider")

    def complete(self, text: str) -> str:
        return text.upper()
