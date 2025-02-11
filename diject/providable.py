import asyncio
import functools
import inspect
from types import TracebackType
from typing import (
    Annotated,
    Any,
    AsyncIterator,
    Callable,
    Final,
    Generator,
    Generic,
    Iterator,
    TypeVar,
    cast,
    get_args,
    get_origin,
    overload,
)

from diject.extensions.reset import ResetProtocol
from diject.extensions.scope import Scope
from diject.extensions.start import StartProtocol
from diject.extensions.status import Status, StatusProtocol
from diject.providers.container import Container
from diject.providers.pretenders.selector import SelectorProvider
from diject.providers.provider import Provider
from diject.utils.empty import EMPTY
from diject.utils.exceptions import DIScopeError, DITypeError
from diject.utils.lock import Lock
from diject.utils.repr import create_class_repr

T = TypeVar("T")
TProvider = TypeVar("TProvider", bound=Provider[Any])
TContainer = TypeVar("TContainer", bound=Container)


class Providable(Generic[T]):
    def __init__(self, provider: Provider[T]) -> None:
        if not isinstance(provider, Provider):
            raise DITypeError(f"Argument 'provider' must be Provider type, not {type(provider)}")

        self.__lock = Lock()
        self.__provider = provider
        self.__scope: Scope | None = None

    def __repr__(self) -> str:
        return create_class_repr(self, self.__provider)

    def __call__(self) -> T:
        return self.__provider.__provide__()

    def __await__(self) -> Generator[Any, None, T]:
        return self.__provider.__aprovide__().__await__()

    def __enter__(self) -> T:
        self.__lock.acquire()

        if self.__scope is not None:
            raise DIScopeError(f"{type(self).__name__}'s scope has already been created")

        self.__scope = Scope()

        return self.__provider.__provide__(self.__scope)

    async def __aenter__(self) -> T:
        await self.__lock.aacquire()

        if self.__scope is not None:
            raise DIScopeError(f"{type(self).__name__}'s scope has already been created")

        self.__scope = Scope()

        return await self.__provider.__aprovide__(self.__scope)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.__scope is None:
            raise DIScopeError(f"{type(self).__name__}'s scope has not been created yet")

        for provider, data in self.__scope.items():
            provider.__reset_scope_data__(data)

        self.__scope = None
        self.__lock.release()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.__scope is None:
            raise DIScopeError(f"{type(self).__name__}'s scope has not been created yet")

        await asyncio.gather(*(p.__areset_scope_data__(data) for p, data in self.__scope.items()))

        self.__scope = None
        await self.__lock.arelease()

    @property
    def provider(self) -> Provider[T]:
        return self.__provider

    def status(self) -> Status:
        if isinstance(self.__provider, StatusProtocol):
            return self.__provider.__status__()
        raise DITypeError("Provider do not have status")

    @overload
    def travers(
        self,
        types: type[TProvider] | tuple[type[TProvider], ...],
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> Iterator[tuple[str, TProvider]]:
        pass

    @overload
    def travers(
        self,
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> Iterator[tuple[str, TProvider]]:
        pass

    def travers(
        self,
        types: type[TProvider] | tuple[type[TProvider], ...] | None = None,
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> Any:
        yield from self.__travers(
            provider=self.__provider,
            types=types or cast(type[TProvider], Provider),
            recursive=recursive,
            only_public=only_public,
            only_selected=only_selected,
            cache=set(),
        )

    @overload
    async def atravers(
        self,
        types: type[TProvider] | tuple[type[TProvider], ...],
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> AsyncIterator[tuple[str, TProvider]]:
        pass

    @overload
    async def atravers(
        self,
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> AsyncIterator[tuple[str, TProvider]]:
        pass

    async def atravers(
        self,
        types: type[TProvider] | tuple[type[TProvider], ...] | None = None,
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> Any:
        async for sub_name, sub_provider in self.__atravers(
            provider=self.__provider,
            types=types or cast(type[TProvider], Provider),
            recursive=recursive,
            only_public=only_public,
            only_selected=only_selected,
            cache=set(),
        ):
            yield sub_name, sub_provider

    def start(self) -> None:
        self.__start(
            provider=self.__provider,
            cache=set(),
        )

    async def astart(self) -> None:
        await self.__astart(
            provider=self.__provider,
            cache=set(),
        )

    def shutdown(self) -> None:
        self.__reset(
            provider=self.__provider,
            recursive=True,
            cache=set(),
        )

    async def ashutdown(self) -> None:
        await self.__areset(
            provider=self.__provider,
            recursive=True,
            cache=set(),
        )

    def reset(self) -> None:
        self.__reset(
            provider=self.__provider,
            recursive=False,
            cache=set(),
        )

    async def areset(self) -> None:
        await self.__areset(
            provider=self.__provider,
            recursive=False,
            cache=set(),
        )

    def restart(self) -> None:
        self.reset()
        self.start()

    async def arestart(self) -> None:
        await self.areset()
        await self.astart()

    def __start(
        self,
        provider: Provider[Any],
        cache: set[Provider[Any]],
    ) -> None:
        for sub_name, sub_provider in self.__travers(
            provider=provider,
            types=Provider,
            only_public=True,
            only_selected=True,
            recursive=False,
            cache=cache,
        ):
            self.__start(
                provider=sub_provider,
                cache=cache,
            )

        if isinstance(provider, StartProtocol):
            provider.__start__()

    async def __astart(
        self,
        provider: Provider[Any],
        cache: set[Provider[Any]],
    ) -> None:
        await asyncio.gather(
            *[
                self.__astart(
                    provider=sub_provider,
                    cache=cache,
                )
                async for sub_name, sub_provider in self.__atravers(
                    provider=provider,
                    types=Provider,
                    only_public=True,
                    only_selected=True,
                    recursive=False,
                    cache=cache,
                )
            ]
        )

        if isinstance(provider, StartProtocol):
            await provider.__astart__()

    def __reset(
        self,
        provider: Provider[Any],
        recursive: bool,
        cache: set[Provider[Any]],
    ) -> None:
        if recursive:
            for sub_name, sub_provider in self.__travers(
                provider=provider,
                types=Provider,
                only_public=True,
                only_selected=True,
                recursive=False,
                cache=cache,
            ):
                self.__reset(
                    provider=sub_provider,
                    recursive=recursive,
                    cache=cache,
                )

        if isinstance(provider, ResetProtocol):
            provider.__reset__()

    async def __areset(
        self,
        provider: Provider[Any],
        recursive: bool,
        cache: set[Provider[Any]],
    ) -> None:
        if recursive:
            await asyncio.gather(
                *[
                    self.__areset(
                        provider=sub_provider,
                        recursive=recursive,
                        cache=cache,
                    )
                    async for sub_name, sub_provider in self.__atravers(
                        provider=provider,
                        types=Provider,
                        only_public=True,
                        only_selected=True,
                        recursive=False,
                        cache=cache,
                    )
                ]
            )

        if isinstance(provider, ResetProtocol):
            await provider.__areset__()

    def __travers(
        self,
        provider: Provider[Any],
        types: type[TProvider] | tuple[type[TProvider], ...],
        recursive: bool,
        only_public: bool,
        only_selected: bool,
        cache: set[Provider[Any]],
    ) -> Iterator[tuple[str, TProvider]]:
        if isinstance(provider, SelectorProvider) and only_selected:
            for sub_name, sub_provider in provider.__travers__(only_selected=only_selected):
                yield from self.__travers_provider(
                    name=sub_name,
                    provider=sub_provider,
                    types=types,
                    recursive=recursive,
                    only_public=only_public,
                    only_selected=only_selected,
                    cache=cache,
                )
        else:
            for sub_name, sub_provider in provider.__travers__():
                if not (only_public and sub_name.startswith("_")):
                    yield from self.__travers_provider(
                        name=sub_name,
                        provider=sub_provider,
                        types=types,
                        recursive=recursive,
                        only_public=only_public,
                        only_selected=only_selected,
                        cache=cache,
                    )

    async def __atravers(
        self,
        provider: Provider[Any],
        types: type[TProvider] | tuple[type[TProvider], ...],
        recursive: bool,
        only_public: bool,
        only_selected: bool,
        cache: set[Provider[Any]],
    ) -> AsyncIterator[tuple[str, TProvider]]:
        if isinstance(provider, SelectorProvider) and only_selected:
            async for sub_name, sub_provider in provider.__atravers__(only_selected=only_selected):
                async for _sub_name, _sub_provider in self.__atravers_provider(
                    name=sub_name,
                    provider=sub_provider,
                    types=types,
                    recursive=recursive,
                    only_public=only_public,
                    only_selected=only_selected,
                    cache=cache,
                ):
                    yield _sub_name, _sub_provider
        else:
            for sub_name, sub_provider in provider.__travers__():
                if not (only_public and sub_name.startswith("_")):
                    async for _sub_name, _sub_provider in self.__atravers_provider(
                        name=sub_name,
                        provider=sub_provider,
                        types=types,
                        recursive=recursive,
                        only_public=only_public,
                        only_selected=only_selected,
                        cache=cache,
                    ):
                        yield _sub_name, _sub_provider

    def __travers_provider(
        self,
        name: str,
        provider: Provider[Any],
        types: type[TProvider] | tuple[type[TProvider], ...],
        recursive: bool,
        only_public: bool,
        only_selected: bool,
        cache: set[Provider[Any]],
    ) -> Iterator[tuple[str, TProvider]]:
        if provider not in cache:
            cache.add(provider)

            if isinstance(provider, types):
                yield name, cast(TProvider, provider)

            if recursive:
                yield from self.__travers(
                    provider=provider,
                    types=types,
                    recursive=recursive,
                    only_public=only_public,
                    only_selected=only_selected,
                    cache=cache,
                )

    async def __atravers_provider(
        self,
        name: str,
        provider: Provider[Any],
        types: type[TProvider] | tuple[type[TProvider], ...],
        recursive: bool,
        only_public: bool,
        only_selected: bool,
        cache: set[Provider[Any]],
    ) -> AsyncIterator[tuple[str, TProvider]]:
        if provider not in cache:
            cache.add(provider)

            if isinstance(provider, types):
                yield name, cast(TProvider, provider)

            if recursive:
                async for sub_name, sub_provider in self.__atravers(
                    provider=provider,
                    types=types,
                    recursive=recursive,
                    only_public=only_public,
                    only_selected=only_selected,
                    cache=cache,
                ):
                    yield sub_name, sub_provider


class ProvidableBuilder:
    def __repr__(self) -> str:
        return create_class_repr(self)

    @overload
    def __getitem__(self, provider: type[TContainer]) -> Providable[TContainer]:
        pass

    @overload
    def __getitem__(self, provider: Provider[T]) -> Providable[T]:
        pass

    @overload
    def __getitem__(self, provider: T) -> Providable[T]:
        pass

    def __getitem__(self, provider: Any) -> Any:
        if isinstance(provider, type) and issubclass(provider, Container):
            provider = provider()

        return Providable(provider)


def inject(func: Callable[..., Any]) -> Callable[..., Any]:
    def provide_object(obj: Any, scope: Scope) -> Any:
        if isinstance(obj, Provider):
            return obj.__provide__(scope)
        elif isinstance(obj, type) and issubclass(obj, Container):
            return obj().__provide__(scope)
        elif isinstance(obj, Providable):
            return obj.provider.__provide__(scope)
        else:
            return EMPTY

    def provide_arguments(
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> tuple[tuple[Any, ...], dict[str, Any], Scope]:
        scope: Scope[Any] = Scope()

        signature = inspect.signature(func)
        bound_params = signature.bind_partial(*args, **kwargs)

        for param in signature.parameters.values():
            if get_origin(param.annotation) is Annotated and len(get_args(param.annotation)) == 2:
                base_type, obj = get_args(param.annotation)
                if (
                    param.name not in bound_params.arguments
                    and (value := provide_object(obj, scope)) is not EMPTY
                ):
                    bound_params.arguments[param.name] = value

            if (obj := bound_params.arguments.get(param.name)) and (
                value := provide_object(obj, scope)
            ) is not EMPTY:
                bound_params.arguments[param.name] = value

            if (obj := param.default) is not param.empty and (
                value := provide_object(obj, scope)
            ) is not EMPTY:
                bound_params.arguments[param.name] = value

        return bound_params.args, bound_params.kwargs, scope

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        args, kwargs, scope = provide_arguments(args, kwargs)

        try:
            result = func(*args, **kwargs)
        finally:
            for provider, data in scope.items():
                provider.__reset_scope_data__(data)

        return result

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        args, kwargs, scope = provide_arguments(args, kwargs)

        try:
            result = await func(*args, **kwargs)
        finally:
            await asyncio.gather(
                *(provider.__areset_scope_data__(data) for provider, data in scope.items())
            )

        return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


Provide: Final = ProvidableBuilder()
