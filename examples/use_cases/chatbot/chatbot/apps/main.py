from chatbot.containers.containers import Services
from chatbot.core.chat_service import ChatService

import diject as di


@di.inject
def main(service: ChatService = Services.chat_service) -> str:
    output = service.chat("Hello world!")
    print("pre", output)
    service = di.provide(Services.chat_service)
    output = service.chat("Hello world!")
    return output


print(main())
print()
print(main())
