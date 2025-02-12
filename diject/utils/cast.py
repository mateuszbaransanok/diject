from typing import Any

from diject.providers.provider import Provider


def any_as_provider(obj: Any) -> Provider:
    from diject.providers.collections.dict import DictProvider
    from diject.providers.collections.list import ListProvider
    from diject.providers.collections.tuple import TupleProvider
    from diject.providers.object import ObjectProvider

    if isinstance(obj, Provider):
        return obj
    elif (obj_type := type(obj)) is dict:
        return DictProvider(obj)
    elif obj_type is list:
        return ListProvider(obj)
    elif obj_type is tuple:
        return TupleProvider(obj)
    else:
        return ObjectProvider(obj)
