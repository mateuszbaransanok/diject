from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import contextmanager
from types import TracebackType
from typing import Any, Generic, TypeVar

from diject.exceptions import DISelectorError, DITypeError
from diject.injector import Injector
from diject.providers.provider import Pretender, PretenderBuilder, Provider
from diject.utils.cast import any_as_provider
from diject.utils.status import Status
from diject.utils.string import create_class_repr

T = TypeVar("T")


class SelectorProvider(Provider[T]):
    def __init__(self, selector: Provider[str] | str, /, **providers: Provider[T] | T) -> None:
        super().__init__()
        self.__selector = any_as_provider(selector)
        self.__providers = {key: any_as_provider(provider) for key, provider in providers.items()}
        self.__option: str | None = None

    def __repr__(self) -> str:
        return create_class_repr(self, self.__selector, **self.__providers)

    def __getoptions__(self) -> set[str]:
        return set(self.__providers)

    def __setoption__(self, option: str, provider: Provider[T] | T) -> None:
        self.__providers[option] = any_as_provider(provider)

    def __propagate_alias__(self, alias: str) -> None:
        for name, provider in self.__travers__():
            provider.__alias__ = f"{alias}{name}"

    def __selected__(self) -> Provider[T]:
        if self.__option is None:
            try:
                with Injector(reuse_context=False):
                    option = self.__selector.__provide__()
            finally:
                self.__selector.__shutdown__()

            if isinstance(option, str):
                self.__option = option
            else:
                raise DITypeError(f"Selector must be 'str' type; not '{type(option).__name__}'")

        try:
            return self.__providers[self.__option]
        except KeyError:
            raise DISelectorError(
                f"Invalid option '{self.__option}'. "
                f"Available options for {self}: {', '.join(self.__providers)}",
            )

    async def __aselected__(self) -> Provider[T]:
        if self.__option is None:
            try:
                async with Injector(reuse_context=False):
                    option = await self.__selector.__aprovide__()
            finally:
                await self.__selector.__ashutdown__()

            if isinstance(option, str):
                self.__option = option
            else:
                raise DITypeError(f"Selector must be 'str' type; not '{type(option).__name__}'")

        try:
            return self.__providers[self.__option]
        except KeyError:
            raise DISelectorError(
                f"Invalid option '{self.__option}'. "
                f"Available options for {self}: {', '.join(self.__providers)}",
            )

    def __travers__(
        self,
        *,
        only_selected: bool = False,
    ) -> Iterator[tuple[str, Provider]]:
        try:
            yield from self.__travers_dependency__(only_selected=only_selected)
        except Exception:
            self.__status = Status.CORRUPTED
            raise

    async def __atravers__(
        self,
        *,
        only_selected: bool = False,
    ) -> AsyncIterator[tuple[str, Provider]]:
        try:
            async for name, provider in self.__atravers_dependency__(only_selected=only_selected):
                yield name, provider
        except Exception:
            self.__status = Status.CORRUPTED
            raise

    def __travers_dependency__(
        self,
        *,
        only_selected: bool = False,
    ) -> Iterator[tuple[str, Provider]]:
        if only_selected:
            with self.__lock__:
                selected = self.__selected__()
            yield f"[{self.__option}]", selected
        else:
            for option, provider in self.__providers.items():
                yield f"[{option}]", provider

        yield "?", self.__selector

    async def __atravers_dependency__(
        self,
        *,
        only_selected: bool = False,
    ) -> AsyncIterator[tuple[str, Provider]]:
        if only_selected:
            async with self.__lock__:
                selected = await self.__aselected__()
            yield f"[{self.__option}]", selected
        else:
            for option, provider in self.__providers.items():
                yield f"[{option}]", provider

        yield "?", self.__selector

    def __provide_dependency__(self) -> T:
        with self.__lock__:
            selected = self.__selected__()
        return selected.__provide__()

    async def __aprovide_dependency__(self) -> T:
        async with self.__lock__:
            selected = await self.__aselected__()
        return await selected.__aprovide__()

    def __start_dependency__(self) -> None:
        selected = self.__selected__()
        selected.__start__()

    async def __astart_dependency__(self) -> None:
        selected = await self.__aselected__()
        await selected.__astart__()

    def __shutdown__(self) -> None:
        with self.__lock__:
            if self.__status__ is not Status.IDLE:
                if self.__option is not None:
                    if self.__option in self.__providers:
                        self.__providers[self.__option].__shutdown__()
                    self.__option = None
                self.__status__ = Status.IDLE

    async def __ashutdown__(self) -> None:
        async with self.__lock__:
            if self.__status__ is not Status.IDLE:
                if self.__option is not None:
                    if self.__option in self.__providers:
                        await self.__providers[self.__option].__ashutdown__()
                    self.__option = None
                self.__status__ = Status.IDLE


class SelectorOption:
    def __init__(self, option: str, available_selectors: set[SelectorProvider[Any]]) -> None:
        self._option = option
        self._available_selectors = available_selectors
        self._closed = False

    def __setitem__(self, selector: Any, provider: Any) -> None:
        if self._closed:
            raise DISelectorError("Cannot set selector option outside context manager")

        if not isinstance(selector, SelectorProvider):
            raise DITypeError("Option can be set only for SelectorProvider instance")

        if selector not in self._available_selectors:
            raise DISelectorError("Given selector is not defined in this selector group")

        selector.__setoption__(
            option=self._option,
            provider=provider,
        )

    def __close__(self) -> None:
        self._closed = True


class GroupSelector:
    def __init__(self, selector: str) -> None:
        self._selector = selector
        self._closed = False
        self._available_selectors: set[SelectorProvider[Any]] = set()

    def __getitem__(self, selector_type: Callable[..., T]) -> Callable[[], T]:
        return self._create_empty_selector  # type: ignore[return-value]

    def __call__(self) -> Any:
        return self._create_empty_selector()

    @contextmanager
    def __eq__(self, option: str) -> Iterator[SelectorOption]:  # type: ignore[override]
        if not self._closed:
            raise DISelectorError("Cannot create SelectorOption inside selector context manager")

        if not isinstance(option, str):
            raise DITypeError("Option value have to be a string")

        selector_option = SelectorOption(
            option=option,
            available_selectors=self._available_selectors,
        )

        try:
            yield selector_option
        finally:
            selector_option.__close__()

            for selector in self._available_selectors:
                if option not in selector.__getoptions__():
                    raise DISelectorError(
                        f"At least one selector within group is not setup with option '{option}'",
                    )

    def __close__(self) -> None:
        self._closed = True

    def _create_empty_selector(self) -> SelectorProvider[Any]:
        if self._closed:
            raise DISelectorError("Cannot create selector outside context manager")

        selector: SelectorProvider[Any] = SelectorProvider(self._selector)
        self._available_selectors.add(selector)
        return selector


class SelectorPretender(Pretender, Generic[T]):
    def __init__(self, selector: str) -> None:
        self._selector = selector
        self._group_selector: GroupSelector | None = None

    def __repr__(self) -> str:
        return create_class_repr(self, self._selector)

    def __call__(self, **providers: T) -> T:
        return SelectorProvider(self._selector, **providers)  # type: ignore[return-value]

    def __enter__(self) -> GroupSelector:
        if self._group_selector is not None:
            raise DISelectorError("Group selector already created")

        self._group_selector = GroupSelector(self._selector)

        return self._group_selector

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._group_selector is not None:
            self._group_selector.__close__()
        self._group_selector = None


class SelectorPretenderBuilder(PretenderBuilder[SelectorProvider]):
    def __getitem__(self, selector: str) -> SelectorPretender:
        return SelectorPretender(selector)

    @property
    def type(self) -> type[SelectorProvider]:
        return SelectorProvider
