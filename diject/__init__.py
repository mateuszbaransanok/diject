from typing import Any

from diject.container import Container
from diject.functions import (
    alias,
    aprovide,
    ashutdown,
    astart,
    atravers,
    inject,
    patch,
    provide,
    shutdown,
    start,
    status,
    travers,
)
from diject.providers.collections.dict import DictPretenderBuilder
from diject.providers.collections.list import ListPretenderBuilder
from diject.providers.collections.tuple import TuplePretenderBuilder
from diject.providers.creators.creator import CreatorPretenderBuilder
from diject.providers.creators.scoped import ScopedProvider
from diject.providers.creators.singleton import SingletonProvider
from diject.providers.creators.transient import TransientProvider
from diject.providers.object import ObjectPretenderBuilder
from diject.providers.selector import SelectorPretenderBuilder
from diject.tools.partial import PartialPretenderBuilder

__all__ = [
    "Container",
    "Dict",
    "List",
    "Object",
    "Partial",
    "Scoped",
    "Selector",
    "Singleton",
    "Transient",
    "Tuple",
    "__version__",
    "alias",
    "aprovide",
    "ashutdown",
    "astart",
    "atravers",
    "container",
    "exceptions",
    "functions",
    "inject",
    "patch",
    "provide",
    "providers",
    "shutdown",
    "start",
    "status",
    "tools",
    "travers",
    "utils",
]

__version__ = "0.7.1"

Dict: DictPretenderBuilder
List: ListPretenderBuilder
Object: ObjectPretenderBuilder
Partial: PartialPretenderBuilder
Scoped: CreatorPretenderBuilder[ScopedProvider]
Selector: SelectorPretenderBuilder
Singleton: CreatorPretenderBuilder[SingletonProvider]
Transient: CreatorPretenderBuilder[TransientProvider]
Tuple: TuplePretenderBuilder


def __getattr__(name: str) -> Any:
    match name:
        case "Dict":
            return DictPretenderBuilder()
        case "List":
            return ListPretenderBuilder()
        case "Object":
            return ObjectPretenderBuilder()
        case "Partial":
            return PartialPretenderBuilder()
        case "Scoped":
            return CreatorPretenderBuilder(ScopedProvider)
        case "Selector":
            return SelectorPretenderBuilder()
        case "Singleton":
            return CreatorPretenderBuilder(SingletonProvider)
        case "Transient":
            return CreatorPretenderBuilder(TransientProvider)
        case "Tuple":
            return TuplePretenderBuilder()
