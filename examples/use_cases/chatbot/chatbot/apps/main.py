import diject as di
from chatbot.containers.containers import Services
from chatbot.core.chat_service import ChatService


@di.inject
def main(service: ChatService = Services.chat_service) -> str:
    output = service.chat("Hello world!")
    print("pre", output)
    service = di.provide(Services.chat_service)
    return service.chat("Hello world!")


print(main())
print()
print(main())
