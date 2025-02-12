import diject as di


def some_function(a: str, /, b: str, c: str, n: int) -> str:
    return f"{a=},{b=},{c=},{n=}"


def test_partial() -> None:
    partial = di.Partial[some_function]("a", b="b")
    transient1 = di.Transient[partial](c="c1", n=1)
    transient2 = di.Transient[partial](c="c2", n=2)

    actual1 = di.provide(transient1)
    actual2 = di.provide(transient2)

    assert actual1 == "a='a',b='b',c='c1',n=1"
    assert actual2 == "a='a',b='b',c='c2',n=2"


def test_partial__nested() -> None:
    partial = di.Partial[some_function]("a", b="b")
    partial_child = di.Partial[partial](c="c")
    transient1 = di.Transient[partial_child](n=1)
    transient2 = di.Transient[partial_child](n=2)

    actual1 = di.provide(transient1)
    actual2 = di.provide(transient2)

    assert actual1 == "a='a',b='b',c='c',n=1"
    assert actual2 == "a='a',b='b',c='c',n=2"
