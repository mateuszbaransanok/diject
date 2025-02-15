import sys


def is_custom_class(obj: type) -> bool:
    if not isinstance(obj, type):
        return False

    module_name = getattr(obj, "__module__", "")

    if module_name in sys.builtin_module_names:
        return False

    module = sys.modules.get(module_name)
    if module and getattr(module, "__file__", "").startswith(sys.prefix):
        return False

    return True
