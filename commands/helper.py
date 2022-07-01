
from enum import Enum
from typing import Callable, TypeVar


def to_enum(t: type[Enum], v: str):
    try:
        return t[v.upper()]
    except:
        print(f'Unexpected {t.__name__.lower()} type {v}.')
        return None


def to_int(v: str, tip: str = '', comp: Callable[[int], bool] = lambda _: True):
    try:
        i = int(v)
        if not comp(i):
            raise ValueError(tip)
        return i
    except:
        print(f"Unexpected number {v}. {tip}")
        return None


_T = TypeVar('_T', int, float, None)


def to_tuple(v: str, t: _T = int, sep: str = ',') -> tuple[_T, _T]:
    """
    Example
    -----------
    >>> to_tuple('')
    (None, None)
    >>> to_tuple('1,')
    (1, None)
    >>> to_tuple('1,2')
    (1, 2)
    >>> to_tuple(',2')
    (None, 2)
    >>> to_tuple('1')
    (1, 1)
    """
    min = None
    max = None
    try:
        if not v:
            return (min, max)
        vs = v.split(sep)
        if len(vs) == 1:
            return (t(vs[0]), t(vs[0]))
        if len(vs) == 2:
            minstr, maxstr = vs
            if(minstr):
                min = t(minstr)
            if(maxstr):
                max = t(maxstr)
            return (min, max)
    except Exception as ex:
        print(ex)
        return (min, max)
