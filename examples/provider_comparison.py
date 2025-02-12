from collections.abc import Iterator
from random import randint

import diject as di


def some_generator(a: str) -> Iterator[str]:
    string = f"{a}_{randint(10, 99)}"
    print(">before>", string)
    yield string
    print(">after >", string)


class MainContainer(di.Container):
    singleton = di.Singleton[some_generator](a="singleton")
    scoped = di.Scoped[some_generator](a="scoped")
    transient = di.Transient[some_generator](a="transient")


print("START SCRIPT".center(50, "="))
MainContainer.start()

print("START LOOP".center(50, "="))
for _ in range(2):
    print("START ITERATION".center(50, "-"))
    with di.inject():
        for _ in range(2):
            print("  'singleton'", di.provide(MainContainer.singleton))
            print("  'scoped'", di.provide(MainContainer.scoped))
            print("  'transient'", di.provide(MainContainer.transient))
            print()

    print("END ITERATION".center(50, "-"))

print("END LOOP".center(50, "="))

MainContainer.shutdown()
print("END SCRIPT".center(50, "="))
