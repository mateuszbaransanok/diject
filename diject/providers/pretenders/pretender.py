from abc import ABC
from typing import TYPE_CHECKING, Any, TypeVar

from diject.providers.provider import Provider
from diject.utils.repr import create_class_repr

if TYPE_CHECKING:
    from diject.providers.pretenders.attribute import AttributeProvider
    from diject.providers.pretenders.callable import CallableProvider

T = TypeVar("T")


class PretenderProvider(Provider[T], ABC):
    def __call__(self, *args: Any, **kwargs: Any) -> "CallableProvider":
        from diject.providers.pretenders.callable import CallableProvider

        return CallableProvider(self, *args, **kwargs)

    def __getattr__(self, name: str) -> "AttributeProvider":
        if name.startswith("__"):
            return super().__getattribute__(name)  # type: ignore[no-any-return]
        else:
            from diject.providers.pretenders.attribute import AttributeProvider

            return AttributeProvider(self, name)


class Pretender(ABC):
    def __repr__(self) -> str:
        return create_class_repr(self)


class PretenderBuilder(ABC):
    def __repr__(self) -> str:
        return create_class_repr(self)
