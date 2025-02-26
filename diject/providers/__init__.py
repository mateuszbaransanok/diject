from diject.providers.container import Container
from diject.providers.pretenders.attribute import AttributeProvider
from diject.providers.pretenders.callable import CallableProvider
from diject.providers.pretenders.creators.creator import CreatorProvider
from diject.providers.pretenders.creators.factory import FactoryProvider
from diject.providers.pretenders.creators.services.resource import ResourceProvider
from diject.providers.pretenders.creators.services.scoped import ScopedProvider
from diject.providers.pretenders.creators.services.service import ServiceProvider
from diject.providers.pretenders.creators.services.singleton import SingletonProvider
from diject.providers.pretenders.creators.services.thread import ThreadProvider
from diject.providers.pretenders.creators.services.transient import TransientProvider
from diject.providers.pretenders.object import ObjectProvider
from diject.providers.pretenders.pretender import PretenderProvider
from diject.providers.pretenders.selector import SelectorProvider
from diject.providers.provider import Provider

__all__ = [
    "AttributeProvider",
    "CallableProvider",
    "Container",
    "CreatorProvider",
    "FactoryProvider",
    "ObjectProvider",
    "PretenderProvider",
    "Provider",
    "ResourceProvider",
    "ScopedProvider",
    "SelectorProvider",
    "ServiceProvider",
    "SingletonProvider",
    "ThreadProvider",
    "TransientProvider",
]
