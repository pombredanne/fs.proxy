# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals



try:
    from tlz.itertoolz import unique
except ImportError:

    from six.moves import filterfalse

    def unique(iterable, key=None): 
        "Yield unique elements, preserving order."

        seen = set()
        seen_add = seen.add
        if key is None:
            for element in filterfalse(seen.__contains__, iterable):
                seen_add(element)
                yield element
        else:
            for element in iterable:
                k = key(element)
                if k not in seen:
                    seen_add(k)
                    yield element


__all__ = ["unique_everseen"]
