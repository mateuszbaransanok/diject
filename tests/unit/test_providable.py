from typing import Annotated, TypeAlias

import pytest

import diject as di

factory1: TypeAlias = type


class MockClass:
    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"{type(self).__qualname__}({self.value})"


class MockContainer(di.Container):
    factory1 = di.Factory[MockClass](value="factory1")
    factory2 = di.Factory[MockClass](value="factory2")


def test_providable__inject_by_register() -> None:
    di.Provide[MockContainer.factory1].register()

    @di.inject
    def func(mock: MockClass) -> str:
        return str(mock)

    value = func()

    assert value == "MockClass(factory1)"


def test_providable__inject_by_register__raise_error_on_duplicated() -> None:
    di.Provide[MockContainer].register()

    @di.inject
    def func(mock: MockClass) -> str:
        return str(mock)

    with pytest.raises(TypeError):
        func()


def test_providable__inject_by_annotated_register() -> None:
    di.Provide[MockContainer].register()

    @di.inject
    def func(mock: Annotated[MockClass, "factory1"]) -> str:
        return str(mock)

    value = func()

    assert value == "MockClass(factory1)"


def test_providable__inject_by_annotated_explicit() -> None:
    @di.inject
    def func(mock: Annotated[MockClass, MockContainer.factory1]) -> str:
        return str(mock)

    value = func()

    assert value == "MockClass(factory1)"


def test_providable__inject_by_explicit_default() -> None:
    @di.inject
    def func(mock: MockClass = MockContainer.factory1) -> str:
        return str(mock)

    value = func()

    assert value == "MockClass(factory1)"


def test_providable__inject_with_call_override() -> None:
    @di.inject
    def func(mock: MockClass = MockContainer.factory1) -> str:
        return str(mock)

    value = func(MockContainer.factory2)

    assert value == "MockClass(factory2)"


def test_providable__inject_with_string_annotation_registered__raise_error() -> None:
    di.Provide[MockContainer].register()

    @di.inject
    def func(mock: "factory1") -> str:
        return str(mock)

    with pytest.raises(TypeError):
        func()
