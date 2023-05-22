import locale
import time

from uuid import uuid4


locale.setlocale( locale.LC_ALL, '' )


def as_currency(number: int) -> str:
    """Returns the given number as a currency string"""
    return locale.currency(number, grouping=True)


def create_random_code(length=6, incl_hyphens=False) -> str:
    """Returns a randomly generated code of variable length made from a UUID"""
    code = str(uuid4())[:length]
    if not incl_hyphens:
        code = code.replace('-','')
    return code


def mk_timestamp() -> int:
    """Returns a unix timestamp in milliseconds"""
    return int(time.time() * 1000.0)
