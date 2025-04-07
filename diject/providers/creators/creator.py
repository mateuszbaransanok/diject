import asyncio
from abc import ABC
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any, Generic, ParamSpec, TypeVar, overload

from diject.exceptions import DIAsyncError, DIContextError, DIErrorWrapper, DITypeError
from diject.providers.collections.dict import DictProvider
from diject.providers.collections.tuple import TupleProvider
from diject.providers.object import ObjectProvider
from diject.providers.provider import Pretender, PretenderBuilder, Provider
from diject.tools.partial import Partial
from diject.utils.state import State
from diject.utils.string import create_class_repr

T = TypeVar("T")
TCreatorProvider = TypeVar("TCreatorProvider", bound="CreatorProvider")
TCallable = Callable[..., AsyncIterator[T] | Iterator[T] | T]
P = ParamSpec("P")


class CreatorProvider(Provider[T], ABC):
    def __init__(
        self,
        callable: TCallable | ObjectProvider[TCallable] | Partial[T],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__()

        if isinstance(callable, ObjectProvider):
            callable = callable.__object__

        if isinstance(callable, Provider):
            raise DITypeError(f"'{self}' cannot create other providers")

        if isinstance(callable, Partial):
            args = (*callable.args, *args)
            kwargs = {**callable.kwargs, **kwargs}
            callable = callable.callable

        self.__callable = callable
        self.__args = TupleProvider(args)
        self.__kwargs = DictProvider(kwargs)

    @property
    def __callable__(self) -> TCallable:
        return self.__callable

    @property
    def __args__(self) -> tuple[Provider, ...]:
        return self.__args.__object__

    @property
    def __kwargs__(self) -> dict[str, Provider]:
        return self.__kwargs.__object__

    def __repr__(self) -> str:
        return create_class_repr(self, self.__callable, *self.__args__, **self.__kwargs__)

    def __travers_dependency__(self) -> Iterator[tuple[str, Provider]]:
        yield from self.__args.__travers__()
        yield from self.__kwargs.__travers__()

    def __create__(self, *, allow_generator: bool = True) -> State:
        args = self.__args.__provide__()
        kwargs = self.__kwargs.__provide__()

        try:
            obj = self.__callable(*args, **kwargs)
        except Exception as exc:
            raise DIErrorWrapper(
                origin=exc,
                note=f"Error was encountered while creating '{self}'",
            ) from exc

        match obj:
            case AsyncIterator():
                raise DIAsyncError("Object have to be created asynchronously")
            case Iterator():
                if not allow_generator:
                    raise DIContextError(f"'{self}' has to be called within context")

                try:
                    instance = next(obj)
                except Exception as exc:
                    raise DIErrorWrapper(
                        origin=exc,
                        note=f"Error was encountered while creating '{self}'",
                    ) from exc
            case _:
                instance = obj

        return State(
            object=obj,
            instance=instance,
        )

    async def __acreate__(self, *, allow_generator: bool = True) -> State:
        args, kwargs = await asyncio.gather(
            self.__args.__aprovide__(),
            self.__kwargs.__aprovide__(),
        )

        try:
            obj = self.__callable(*args, **kwargs)
        except Exception as exc:
            raise DIErrorWrapper(
                origin=exc,
                note=f"Error was encountered while creating '{self}'",
            ) from exc

        match obj:
            case AsyncIterator():
                if not allow_generator:
                    raise DIContextError(f"'{self}' has to be called within context")

                try:
                    instance = await anext(obj)
                except Exception as exc:
                    raise DIErrorWrapper(
                        origin=exc,
                        note=f"Error was encountered while creating '{self}'",
                    ) from exc
            case Iterator():
                if not allow_generator:
                    raise DIContextError(f"'{self}' has to be called within context")

                try:
                    instance = next(obj)
                except Exception as exc:
                    raise DIErrorWrapper(
                        origin=exc,
                        note=f"Error was encountered while creating '{self}'",
                    ) from exc
            case _:
                instance = obj

        return State(
            object=obj,
            instance=instance,
        )


class CreatorPretender(Pretender, Generic[T, TCreatorProvider]):
    def __init__(
        self,
        provider_cls: type[TCreatorProvider],
        callable: Callable[..., AsyncIterator[T] | Iterator[T] | T],
    ) -> None:
        self._provider_cls = provider_cls
        self._callable = callable

    def __repr__(self) -> str:
        return create_class_repr(self, self._provider_cls, self._callable)

    def __call__(self, *args: Any, **kwargs: Any) -> CreatorProvider:
        return self._provider_cls(self._callable, *args, **kwargs)


class CreatorPretenderBuilder(PretenderBuilder[TCreatorProvider]):
    def __init__(self, provider_cls: type[TCreatorProvider]) -> None:
        self._provider_cls = provider_cls

    def __repr__(self) -> str:
        return create_class_repr(self, self._provider_cls)

    @overload
    def __getitem__(self, callable: Partial[T]) -> Partial[T]:
        pass

    @overload
    def __getitem__(  # type: ignore[overload-overlap]
        self,
        callable: Callable[P, Iterator[T]],
    ) -> Callable[P, T]:
        pass

    @overload
    def __getitem__(self, callable: type[T]) -> type[T]:
        pass

    @overload
    def __getitem__(self, callable: Callable[P, T]) -> Callable[P, T]:
        pass

    def __getitem__(self, callable: Any) -> Any:
        return CreatorPretender(
            provider_cls=self._provider_cls,
            callable=callable,
        )

    @property
    def type(self) -> type[TCreatorProvider]:
        return self._provider_cls
