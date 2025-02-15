import logging
from abc import ABC
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Callable,
    Generator,
    Iterable,
    Iterator,
)
from typing import (
    Any,
    Generic,
    ParamSpec,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from diject.extensions.scope import Scope
from diject.providers.pretenders.creators.creator import CreatorProvider
from diject.providers.pretenders.pretender import Pretender, PretenderBuilder
from diject.utils.exceptions import DIAsyncError
from diject.utils.repr import create_class_repr

T = TypeVar("T")
TServiceProvider = TypeVar("TServiceProvider", bound="ServiceProvider")
P = ParamSpec("P")

LOG = logging.getLogger(__name__)


class ServiceProvider(CreatorProvider[T], ABC):
    def __init__(
        self,
        callable: Callable[..., Iterator[T] | AsyncIterator[T] | T],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(callable, *args, **kwargs)  # type: ignore[arg-type]

    def __type__(self) -> Any:
        if isinstance(self.__callable__, type):
            return self.__callable__
        else:
            annot_full = get_type_hints(self.__callable__).get("return", Any)
            annot_origin = get_origin(annot_full)

            if annot_origin is None:
                return annot_full
            else:
                annot_args = get_args(annot_full)

                if annot_origin in (
                    AsyncGenerator,
                    AsyncIterable,
                    AsyncIterator,
                    Generator,
                    Iterable,
                    Iterator,
                ):
                    return annot_args[0] if annot_args and isinstance(annot_args[0], type) else Any
                else:
                    return Any

    def __create_object_and_instance__(
        self,
        scope: Scope | None = None,
    ) -> tuple[Iterator[T] | T, T]:
        obj = self.__create__(scope)

        if isinstance(obj, AsyncIterator):
            raise DIAsyncError(f"'{self}' has to be created asynchronously")
        elif isinstance(obj, Iterator):
            instance = next(obj)
        else:
            instance = obj

        return obj, instance

    async def __acreate_object_and_instance__(
        self,
        scope: Scope | None = None,
    ) -> tuple[Iterator[T] | AsyncIterator[T] | T, T]:
        obj = await self.__acreate__(scope)

        if isinstance(obj, AsyncIterator):
            instance = await obj.__anext__()
        elif isinstance(obj, Iterator):
            instance = next(obj)
        else:
            instance = obj

        return obj, instance

    def __close_object__(self, obj: Iterator[T] | AsyncIterator[T] | T) -> None:
        if isinstance(obj, AsyncIterator):
            raise DIAsyncError(f"'{self}' has to be closed asynchronously")
        elif isinstance(obj, Iterator):
            try:
                next(obj)
            except StopIteration:
                pass
            except Exception as exc:
                _msg = "The provider '%s' closed incorrectly with %s: %s"
                LOG.error(_msg, self, type(exc).__name__, exc, exc_info=exc)
            else:
                LOG.error(
                    "The provider '%s' closed incorrectly, generator should be yielded only once",
                    self,
                )

    async def __aclose_object__(self, obj: Iterator[T] | AsyncIterator[T] | T) -> None:
        if isinstance(obj, AsyncIterator):
            try:
                await obj.__anext__()
            except StopAsyncIteration:
                pass
            except Exception as exc:
                _msg = "The provider '%s' closed incorrectly with %s: %s"
                LOG.error(_msg, self, type(exc).__name__, exc, exc_info=exc)
            else:
                LOG.error(
                    "The provider '%s' closed incorrectly, generator should be yielded only once",
                    self,
                )
        elif isinstance(obj, Iterator):
            try:
                next(obj)
            except StopIteration:
                pass
            except Exception as exc:
                _msg = "The provider '%s' closed incorrectly with %s: %s"
                LOG.error(_msg, self, type(exc).__name__, exc, exc_info=exc)
            else:
                LOG.error(
                    "The provider '%s' closed incorrectly, generator should be yielded only once",
                    self,
                )


class ServicePretender(Pretender, Generic[T, TServiceProvider]):
    def __init__(
        self,
        provider_cls: type[TServiceProvider],
        callable: Callable[..., Iterator[T] | AsyncIterator[T] | T],
    ) -> None:
        self.__provider_cls = provider_cls
        self.__callable = callable

    def __repr__(self) -> str:
        return create_class_repr(self, self.__provider_cls, self.__callable)

    def __call__(self, *args: Any, **kwargs: Any) -> ServiceProvider:
        return self.__provider_cls(self.__callable, *args, **kwargs)


class ServicePretenderBuilder(PretenderBuilder, Generic[TServiceProvider]):
    def __init__(self, provider_cls: type[TServiceProvider]) -> None:
        self.__provider_cls = provider_cls

    def __repr__(self) -> str:
        return create_class_repr(self, self.__provider_cls)

    @overload
    def __getitem__(  # type: ignore[overload-overlap]
        self,
        callable: Callable[P, Iterator[T] | AsyncIterator[T]],
    ) -> Callable[P, T]:
        pass

    @overload
    def __getitem__(self, callable: type[T]) -> type[T]:
        pass

    @overload
    def __getitem__(self, callable: Callable[P, T]) -> Callable[P, T]:
        pass

    def __getitem__(self, callable: Any) -> Any:
        return ServicePretender(
            provider_cls=self.__provider_cls,
            callable=callable,
        )
