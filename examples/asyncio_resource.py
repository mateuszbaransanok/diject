import asyncio
from random import randint, random
from typing import AsyncIterator

import diject as di


async def some_generator(a: str) -> AsyncIterator[str]:
    string = f"{a}_{randint(10, 99)}"
    print(">before sleep>", string)
    await asyncio.sleep(1 + random())
    print(">before yield>", string)
    yield string
    print(">after  yield>", string)
    await asyncio.sleep(1 + random())
    print(">after  sleep>", string)


class MainContainer(di.Container):
    resource_a = di.Resource[some_generator](a="resource_a")
    resource_b = di.Resource[some_generator](a="resource_b")


async def get_resource_a() -> str:
    print("  before sleep get_resource_a")
    await asyncio.sleep(0.1)
    print("  before return get_resource_a")
    return await di.Provide[MainContainer.resource_a]


async def main() -> None:
    container_dependency = di.Provide[MainContainer]

    *_, resource_a_value = await asyncio.gather(
        *(container_dependency.astart() for _ in range(10)),
        get_resource_a(),
    )

    print("  RESULT:", resource_a_value)

    await asyncio.gather(
        *(container_dependency.ashutdown() for _ in range(10)),
    )


asyncio.run(main())
