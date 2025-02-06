from typing import Any

from diject.providers.provider import Provider
from diject.utils.collection import CollectionCreator


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
        return FactoryProvider(dict, **obj)
    else:
        return ObjectProvider(obj)
