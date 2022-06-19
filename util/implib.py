"""
See:
-----------
https://www.cnblogs.com/meishandehaizi/p/5863233.html
"""
import importlib.util
from importlib.machinery import ModuleSpec


def get_module_spec(name: str):
    """
    Checks if the module exists.

    :param name: Full-qualified name of module.
    :return: Spec of the module if it exists, None otherwise.
    """
    if not name or not isinstance(name, str):
        return None
    try:
        return importlib.util.find_spec(name)
    except ModuleNotFoundError:
        return None


def import_module_from_spec(module_spec: ModuleSpec):
    """
    Import the module specified by module_spec.

    :param module_spec: Spec of the module. Get from :func:`get_module_spec`.
    :return: Module if it exists, None otherwise.
    """
    if module_spec is None:
        return None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def import_module(name: str):
    """
    Import the module specified by name and package.

    :param name: Full-qualified name of module.
    :return: Module if it exists, None otherwise.
    """
    module_spec = get_module_spec(name)
    return import_module_from_spec(module_spec)


def import_function(callable: str):
    """
    Import the callable.

    :param callable: Full-qualified name of class or function.
            `<module>.<callable>`, such as 'os.path.join', 'time.time'.
    :return: Callable if it exists, None otherwise.

    Example
    ------------------
    >>> import_function('os.path.join') # return function os.path.join
    >>> import_function(join) # return directly if it is not str
    >>> import_function('os.path.unexist_func') # return None if callable does not exist.
    """
    if not isinstance(callable, str):
        return callable
    splits = callable.split('.')
    if len(splits) < 2:
        return None
    module_name = '.'.join(splits[:-1])
    callable = splits[-1]
    module = import_module(module_name)
    try:
        return getattr(module, callable)
    except AttributeError:
        return None
