class DIError(Exception):
    pass


class DITypeError(DIError):
    pass


class DINotStartedError(DIError):
    pass


class DIScopeError(DIError):
    pass


class DIAsyncError(DIError):
    pass


class DISelectorError(DIError):
    pass


class DINameError(DIError):
    pass


class DIEmptyObjectError(DIError):
    pass
