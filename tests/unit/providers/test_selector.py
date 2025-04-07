from unittest.mock import Mock

import diject as di


def test_selector() -> None:
    selector_provider = di.Selector["opt_a"](
        opt_a="A",
        opt_b="B",
    )

    actual = di.provide(selector_provider)

    assert actual == "A"


def test_selector__start() -> None:
    mock_a = Mock()
    mock_b = Mock()

    class Container(di.Container):
        selector_provider = di.Selector["opt_a"](
            opt_a=di.Singleton[mock_a](),
            opt_b=di.Singleton[mock_b](),
        )

    Container.start()

    mock_a.assert_called()
    mock_b.assert_not_called()
