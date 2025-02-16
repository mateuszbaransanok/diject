import asyncio
import functools
from collections.abc import Callable
from types import TracebackType
from typing import Any, Generic, TypeVar, overload
from unittest import mock

from diject.providers.container import Container
from diject.providers.provider import Provider
from diject.utils.exceptions import DINameError, DITypeError
from diject.utils.repr import create_class_repr

T = TypeVar("T")
TProvider = TypeVar("TProvider", bound=Provider[Any])
TContainer = TypeVar("TContainer", bound=Container)


class ProviderMock:
    def __init__(
        self,
        provider: Provider[Any],
        target: str = "",
        *,
        return_value: Any = mock.DEFAULT,
        side_effect: Any = None,
        **kwargs: mock.Mock | mock.AsyncMock,
    ) -> None:
        if not isinstance(provider, Provider):
            raise DITypeError(f"Argument 'provider' must be Provider type, not {type(provider)}")

        self.__provider = self.__get_provider_by_target(provider, target) if target else provider

        if "__provide__" not in kwargs:
            kwargs["__provide__"] = mock.Mock(
                return_value=return_value,
                side_effect=side_effect,
            )

        if "__aprovide__" not in kwargs:
            kwargs["__aprovide__"] = mock.AsyncMock(
                return_value=return_value,
                side_effect=side_effect,
            )

        if "__travers__" not in kwargs:
            kwargs["__travers__"] = mock.Mock(return_value=iter(()))

        if "__atravers__" not in kwargs:
            kwargs["__atravers__"] = mock.AsyncMock(return_value=iter(()))

        for kw in ("__status__", "__start__", "__shutdown__", "__reset__"):
            if kw not in kwargs:
                kwargs[kw] = mock.Mock()

        for kw in ("__astart__", "__ashutdown__", "__areset__"):
            if kw not in kwargs:
                kwargs[kw] = mock.AsyncMock()

        self.__origins = {}

        for attr, mock_obj in kwargs.items():
            if hasattr(self.__provider, attr):
                self.__origins[attr] = getattr(self.__provider, attr)
                setattr(self.__provider, attr, mock_obj)

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.restore()

    def restore(self) -> None:
        for attr, origin in self.__origins.items():
            setattr(self.__provider, attr, origin)

    @staticmethod
    def __get_provider_by_target(provider: Provider[Any], target: str) -> Provider[Any]:
        for key in target.split("."):
            for name, sub_provider in provider.__travers__():
                if key == name:
                    provider = sub_provider
                    break
            else:
                raise DINameError(f"Name '{key}' not in {provider}")

        return provider


class ProviderMockPartial(Generic[T]):
    def __init__(self, provider: Provider[T], target: str) -> None:
        self.__provider = provider
        self.__target = target

    def __repr__(self) -> str:
        return create_class_repr(self, self.__provider)

    def __call__(
        self,
        *,
        return_value: Any = mock.DEFAULT,
        side_effect: Any = None,
        **kwargs: mock.Mock | mock.AsyncMock,
    ) -> ProviderMock:
        return ProviderMock(
            provider=self.__provider,
            target=self.__target,
            return_value=return_value,
            side_effect=side_effect,
            **kwargs,
        )


class ProviderMockBuilder:
    def __repr__(self) -> str:
        return create_class_repr(self)

    @overload
    def __getitem__(
        self,
        provider: type[TContainer] | tuple[type[TContainer], str],
    ) -> ProviderMockPartial[T]:
        pass

    @overload
    def __getitem__(
        self,
        provider: Provider[T] | tuple[Provider[T], str],
    ) -> ProviderMockPartial[T]:
        pass

    @overload
    def __getitem__(self, provider: T | tuple[T, str]) -> ProviderMockPartial[T]:
        pass

    def __getitem__(self, provider: Any) -> Any:
        if isinstance(provider, tuple):
            provider, target = provider
        else:
            target = ""

        if isinstance(provider, type) and issubclass(provider, Container):
            provider = provider()

        return ProviderMockPartial(provider, target)


def patch(
    provider: Any,
    target: str = "",
    *,
    return_value: Any = mock.DEFAULT,
    side_effect: Any = None,
    **mock_kwargs: mock.Mock | mock.AsyncMock,
) -> Callable[..., Any]:
    if isinstance(provider, type) and issubclass(provider, Container):
        provider = provider()

    if not isinstance(provider, Provider):
        raise DITypeError(f"Argument 'provider' must be Provider type, not {type(provider)}")

    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with ProviderMock(
                provider=provider,
                target=target,
                return_value=return_value,
                side_effect=side_effect,
                **mock_kwargs,
            ):
                result = func(*args, **kwargs)
            return result

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with ProviderMock(
                provider=provider,
                target=target,
                return_value=return_value,
                side_effect=side_effect,
                **mock_kwargs,
            ):
                result = await func(*args, **kwargs)
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return wrapper
