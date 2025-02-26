from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from diject.providers.provider import Provider
from diject.utils.types import create_class_repr

if TYPE_CHECKING:
    from diject.providers.pretenders.attribute import AttributeProvider
    from diject.providers.pretenders.callable import CallableProvider

T = TypeVar("T")


class PretenderProvider(Provider[T], ABC):
    def __call__(self, *args: Any, **kwargs: Any) -> "CallableProvider":
        from diject.providers.pretenders.callable import CallableProvider

        callable = CallableProvider(self, *args, **kwargs)

        if self.__has_alias__:
            callable.__alias__ = f"{self.__alias__}()"

        return callable

    def __getattr__(self, name: str) -> "AttributeProvider":
        if name.startswith("__"):
            return super().__getattribute__(name)  # type: ignore[no-any-return]
        else:
            from diject.providers.pretenders.attribute import AttributeProvider

            attribute = AttributeProvider(self, name)

            if self.__has_alias__:
                attribute.__alias__ = f"{self.__alias__}.{name}"

            return attribute


class Pretender(ABC):
    def __repr__(self) -> str:
        return create_class_repr(self)


class PretenderBuilder(Generic[T], ABC):
    def __repr__(self) -> str:
        return create_class_repr(self)

    @property
    @abstractmethod
    def type(self) -> type[T]:
        pass
