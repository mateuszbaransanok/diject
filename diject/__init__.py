from typing import Any

from diject.providable import ProvidableBuilder, inject
from diject.providers.container import Container
from diject.providers.pretenders.creators.creator import CreatorPretenderBuilder
from diject.providers.pretenders.creators.factory import FactoryProvider
from diject.providers.pretenders.creators.services.resource import ResourceProvider
from diject.providers.pretenders.creators.services.scoped import ScopedProvider
from diject.providers.pretenders.creators.services.service import ServicePretenderBuilder
from diject.providers.pretenders.creators.services.singleton import SingletonProvider
from diject.providers.pretenders.creators.services.thread import ThreadPretenderBuilder
from diject.providers.pretenders.creators.services.transient import TransientProvider
from diject.providers.pretenders.object import ObjectPretenderBuilder
from diject.providers.pretenders.selector import SelectorPretenderBuilder
from diject.utils.mock import ProviderMockBuilder, patch

__all__ = [
    "Container",
    "Factory",
    "Mock",
    "Object",
    "Provide",
    "Resource",
    "Scoped",
    "Selector",
    "Singleton",
    "Thread",
    "Transient",
    "__version__",
    "extensions",
    "inject",
    "patch",
    "providable",
    "providers",
    "utils",
]

__version__ = "0.5.1"

Factory: CreatorPretenderBuilder[FactoryProvider[Any]]
Mock: ProviderMockBuilder
Object: ObjectPretenderBuilder
Provide: ProvidableBuilder
Resource: ServicePretenderBuilder[ResourceProvider[Any]]
Scoped: ServicePretenderBuilder[ScopedProvider[Any]]
Selector: SelectorPretenderBuilder
Singleton: ServicePretenderBuilder[SingletonProvider[Any]]
Thread: ThreadPretenderBuilder
Transient: ServicePretenderBuilder[TransientProvider[Any]]


def __getattr__(name: str) -> Any:
    match name:
        case "Factory":
            return CreatorPretenderBuilder(FactoryProvider)
        case "Mock":
            return ProviderMockBuilder()
        case "Object":
            return ObjectPretenderBuilder()
        case "Provide":
            return ProvidableBuilder()
        case "Resource":
            return ServicePretenderBuilder(ResourceProvider)
        case "Scoped":
            return ServicePretenderBuilder(ScopedProvider)
        case "Selector":
            return SelectorPretenderBuilder()
        case "Singleton":
            return ServicePretenderBuilder(SingletonProvider)
        case "Thread":
            return ThreadPretenderBuilder()
        case "Transient":
            return ServicePretenderBuilder(TransientProvider)
