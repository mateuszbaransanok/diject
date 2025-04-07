class DIError(Exception):
    pass


class DIErrorWrapper(DIError):
    def __init__(
        self,
        origin: Exception,
        note: str = "",
        caused_by: Exception | None = None,
    ) -> None:
        self._origin = origin
        self._caused_by = caused_by
        self._note = note

        if self._note:
            self._origin.add_note(self._note)

    @property
    def origin(self) -> Exception:
        return self._origin

    @property
    def caused_by(self) -> Exception | None:
        return self._caused_by

    def __str__(self) -> str:
        return self._note


class DITypeError(DIError):
    pass


class DIAsyncError(DIError):
    pass


class DIContainerError(DIError):
    pass


class DIContextError(DIError):
    pass


class DISelectorError(DIError):
    pass


class DIObjectError(DIError):
    pass
