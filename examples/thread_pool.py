from concurrent.futures import ThreadPoolExecutor
from random import randint, random
from time import sleep
from typing import Iterator

import diject as di


def some_generator(a: str) -> Iterator[str]:
    string = f"{a}_{randint(10, 99)}"
    print(">before>", string)
    yield string
    print(">after >", string)


thread = di.Thread[some_generator](a="thread")


print("START".center(50, "="))


def main(i: int) -> None:
    sleep(random())
    print(f"  'thread({i})'", di.Provide[thread]())
    sleep(random())


with ThreadPoolExecutor(3) as executor:
    executor.map(main, (i for i in range(10)))

print("END".center(50, "="))
