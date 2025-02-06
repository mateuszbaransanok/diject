from random import randint
from typing import Annotated

import diject as di


def some_function(a: str) -> str:
    return f"{a}_{randint(10, 99)}"


factory = di.Factory[some_function](a=di.Scoped[some_function](a="scope"))


@di.Provide
def main(
    normal: str,
    pos_dep: Annotated[str, factory],
    /,
    kw_dep: Annotated[str, factory],
    default_dep: str = factory,
) -> None:
    print("normal:", normal)
    print("pos_dep:", pos_dep)
    print("kw_dep:", kw_dep)
    print("default_dep:", default_dep)
    print()


print("START SCRIPT".center(50, "="), end="\n\n")

for _ in range(2):
    main("normal")

print("END".center(50, "="))
