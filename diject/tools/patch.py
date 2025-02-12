import functools
import inspect
from collections.abc import Callable
from types import TracebackType
from typing import Any, TypeVar
from unittest import mock

from diject.exceptions import DITypeError
from diject.providers.provider import Provider

T = TypeVar("T")
TProvider = TypeVar("TProvider", bound=Provider)


class Patch:
    def __init__(
        self,
        provider: Any,
        *,
        return_value: Any = mock.DEFAULT,
        side_effect: Any = None,
        **kwargs: mock.Mock,
    ) -> None:
        if not isinstance(provider, Provider):
            raise DITypeError(f"Argument 'provider' must be Provider type, not {type(provider)}")

        self._provider = provider
        self._kwargs = kwargs

        if "__provide__" not in self._kwargs:
            self._kwargs["__provide__"] = mock.Mock(
                return_value=return_value,
                side_effect=side_effect,
            )

        if "__aprovide__" not in self._kwargs:
            self._kwargs["__aprovide__"] = mock.AsyncMock(
                return_value=return_value,
                side_effect=side_effect,
            )

        if "__travers__" not in self._kwargs:
            self._kwargs["__travers__"] = mock.Mock(return_value=iter(()))

        for kw in ("__status__", "__reset__"):
            if kw not in self._kwargs:
                self._kwargs[kw] = mock.Mock()

        for kw in ("__areset__",):
            if kw not in self._kwargs:
                self._kwargs[kw] = mock.AsyncMock()

        self._origins: dict[str, Callable] = {}

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with Patch(self._provider, **self._kwargs):
                result = func(*args, **kwargs)
            return result

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with Patch(self._provider, **self._kwargs):
                result = await func(*args, **kwargs)
            return result

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    def __enter__(self) -> None:
        for attr, mock_obj in self._kwargs.items():
            if hasattr(self._provider, attr):
                self._origins[attr] = getattr(self._provider, attr)
                setattr(self._provider, attr, mock_obj)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        for attr, origin in self._origins.items():
            setattr(self._provider, attr, origin)
