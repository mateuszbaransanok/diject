import asyncio
import functools
import inspect
from collections.abc import Awaitable, Callable
from contextvars import ContextVar, Token
from types import TracebackType
from typing import Annotated, Any, ParamSpec, TypeVar, get_args, get_origin, overload

from diject.exceptions import DIErrorWrapper
from diject.providers.provider import Provider
from diject.utils.context import Context

T = TypeVar("T")
P = ParamSpec("P")


class Injector:
    _CONTEXT: ContextVar["Context | None"] = ContextVar("DIJECT_CONTEXT", default=None)

    def __init__(self, *, reuse_context: bool = True, close_context: bool = True) -> None:
        self._reuse_context = reuse_context
        self._close_context = close_context
        self._context: Context | None = None
        self._token: Token | None = None

    @overload
    def __call__(self, func: Callable[P, T], /) -> Callable[P, T] | Callable[..., T]:
        pass

    @overload
    def __call__(
        self,
        func: Callable[P, Awaitable[T]],
        /,
    ) -> Callable[P, Awaitable[T]] | Callable[..., Awaitable[T]]:
        pass

    def __call__(self, func: Any, /) -> Any:
        signature = inspect.signature(func)

        def prepare_arguments(
            *args: Any,
            **kwargs: Any,
        ) -> tuple[inspect.BoundArguments, dict[str, Provider]]:
            bound_params = signature.bind_partial(*args, **kwargs)

            providers = {}
            for param in signature.parameters.values():
                if param.name in bound_params.arguments:
                    if isinstance(value := bound_params.arguments[param.name], Provider):
                        providers[param.name] = value
                elif param.default is not param.empty:
                    if isinstance(default := param.default, Provider):
                        providers[param.name] = default
                elif get_origin(param.annotation) is Annotated:
                    annot_args = get_args(param.annotation)
                    if len(annot_args) == 2:
                        _, annot_meta = annot_args
                        if isinstance(annot_meta, Provider):
                            providers[param.name] = annot_meta

            return bound_params, providers

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            bound_params, providers = prepare_arguments(*args, **kwargs)

            with Injector():
                try:
                    for name, value in providers.items():
                        bound_params.arguments[name] = value.__provide__()
                except DIErrorWrapper as exc:
                    raise exc.origin from exc.caused_by

                signature.bind(*bound_params.args, **bound_params.kwargs)

                return func(*bound_params.args, **bound_params.kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            bound_params, providers = prepare_arguments(*args, **kwargs)

            with Injector():
                try:
                    values = await asyncio.gather(*(v.__aprovide__() for v in providers.values()))
                except DIErrorWrapper as exc:
                    raise exc.origin from exc.caused_by

                for name, value in zip(providers, values, strict=True):
                    bound_params.arguments[name] = value

                signature.bind(*bound_params.args, **bound_params.kwargs)

                return await func(*bound_params.args, **bound_params.kwargs)

        @functools.wraps(func)
        def sync_generator(*args: Any, **kwargs: Any) -> Any:
            bound_params, providers = prepare_arguments(*args, **kwargs)

            with Injector():
                try:
                    for name, value in providers.items():
                        bound_params.arguments[name] = value.__provide__()
                except DIErrorWrapper as exc:
                    raise exc.origin from exc.caused_by

                signature.bind(*bound_params.args, **bound_params.kwargs)

                yield from func(*bound_params.args, **bound_params.kwargs)

        @functools.wraps(func)
        async def async_generator(*args: Any, **kwargs: Any) -> Any:
            bound_params, providers = prepare_arguments(*args, **kwargs)

            with Injector():
                try:
                    values = await asyncio.gather(*(v.__aprovide__() for v in providers.values()))
                except DIErrorWrapper as exc:
                    raise exc.origin from exc.caused_by

                for name, value in zip(providers, values, strict=True):
                    bound_params.arguments[name] = value

                signature.bind(*bound_params.args, **bound_params.kwargs)

                async for result in func(*bound_params.args, **bound_params.kwargs):
                    yield result

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        elif inspect.isasyncgenfunction(func):
            return async_generator
        elif inspect.isgeneratorfunction(func):
            return sync_generator
        else:
            return sync_wrapper

    def __enter__(self) -> Context | None:
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    async def __aenter__(self) -> Context | None:
        return self.open()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    @classmethod
    def get_context(cls) -> Context | None:
        return cls._CONTEXT.get()

    def open(self) -> Context | None:
        if not (self._reuse_context and self._CONTEXT.get()):
            self._context = Context()
            self._token = self._CONTEXT.set(self._context)

        return self._context

    def close(self) -> None:
        if self._context and self._close_context:
            self._context.close()
            self._context = None

        if self._token:
            self._CONTEXT.reset(self._token)
            self._token = None

    async def aclose(self) -> None:
        if self._context and self._close_context:
            await self._context.aclose()
            self._context = None

        if self._token:
            self._CONTEXT.reset(self._token)
            self._token = None
