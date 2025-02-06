import asyncio
from abc import ABC
from typing import Any, Callable, Generic, Iterator, ParamSpec, Type, TypeVar, overload

from diject.extensions.scope import Scope
from diject.providers.pretenders.pretender import Pretender, PretenderBuilder, PretenderProvider
from diject.providers.provider import Provider
from diject.utils.convert import any_as_provider
from diject.utils.exceptions import DITypeError
from diject.utils.repr import create_class_repr

T = TypeVar("T")
TCreatorProvider = TypeVar("TCreatorProvider", bound="CreatorProvider")
P = ParamSpec("P")


class CreatorProvider(PretenderProvider[T], ABC):
    def __init__(self, callable: Type[T] | Callable[..., T], /, *args: Any, **kwargs: Any) -> None:
        super().__init__()

        if isinstance(callable, Provider):
            raise DITypeError(f"'{self}' cannot create other providers")

        self.__callable = callable
        self.__args = tuple(any_as_provider(arg) for arg in args)
        self.__kwargs = {kw: any_as_provider(arg) for kw, arg in kwargs.items()}

    @property
    def __callable__(self) -> Type[T] | Callable[..., T]:
        return self.__callable

    @property
    def __args__(self) -> tuple[Provider[Any], ...]:
        return self.__args

    @property
    def __kwargs__(self) -> dict[str, Provider[Any]]:
        return self.__kwargs

    def __repr__(self) -> str:
        return create_class_repr(self, self.__callable, *self.__args, **self.__kwargs)

    def __travers__(self) -> Iterator[tuple[str, Provider[Any]]]:
        for i, arg in enumerate(self.__args):
            yield str(i), arg

        for kw, arg in self.__kwargs.items():
            yield kw, arg

    def __create__(self, scope: Scope | None = None) -> T:
        args = tuple(arg.__provide__(scope) for arg in self.__args)
        kwargs = {kw: arg.__provide__(scope) for kw, arg in self.__kwargs.items()}
        try:
            return self.__callable(*args, **kwargs)
        except Exception as exc:
            exc.add_note(f"Error was encountered while providing {self}")
            raise

    async def __acreate__(self, scope: Scope | None = None) -> T:
        args = await asyncio.gather(*(arg.__aprovide__(scope) for arg in self.__args))
        values = await asyncio.gather(*(arg.__aprovide__(scope) for arg in self.__kwargs.values()))
        kwargs = {kw: arg for kw, arg in zip(self.__kwargs, values, strict=True)}
        try:
            return self.__callable(*args, **kwargs)
        except Exception as exc:
            exc.add_note(f"Error was encountered while providing {self}")
            raise


class CreatorPretender(Pretender, Generic[T, TCreatorProvider]):
    def __init__(
        self,
        provider_cls: Type[TCreatorProvider],
        callable: Type[T] | Callable[..., T],
    ) -> None:
        self.__provider_cls = provider_cls
        self.__callable = callable

    def __repr__(self) -> str:
        return create_class_repr(self, self.__provider_cls, self.__callable)

    def __call__(self, *args: Any, **kwargs: Any) -> CreatorProvider:
        return self.__provider_cls(self.__callable, *args, **kwargs)


class CreatorPretenderBuilder(PretenderBuilder, Generic[TCreatorProvider]):
    def __init__(self, provider_cls: Type[TCreatorProvider]) -> None:
        self.__provider_cls = provider_cls

    def __repr__(self) -> str:
        return create_class_repr(self, self.__provider_cls)

    @overload
    def __getitem__(self, callable: Type[T]) -> Type[T]:
        pass

    @overload
    def __getitem__(self, callable: Callable[P, T]) -> Callable[P, T]:
        pass

    def __getitem__(self, callable: Any) -> Any:
        return CreatorPretender(
            provider_cls=self.__provider_cls,
            callable=callable,
        )
