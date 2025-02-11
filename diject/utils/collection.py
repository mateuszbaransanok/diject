from typing import Any, Generic, TypeVar

TCollection = TypeVar("TCollection", list, tuple, set)


class CollectionCreator(Generic[TCollection]):
    def __init__(self, collection_cls: type[TCollection]) -> None:
        self.__collection_cls: type[TCollection] = collection_cls

    def __call__(self, *items: Any) -> TCollection:
        return self.__collection_cls(items)
