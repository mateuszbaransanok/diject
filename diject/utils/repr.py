from typing import Any


def create_class_repr(self: Any, /, *args: Any, **kwargs: Any) -> str:
    _args = ", ".join(_object_repr(v) for v in args)
    _kwargs = ", ".join(f"{k}={_object_repr(v)}" for k, v in kwargs.items())
    _kwargs = f", {_kwargs}" if _args and _kwargs else _kwargs
    return f"{type(self).__qualname__}({_args}{_kwargs})"


def _object_repr(obj: Any) -> str:
    if hasattr(obj, "__qualname__"):
        return obj.__qualname__
    return repr(obj)
