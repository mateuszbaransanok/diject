import threading
import typing
from functools import cache

from diject.providers.provider import Provider
from diject.utils.empty import EMPTY, Empty
from diject.utils.types import is_custom_class

if typing.TYPE_CHECKING:
    from diject.providers.container import Container

__LOCK = threading.Lock()
__REGISTRY: dict[type | str, set[Provider | type["Container"]]] = {}
__MODULES: dict[Provider | type["Container"], set[str]] = {}


def register(
    provider: Provider | type["Container"],
    annotations: set[type] | list[type] | tuple[type, ...] | None = None,
    aliases: set[str] | list[str] | tuple[str, ...] | None = None,
    modules: set[str] | list[str] | tuple[str, ...] | None = None,
) -> None:
    with __LOCK:
        __MODULES.setdefault(provider, set())
        __MODULES[provider].update(modules or ())

        for key in (
            *(cls for cls in annotations or () if is_custom_class(cls)),
            *(aliases or ()),
        ):
            __REGISTRY.setdefault(key, set())
            __REGISTRY[key].add(provider)

        get_registered_provider.cache_clear()


def unregister(provider: Provider | type["Container"]) -> None:
    with __LOCK:
        __MODULES.pop(provider, None)

        for key, providers in list(__REGISTRY.items()):
            providers.discard(provider)
            if not providers:
                __REGISTRY.pop(key)

        get_registered_provider.cache_clear()


@cache
def get_registered_provider(
    key: str | type,
    module: str = "",
) -> Provider | type["Container"] | Empty:
    if key not in __REGISTRY:
        return EMPTY

    registered_provider: Provider | type["Container"] | None = None
    for provider in __REGISTRY[key]:
        provider_modules = __MODULES[provider]
        if not module or (not provider_modules or module in provider_modules):
            if registered_provider is None:
                registered_provider = provider
            else:
                return EMPTY

    if registered_provider is None:
        return EMPTY
    else:
        return registered_provider
