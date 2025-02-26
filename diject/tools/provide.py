import asyncio
import functools
import inspect
from collections.abc import AsyncIterator, Callable, Generator, Hashable, Iterator
from types import TracebackType
from typing import (
    Annotated,
    Any,
    Generic,
    TypeVar,
    cast,
    get_args,
    get_origin,
    overload,
)

from diject.exceptions import DIScopeError, DITypeError
from diject.protocols.reset_protocol import ResetProtocol
from diject.protocols.start_protocol import StartProtocol
from diject.protocols.status_protocol import StatusProtocol
from diject.providers.container import Container
from diject.providers.pretenders.selector import SelectorProvider
from diject.providers.provider import Provider
from diject.utils.lock import Lock
from diject.utils.registry import get_registered_provider, register_provider, unregister_provider
from diject.utils.scope import Scope
from diject.utils.status import Status
from diject.utils.types import EMPTY, Empty, create_class_repr

T = TypeVar("T")
TProvider = TypeVar("TProvider", bound=Provider[Any])
TContainer = TypeVar("TContainer", bound=Container)


class Dependency(Generic[T]):
    """A class that wraps a Provider to provide a clean interface for working with providers,
    including context management, status retrieval, and traversal of related providers.

    Attributes:
        provider: The provider being wrapped by the Dependency.
        __lock: A lock used to manage concurrent access.
        __scope: The scope associated with the provider.
    """

    def __init__(self, provider: Provider[T]) -> None:
        """Initializes the Dependency instance with the provided provider.

        Args:
            provider: A Provider instance to wrap.

        Raises:
            DITypeError: If the provided argument is not an instance of the Provider class.
        """
        if not isinstance(provider, Provider):
            raise DITypeError(f"Argument 'provider' must be Provider type, not {type(provider)}")

        self.__lock = Lock()
        self.__provider = provider
        self.__scope: Scope | None = None

    def __repr__(self) -> str:
        return create_class_repr(self, self.__provider)

    def __call__(self) -> T:
        """Calls the provider and returns the provided value.

        Returns:
            T: The value provided by the provider.
        """
        return self.__provider.__provide__()

    def __await__(self) -> Generator[Any, None, T]:
        """Calls the provider asynchronously and returns the provided value.

        Returns:
            Generator: A generator that yields the value provided by the provider.
        """
        return self.__provider.__aprovide__().__await__()

    def __enter__(self) -> T:
        """Enters the context manager and provides the provider's value.

        Returns:
            T: The value provided by the provider within the context.

        Raises:
            DIScopeError: If the scope has already been created.
        """
        self.__lock.acquire()

        if self.__scope is not None:
            raise DIScopeError(f"{type(self).__name__}'s scope has already been created")

        self.__scope = Scope()

        return self.__provider.__provide__(self.__scope)

    async def __aenter__(self) -> T:
        """Asynchronously enters the context manager and provides the provider's value.

        Returns:
            T: The value provided by the provider within the context.

        Raises:
            DIScopeError: If the scope has already been created.
        """
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
        """Exits the context manager and closes the scope and associated providers.

        Args:
            exc_type: The exception type if one occurred.
            exc_val: The exception value if one occurred.
            exc_tb: The traceback if one occurred.

        Raises:
            DIScopeError: If the scope has not been created yet.
        """
        if self.__scope is None:
            raise DIScopeError(f"{type(self).__name__}'s scope has not been created yet")

        for provider, data in self.__scope.items():
            provider.__close__(data)

        self.__scope = None
        self.__lock.release()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Asynchronously exits the context manager and closes the scope and associated providers.

        Args:
            exc_type: The exception type if one occurred.
            exc_val: The exception value if one occurred.
            exc_tb: The traceback if one occurred.

        Raises:
            DIScopeError: If the scope has not been created yet.
        """
        if self.__scope is None:
            raise DIScopeError(f"{type(self).__name__}'s scope has not been created yet")

        await asyncio.gather(*(p.__aclose__(data) for p, data in self.__scope.items()))

        self.__scope = None
        await self.__lock.arelease()

    @property
    def provider(self) -> Provider[T]:
        """Returns the wrapped provider.

        Returns:
            Provider[T]: The wrapped provider instance.
        """
        return self.__provider

    @property
    def status(self) -> Status:
        """Returns the status of the provider.

        Returns:
            Status: The status of the provider.

        Raises:
            DITypeError: If the provider does not implement the StatusProtocol.
        """
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
    ) -> Iterator[tuple[str, Provider[Any]]]:
        pass

    def travers(
        self,
        types: type[TProvider] | tuple[type[TProvider], ...] | None = None,
        *,
        recursive: bool = False,
        only_public: bool = False,
        only_selected: bool = False,
    ) -> Any:
        """
        Traverses the provider and its sub-providers, yielding their names and types.

        Args:
            types: The types of providers to traverse.
            recursive: Whether to traverse recursively.
            only_public: Whether to include only public providers inside Container.
            only_selected: Whether to include only selected providers.

        Yields:
            tuple[str, Provider[Any]]: The name and provider of each item found.
        """
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
        """Starts the providers.

        This method initiates the provider by calling its internal start method
        (if it supports the StartProtocol). It also ensures that all necessary
        initialization tasks are completed for the provider.
        """
        self.__start(
            provider=self.__provider,
            cache=set(),
        )

    async def astart(self) -> None:
        """Asynchronously starts the providers.

        This method asynchronously initiates the provider by calling its internal
        start method (if it supports the StartProtocol). It ensures that any
        asynchronous setup tasks for the provider are completed.
        """
        await self.__astart(
            provider=self.__provider,
            cache=set(),
        )

    def shutdown(self) -> None:
        """Resets the providers.

        This method performs a graceful shutdown of the provider, calling its internal
        reset method recursively if it supports the ResetProtocol. It ensures all
        resources are released properly.
        """

        self.__reset(
            provider=self.__provider,
            recursive=True,
            cache=set(),
        )

    async def ashutdown(self) -> None:
        """Asynchronously resets the providers.

        This method asynchronously performs a graceful shutdown of the provider,
        calling its internal reset method recursively (if it supports the
        ResetProtocol) to ensure all resources are released asynchronously.
        """
        await self.__areset(
            provider=self.__provider,
            recursive=True,
            cache=set(),
        )

    def reset(self) -> None:
        """Resets the provider.

        This method resets the provider, calling its internal reset method without
        recursion. This is typically used to reset the state of the provider to its
        initial configuration.
        """
        self.__reset(
            provider=self.__provider,
            recursive=False,
            cache=set(),
        )

    async def areset(self) -> None:
        """Asynchronously resets the provider.

        This method asynchronously resets the provider, calling its internal reset
        method without recursion to reset the provider's state.
        """
        await self.__areset(
            provider=self.__provider,
            recursive=False,
            cache=set(),
        )

    def register(
        self,
        annotation: type | tuple[type, ...] | set[type] | list[type] | None = None,
        alias: str | tuple[str, ...] | set[str] | list[str] | None = None,
        wire: str | tuple[str, ...] | set[str] | list[str] | None = None,
    ) -> None:
        """Registers the provider with annotations, aliases, and modules.

        This method registers the provider with the given annotations, aliases, and
        modules. It ensures that the provider is appropriately linked to other
        components in the system, such as containers or other services.

        Args:
            annotation (type | tuple[type, ...] | set[type] | list[type] | None):
                The type annotation(s) to associate with the provider.
            alias (str | tuple[str, ...] | set[str] | list[str] | None):
                The alias or aliases to register for the provider.
            wire (str | tuple[str, ...] | set[str] | list[str] | None):
                The module or modules to associate with the provider.
        """
        aliases = {alias} if isinstance(alias, str) else set(alias) if alias else set()
        modules = {wire} if isinstance(wire, str) else set(wire) if wire else set()

        if isinstance(self.__provider, Container):
            self.__register_container(
                container=type(self.__provider),
                aliases=aliases,
                modules=modules,
            )
        else:
            if isinstance(annotation, list | tuple | set):
                annotations = annotation
            elif annotation:
                annotations = (annotation,)
            elif isinstance(annot := self.__provider.__type__(), type):
                annotations = annot.mro()
            else:
                annotations = ()

            register_provider(
                provider=self.__provider,
                annotations=annotations,
                aliases=aliases,
                modules=modules,
            )

    def unregister(self) -> None:
        """Unregisters the provider.

        This method unregisters the provider from the system. If the provider is a
        container, it will also unregister all providers contained within the container.
        """
        if isinstance(self.__provider, Container):
            self.__unregister_container(type(self.__provider))
        else:
            unregister_provider(self.__provider)

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

    def __register_container(
        self,
        container: type[Container],
        aliases: set[str],
        modules: set[str],
    ) -> None:
        container_modules = set(getattr(container, "__wire__", ()))
        container_modules.update(modules)

        register_provider(
            provider=container,
            annotations=(container,),
            aliases=aliases,
            modules=container_modules,
        )

        for name, provider in self.travers(only_public=True):
            if isinstance(provider, Container):
                self.__register_container(
                    container=container,
                    aliases=set(),
                    modules=modules,
                )
            else:
                if name in container.__annotations__:
                    annot = container.__annotations__[name]
                else:
                    annot = provider.__type__()

                register_provider(
                    provider=provider,
                    annotations=annot.mro() if isinstance(annot, type) else (),
                    aliases={name, provider.__alias__},
                    modules=container_modules,
                )

    def __unregister_container(self, container: type[Container]) -> None:
        unregister_provider(container)

        for name, provider in self.travers(only_public=True):
            if isinstance(provider, Container):
                self.__unregister_container(container)
            else:
                unregister_provider(provider)


class DependencyBuilder:
    def __repr__(self) -> str:
        return create_class_repr(self)

    @overload
    def __getitem__(self, provider: type[TContainer]) -> Dependency[TContainer]:
        pass

    @overload
    def __getitem__(self, provider: Provider[T]) -> Dependency[T]:
        pass

    @overload
    def __getitem__(self, provider: T) -> Dependency[T]:
        pass

    def __getitem__(self, provider: Any) -> Any:
        if (
            isinstance(provider, str)
            or (isinstance(provider, type) and not issubclass(provider, Container))
        ) and isinstance(provider, Hashable):
            provider = get_registered_provider(provider)

        if isinstance(provider, type) and issubclass(provider, Container):
            provider = provider()

        return Dependency(provider)


def inject(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that injects dependencies into the function.

    This decorator is used to inject providers into a function by resolving
    the function's parameters and providing the necessary objects based on
    their type annotations. It also supports both synchronous and asynchronous
    functions.

    Args:
        func (Callable[..., Any]): The function to which the dependencies will
            be injected.

    Returns:
        Callable[..., Any]: The wrapped function with dependencies injected.
    """

    def provide_object(obj: Any, scope: Scope) -> Any:
        if isinstance(obj, Provider):
            return obj.__provide__(scope)
        elif isinstance(obj, type) and issubclass(obj, Container):
            return obj().__provide__(scope)
        elif isinstance(obj, Dependency):
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

        module = getattr(func, "__module__", "")

        for param in signature.parameters.values():
            if param.name in bound_params.arguments:
                value = bound_params.arguments[param.name]
            elif param.default is not param.empty:
                value = param.default
            else:
                annot_type = get_origin(param.annotation) or param.annotation

                if annot_type is Annotated:
                    annot_args = get_args(param.annotation)
                    if len(annot_args) == 2:
                        if isinstance(annot_args[1], str):
                            value = get_registered_provider(annot_args[1], module)
                        elif isinstance(annot_args[1], Provider) or (
                            isinstance(annot_args[1], type) and issubclass(annot_args[1], Container)
                        ):
                            value = annot_args[1]
                        else:
                            value = get_registered_provider(annot_args[0], module)
                    elif annot_args:
                        value = get_registered_provider(annot_args[0], module)
                    else:
                        value = EMPTY
                elif isinstance(param.annotation, type):
                    value = get_registered_provider(param.annotation, module)
                else:
                    value = EMPTY

            if not isinstance(value := provide_object(value, scope), Empty):
                bound_params.arguments[param.name] = value

        signature.bind(*bound_params.args, **bound_params.kwargs)

        return bound_params.args, bound_params.kwargs, scope

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        args, kwargs, scope = provide_arguments(args, kwargs)

        try:
            result = func(*args, **kwargs)
        finally:
            for provider, data in scope.items():
                provider.__close__(data)

        return result

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        args, kwargs, scope = provide_arguments(args, kwargs)

        try:
            result = await func(*args, **kwargs)
        finally:
            await asyncio.gather(*(provider.__aclose__(data) for provider, data in scope.items()))

        return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
