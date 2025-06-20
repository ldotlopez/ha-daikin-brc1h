"""Retriable tools for daikin_brc1h."""

# Copyright (C) 2019-2024 Luis López <luis@cuarentaydos.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.

import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from typing import Any

LOGGER = logging.getLogger(__name__)

AsyncCallable = Callable[..., Awaitable]  # Why doesn't python define this?


DEFAULT_RETRIES = 3
DEFAULT_DELAY = 0


def awaitable_retriable(
    allowed_exceptions: type | list[type] | None = None,
    n: int = DEFAULT_RETRIES,
    delay: float = DEFAULT_DELAY,
    recover_awaitable: AsyncCallable | None = None,
) -> Callable:
    """Decorator generator."""
    if allowed_exceptions is None:
        allowed_exceptions = []
    elif not isinstance(allowed_exceptions, list):
        allowed_exceptions = [allowed_exceptions]

    def decorator(awaitable: AsyncCallable) -> AsyncCallable:
        """Just a pre wrapper that acts as the real decorator."""

        @wraps(awaitable)
        async def wrapper(*args, **kwargs) -> Any:
            """Call main awaitable under the retry loop."""
            for x in range(n):
                try:
                    return await awaitable(*args, **kwargs)
                except Exception as e:
                    if e.__class__ not in allowed_exceptions:
                        raise  # not my job

                    LOGGER.debug(
                        f"{awaitable.__name__}({args}, {kwargs})"  # noqa: G004
                        f" failed at try #{x + 1} with {e!r}"
                    )
                    if x + 1 == n:
                        raise  # Max attempts

                    if recover_awaitable:
                        await recover_awaitable(*args, **kwargs)

                    if delay:
                        await asyncio.sleep(delay)

            excmsg = "this code should be unreacheable."
            raise RuntimeError(excmsg)

        return wrapper

    return decorator


@contextmanager
def awaitable_retriable_ctx(
    awaitable: AsyncCallable, *args, **kwargs
) -> Iterator[AsyncCallable]:
    """Wrapper around awaitable_retriable decorator to act as context manager."""
    yield awaitable_retriable(*args, **kwargs)(awaitable)


def make_awaitable_retriable(
    awaitable: AsyncCallable, *args, **kwargs
) -> AsyncCallable:
    """
    Wrapper around awaitable_retriable decorator to create the retriable
    awaitable.
    """  # noqa: D205
    return awaitable_retriable(*args, **kwargs)(awaitable)


async def main() -> None:
    """Test func."""

    async def test_fn() -> None:
        raise ValueError

    with awaitable_retriable_ctx(test_fn, allowed_exceptions=[ValueError]) as fn:
        print(await fn())  # noqa: T201


if __name__ == "__main__":
    LOGGER.setLevel(logging.DEBUG)
    asyncio.run(main())
