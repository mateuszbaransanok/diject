import sys
from typing import Any, Final, Generic, TypeVar

from diject.providers.provider import Provider


# EMPTY VALUE TYPE ---------------------------------------------------------------------------------
class Empty:
    pass


EMPTY: Final = Empty()


# CUSTOM CLASS CHECKER -----------------------------------------------------------------------------
def is_custom_class(obj: type) -> bool:
    if not isinstance(obj, type):
        return False

    module_name = getattr(obj, "__module__", "")

    if module_name in sys.builtin_module_names:
        return False

    module = sys.modules.get(module_name)
    if module and getattr(module, "__file__", "").startswith(sys.prefix):
        return False

    return True


# CLASS REPRESENTATION -----------------------------------------------------------------------------
def create_class_repr(self: Any, /, *args: Any, **kwargs: Any) -> str:
    _args = ", ".join(_object_repr(v) for v in args)
    _kwargs = ", ".join(f"{k}={_object_repr(v)}" for k, v in kwargs.items())
    _kwargs = f", {_kwargs}" if _args and _kwargs else _kwargs
    return f"{type(self).__qualname__}({_args}{_kwargs})"


def _object_repr(obj: Any) -> str:
    if hasattr(obj, "__qualname__"):
        return obj.__qualname__
    return repr(obj)


# CLASS FOR CREATING COLLECTIONS BY FACTORY PROVIDER -----------------------------------------------
TCollection = TypeVar("TCollection", list, tuple, set)


class CollectionCreator(Generic[TCollection]):
    def __init__(self, collection_cls: type[TCollection]) -> None:
        self.__collection_cls: type[TCollection] = collection_cls

    def __call__(self, *items: Any) -> TCollection:
        return self.__collection_cls(items)


# CAST OBJECT TO PROVIDER TYPE ---------------------------------------------------------------------
def any_as_provider(obj: Any) -> Provider[Any]:
    from diject.providers.container import Container

    if isinstance(obj, Provider):
        return obj
    elif isinstance(obj, type) and issubclass(obj, Container):
        return obj()
    else:
        return obj_as_provider(obj)


def obj_as_provider(obj: Any) -> Provider[Any]:
    from diject.providers.pretenders.creators.factory import FactoryProvider
    from diject.providers.pretenders.object import ObjectProvider

    collection = type(obj)

    if collection in (list, tuple, set):
        return FactoryProvider(CollectionCreator(collection), *obj)
    elif collection is dict:
        return FactoryProvider(dict, obj_as_provider(tuple(obj.items())))
    else:
        return ObjectProvider(obj)
