"""Decorators for professional, self-documenting lab structure.

These give each lab step a consistent, inspectable wrapper instead of bare
function calls:

* ``@lab_step`` prints a labelled banner and times the step.
* ``@async_lab_step`` is the coroutine equivalent.
* ``@requires`` asserts that prerequisite agent servers are reachable before a
  step runs, turning a confusing connection-refused traceback into a clear
  message about which server to start first.

Acronyms: A2A - Agent-to-Agent; URL - Uniform Resource Locator.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

import httpx

P = ParamSpec("P")
R = TypeVar("R")


def lab_step(title: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Wrap a synchronous lab step with a labelled, timed banner."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            print(f"\u25b6  {title}")
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            print(f"\u2713  {title}  ({elapsed:.2f}s)")
            return result

        return wrapper

    return decorator


def async_lab_step(
    title: str,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Wrap an asynchronous lab step with a labelled, timed banner."""

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            print(f"\u25b6  {title}")
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            print(f"\u2713  {title}  ({elapsed:.2f}s)")
            return result

        return wrapper

    return decorator


def requires(*urls: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Assert prerequisite agent servers are reachable before running.

    Each Uniform Resource Locator (URL) is probed at its Agent Card well-known
    path. If any server is down, raise a clear error naming the missing one
    instead of letting a connection-refused error surface deep in the stack.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for url in urls:
                card_url = url.rstrip("/") + "/.well-known/agent-card.json"
                try:
                    resp = httpx.get(card_url, timeout=3.0)
                    resp.raise_for_status()
                except Exception as exc:  # noqa: BLE001 - re-raised with context
                    msg = (
                        f"Prerequisite agent at {url} is not reachable "
                        f"({exc}). Start it first, e.g. "
                        f"`uv run a2a_policy_agent.py`."
                    )
                    raise RuntimeError(msg) from exc
            return func(*args, **kwargs)

        return wrapper

    return decorator
