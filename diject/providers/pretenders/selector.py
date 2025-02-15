import logging
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import contextmanager
from types import TracebackType
from typing import Any, Generic, TypeVar

from diject.extensions.reset import ResetProtocol
from diject.extensions.scope import Scope
from diject.extensions.status import Status, StatusProtocol
from diject.providers.pretenders.pretender import (
    Pretender,
    PretenderBuilder,
    PretenderProvider,
)
from diject.providers.provider import Provider
from diject.utils.convert import any_as_provider
from diject.utils.exceptions import DISelectorError, DITypeError
from diject.utils.lock import Lock
from diject.utils.repr import create_class_repr

T = TypeVar("T")

LOG = logging.getLogger(__name__)


class SelectorProvider(PretenderProvider[T], StatusProtocol, ResetProtocol):
    def __init__(self, selector: Provider[str] | str, /, **providers: Provider[T] | T) -> None:
        super().__init__()
        self.__lock = Lock()
        self.__selector = any_as_provider(selector)
        self.__providers = {
            option: any_as_provider(provider) for option, provider in providers.items()
        }
        self.__option: str | None = None

    def __repr__(self) -> str:
        return create_class_repr(self, self.__selector, **self.__providers)

    def __propagate_alias__(self, alias: str) -> None:
        for name, provider in self.__travers__():
            provider.__alias__ = f"{alias}{name}"

    def __getoptions__(self) -> set[str]:
        return set(self.__providers)

    def __setoption__(self, option: str, provider: Provider[T] | T) -> None:
        self.__providers[option] = any_as_provider(provider)

    def __selector__(self) -> Provider[str]:
        return self.__selector

    def __selected__(self) -> Provider[T]:
        with self.__lock:
            if self.__option is None:
                self.__option = self.__selector.__provide__()
                LOG.debug("Select %s[%s]", self.__alias__, self.__option)

            try:
                return self.__providers[self.__option]
            except KeyError:
                raise DISelectorError(
                    f"Invalid option '{self.__option}'. "
                    f"Available options for {self}: {', '.join(self.__providers)}"
                )

    async def __aselected__(self) -> Provider[T]:
        async with self.__lock:
            if self.__option is None:
                self.__option = await self.__selector.__aprovide__()
                LOG.debug("Async select %s[%s]", self.__alias__, self.__option)

            try:
                return self.__providers[self.__option]
            except KeyError:
                raise DISelectorError(
                    f"Invalid option '{self.__option}'. "
                    f"Available options for {self}: {', '.join(self.__providers)}"
                )

    def __type__(self) -> Any:
        if not self.__providers:
            return Any

        baseline, *others = (
            tp.mro() if isinstance(tp := provider.__type__(), type) else ()
            for name, provider in self.__providers.items()
        )

        for cls in baseline:
            if all(cls in other for other in others):
                return cls

        return Any

    def __travers__(
        self,
        only_selected: bool = False,
    ) -> Iterator[tuple[str, Provider[Any]]]:
        yield "?", self.__selector

        if only_selected:
            selected = self.__selected__()
            yield f"[{self.__option}]", selected
        else:
            for option, provider in self.__providers.items():
                yield f"[{option}]", provider

    async def __atravers__(
        self,
        only_selected: bool = False,
    ) -> AsyncIterator[tuple[str, Provider[Any]]]:
        yield "?", self.__selector

        if only_selected:
            selected = await self.__aselected__()
            yield f"[{self.__option}]", selected
        else:
            for option, provider in self.__providers.items():
                yield f"[{option}]", provider

    def __provide__(self, scope: Scope | None = None) -> T:
        selected = self.__selected__()
        return selected.__provide__(scope)

    async def __aprovide__(self, scope: Scope | None = None) -> T:
        selected = await self.__aselected__()
        return await selected.__aprovide__(scope)

    def __status__(self) -> Status:
        return Status.STOPPED if self.__option is None else Status.STARTED

    def __reset__(self) -> None:
        with self.__lock:
            self.__option = None

    async def __areset__(self) -> None:
        async with self.__lock:
            self.__option = None


class SelectorOption:
    def __init__(self, option: str, available_selectors: set[SelectorProvider[Any]]) -> None:
        self.__option = option
        self.__available_selectors = available_selectors
        self.__closed = False

    def __setitem__(self, selector: Any, provider: Any) -> None:
        if self.__closed:
            raise DISelectorError("Cannot set selector option outside context manager")

        if not isinstance(selector, SelectorProvider):
            raise DITypeError("Option can be set only for SelectorProvider instance")

        if selector not in self.__available_selectors:
            raise DISelectorError("Given selector is not defined in this selector group")

        selector.__setoption__(
            option=self.__option,
            provider=provider,
        )

    def __close__(self) -> None:
        self.__closed = True


class GroupSelector:
    def __init__(self, selector: str) -> None:
        self.__selector = selector
        self.__closed = False
        self.__available_selectors: set[SelectorProvider[Any]] = set()

    def __getitem__(self, selector_type: Callable[..., T]) -> Callable[[], T]:
        return self.__create_empty_selector  # type: ignore[return-value]

    def __call__(self) -> Any:
        return self.__create_empty_selector()

    @contextmanager
    def __eq__(self, option: str) -> Iterator[SelectorOption]:  # type: ignore[override]
        if not self.__closed:
            raise DISelectorError("Cannot create SelectorOption inside selector context manager")

        if not isinstance(option, str):
            raise DITypeError("Option value have to be a string")

        selector_option = SelectorOption(
            option=option,
            available_selectors=self.__available_selectors,
        )

        try:
            yield selector_option
        finally:
            selector_option.__close__()

            for selector in self.__available_selectors:
                if option not in selector.__getoptions__():
                    raise DISelectorError(
                        f"At least one selector within group is not setup with option '{option}'",
                    )

    def __close__(self) -> None:
        self.__closed = True

    def __create_empty_selector(self) -> SelectorProvider[Any]:
        if self.__closed:
            raise DISelectorError("Cannot create selector outside context manager")

        selector: SelectorProvider[Any] = SelectorProvider(self.__selector)
        self.__available_selectors.add(selector)
        return selector


class SelectorPretender(Pretender, Generic[T]):
    def __init__(self, selector: str) -> None:
        self.__selector = selector
        self.__group_selector: GroupSelector | None = None

    def __repr__(self) -> str:
        return create_class_repr(self, self.__selector)

    def __call__(self, **providers: T) -> T:
        return SelectorProvider(self.__selector, **providers)  # type: ignore[return-value]

    def __enter__(self) -> GroupSelector:
        if self.__group_selector is not None:
            raise DISelectorError("Group selector already created")

        self.__group_selector = GroupSelector(self.__selector)

        return self.__group_selector

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.__group_selector is not None:
            self.__group_selector.__close__()
        self.__group_selector = None


class SelectorPretenderBuilder(PretenderBuilder):
    def __getitem__(self, selector: str) -> SelectorPretender:
        return SelectorPretender(selector)
