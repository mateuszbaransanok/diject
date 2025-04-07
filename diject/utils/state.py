import asyncio
import warnings
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from diject.exceptions import DIAsyncError

T = TypeVar("T")


@dataclass
class State(Generic[T]):
    object: AsyncIterator[T] | Iterator[T] | T
    instance: T
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def close(self) -> None:
        match self.object:
            case AsyncIterator():
                raise DIAsyncError("Object have to be closed asynchronously")
            case Iterator():
                try:
                    next(self.object)
                except StopIteration:
                    pass
                except Exception as exc:
                    warnings.warn(
                        f"The object '{self.object}' closed incorrectly "
                        f"with {type(exc).__name__}: {exc}",
                        stacklevel=1,
                    )
                else:
                    warnings.warn(
                        f"The object '{self.object}' closed incorrectly, "
                        f"generator should yield only once",
                        stacklevel=1,
                    )

    async def aclose(self) -> None:
        match self.object:
            case AsyncIterator():
                try:
                    await anext(self.object)
                except StopAsyncIteration:
                    pass
                except Exception as exc:
                    warnings.warn(
                        f"The object '{self.object}' closed incorrectly "
                        f"with {type(exc).__name__}: {exc}",
                        stacklevel=1,
                    )
                else:
                    warnings.warn(
                        f"The object '{self.object}' closed incorrectly, "
                        f"generator should yield only once",
                        stacklevel=1,
                    )
            case Iterator():
                try:
                    next(self.object)
                except StopIteration:
                    pass
                except Exception as exc:
                    warnings.warn(
                        f"The object '{self.object}' closed incorrectly "
                        f"with {type(exc).__name__}: {exc}",
                        stacklevel=1,
                    )
                else:
                    warnings.warn(
                        f"The object '{self.object}' closed incorrectly, "
                        f"generator should yield only once",
                        stacklevel=1,
                    )
