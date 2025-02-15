from collections.abc import Iterator
from random import randint

import diject as di


def some_function(a: str) -> str:
    return f"{a}_{randint(10, 99)}"


def some_generator(a: str) -> Iterator[str]:
    string = f"{a}_{randint(10, 99)}"
    print(">before>", string)
    yield string
    print(">after >", string)


class MainContainer(di.Container):
    factory = di.Factory[some_function](a="factory")
    singleton = di.Singleton[some_generator](a="singleton")
    resource = di.Resource[some_generator](a="resource")
    scoped = di.Scoped[some_generator](a="scoped")
    transient = di.Transient[some_generator](a="transient")
    thread = di.Thread[some_generator](a="thread")


print("START SCRIPT".center(50, "="))
di.Provide[MainContainer].start()

print("START LOOP".center(50, "="))
for _ in range(2):
    print("START ITERATION".center(50, "-"))
    with di.Provide[MainContainer] as container:
        for _ in range(2):
            print("  'factory'", container.factory)
            print("  'singleton'", container.singleton)
            print("  'resource'", container.resource)
            print("  'scoped'", container.scoped)
            print("  'transient'", container.transient)
            print("  'thread'", container.thread)
            print()

    print("END ITERATION".center(50, "-"))

print("END LOOP".center(50, "="))

di.Provide[MainContainer].shutdown()
print("END SCRIPT".center(50, "="))
