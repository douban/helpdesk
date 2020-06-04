# coding: utf-8

from datetime import datetime, timedelta
import functools

from cached_property import cached_property, cached_property_with_ttl  # NOQA


def timed_cache(**timedelta_kwargs):
    def _wrapper(f):
        update_delta = timedelta(**timedelta_kwargs)
        next_update = datetime.utcnow() - update_delta
        # Apply @lru_cache to f with no cache size limit
        f = functools.lru_cache(maxsize=128)(f)

        @functools.wraps(f)
        def _wrapped(*args, **kwargs):
            nonlocal next_update
            now = datetime.utcnow()
            if now >= next_update:
                f.cache_clear()
                next_update = now + update_delta
            return f(*args, **kwargs)

        return _wrapped

    return _wrapper
