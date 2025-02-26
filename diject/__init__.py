from typing import Any

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
from diject.tools.mock import ProviderMockBuilder, patch
from diject.tools.partial import PartialPretenderBuilder
from diject.tools.provide import DependencyBuilder, inject

__all__ = [
    "Container",
    "Factory",
    "Mock",
    "Object",
    "Partial",
    "Provide",
    "Resource",
    "Scoped",
    "Selector",
    "Singleton",
    "Thread",
    "Transient",
    "__version__",
    "inject",
    "exceptions",
    "patch",
    "protocols",
    "providers",
    "tools",
    "utils",
]

__version__ = "0.7.1"

Factory: CreatorPretenderBuilder[FactoryProvider]
Mock: ProviderMockBuilder
Object: ObjectPretenderBuilder
Partial: PartialPretenderBuilder
Provide: DependencyBuilder
Resource: ServicePretenderBuilder[ResourceProvider]
Scoped: ServicePretenderBuilder[ScopedProvider]
Selector: SelectorPretenderBuilder
Singleton: ServicePretenderBuilder[SingletonProvider]
Thread: ThreadPretenderBuilder
Transient: ServicePretenderBuilder[TransientProvider]


def __getattr__(name: str) -> Any:
    match name:
        case "Factory":
            return CreatorPretenderBuilder(FactoryProvider)
        case "Mock":
            return ProviderMockBuilder()
        case "Object":
            return ObjectPretenderBuilder()
        case "Partial":
            return PartialPretenderBuilder()
        case "Provide":
            return DependencyBuilder()
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
