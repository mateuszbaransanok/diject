from collections.abc import Callable
from typing import Any, Generic, TypeVar

from diject.exceptions import DITypeError
from diject.providers.object import ObjectProvider
from diject.providers.provider import Provider
from diject.utils.string import create_class_repr

T = TypeVar("T")


class Partial(Generic[T]):
    def __init__(self, callable: Callable[..., T], *args: Any, **kwargs: Any) -> None:
        if isinstance(callable, ObjectProvider):
            callable = callable.__object__

        if isinstance(callable, Provider):
            raise DITypeError(f"Partial callable cannot be provider {callable}")

        if isinstance(callable, Partial):
            args = (*callable.args, *args)
            kwargs = {**callable.kwargs, **kwargs}
            callable = callable.callable

        self.__callable = callable
        self.__args = args
        self.__kwargs = kwargs

    def __repr__(self) -> str:
        return create_class_repr(self, self.__callable, *self.__args, **self.__kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        return self.__callable(*self.__args, *args, **{**self.__kwargs, **kwargs})

    @property
    def callable(self) -> Callable[..., T]:
        return self.__callable

    @property
    def args(self) -> tuple[Any, ...]:
        return self.__args

    @property
    def kwargs(self) -> dict[str, Any]:
        return self.__kwargs


class PartialPretender(Generic[T]):
    def __init__(self, callable: Callable[..., T]) -> None:
        self.__callable = callable

    def __repr__(self) -> str:
        return create_class_repr(self, self.__callable)

    def __call__(self, *args: Any, **kwargs: Any) -> Partial[T]:
        return Partial(self.__callable, *args, **kwargs)


class PartialPretenderBuilder(Generic[T]):
    def __repr__(self) -> str:
        return create_class_repr(self)

    def __getitem__(self, callable: Callable[..., T]) -> Callable[..., Partial[T]]:
        return PartialPretender(callable)
