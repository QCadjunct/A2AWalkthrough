"""WORM, Enum-keyed cascade governance.

A ``Cascade`` is a Write Once Reuse Many (WORM) governance registry: it pairs a
parent vocabulary with a child vocabulary over a containment mapping (parent ->
[valid children]), and validates that pairing on any method it guards. The
parent and child are ``CascadeKey`` Enum members — never string literals — so
the relationship a cascade governs is itself drawn from a closed, typed set.

Built once at import, a ``Cascade`` is immutable and reused across every lab:
the data is frozen, no attribute can be reassigned. This mirrors the foundation's
hub-spoke discipline — the registry is the write-once hub; every guarded method
is a reuse-many spoke.

The guard binds arguments against the decorated function's real signature, so a
pair is validated whether passed positionally or by keyword, and a parameter
named by a ``CascadeKey`` that does not exist on the function fails at DECORATION
time (import), not at call time.

Acronyms: WORM - Write Once Reuse Many.
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Mapping
from enum import StrEnum, unique
from types import MappingProxyType


@unique
class CascadeKey(StrEnum):
    """The governed parameter names a cascade may bind.

    A member's value is the parameter name it binds on a decorated function
    (e.g. ``CascadeKey.VENDOR`` binds the ``vendor`` parameter). Closed set:
    a cascade can only govern a relationship named here.
    """

    VENDOR = "vendor"
    MODEL = "model"
    ROLE = "role"
    SKILL = "skill"
    TOPIC = "topic"
    PROFILE = "profile"


class Cascade:
    """A WORM governance registry: parent CascadeKey -> child CascadeKey over data."""

    __slots__ = ("_parent", "_child", "_data")

    def __init__(
        self,
        parent: CascadeKey,
        child: CascadeKey,
        data: Mapping[str, list[str]],
    ) -> None:
        if not isinstance(parent, CascadeKey) or not isinstance(child, CascadeKey):
            raise TypeError(
                "parent and child must be CascadeKey members, not strings"
            )
        if not data:
            raise ValueError("Cascade registry cannot be empty")
        object.__setattr__(self, "_parent", parent)
        object.__setattr__(self, "_child", child)
        # WORM: deep-freeze the data (read-only mapping of immutable tuples).
        frozen = {key: tuple(values) for key, values in data.items()}
        object.__setattr__(self, "_data", MappingProxyType(frozen))

    def __setattr__(self, *_: object) -> None:
        raise AttributeError("Cascade is Write Once Reuse Many; it is immutable")

    def __delattr__(self, *_: object) -> None:
        raise AttributeError("Cascade is Write Once Reuse Many; it is immutable")

    @property
    def parent(self) -> CascadeKey:
        return self._parent

    @property
    def child(self) -> CascadeKey:
        return self._child

    def children(self, parent_value: str) -> tuple[str, ...]:
        """Cascade query: every child the parent value makes available."""
        return self._data.get(parent_value, ())

    def parents(self) -> tuple[str, ...]:
        """Every parent value in the registry."""
        return tuple(self._data)

    def validate(self, parent_value: str, child_value: str) -> None:
        """Raise a named error unless ``parent_value`` contains ``child_value``."""
        if parent_value not in self._data:
            raise ValueError(
                f"unknown {self._parent.value} {parent_value!r}. "
                f"Known: {list(self._data)}"
            )
        if child_value not in self._data[parent_value]:
            raise ValueError(
                f"{child_value!r} is not a {parent_value} {self._child.value}. "
                f"{parent_value} {self._child.value}s: {list(self._data[parent_value])}"
            )

    def guard(self, func):
        """Decorate ``func`` so its (parent, child) arguments are validated.

        Fails at decoration time if ``func`` lacks a parameter named by either
        CascadeKey; validates the pair at call time, binding by signature so
        positional and keyword calls both validate.
        """
        sig = inspect.signature(func)
        for key in (self._parent, self._child):
            if key.value not in sig.parameters:
                raise TypeError(
                    f"@guard: {func.__name__}() has no parameter "
                    f"{key.value!r} (from CascadeKey.{key.name}); "
                    f"its parameters are {list(sig.parameters)}"
                )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            self.validate(
                bound.arguments[self._parent.value],
                bound.arguments[self._child.value],
            )
            return func(*args, **kwargs)

        return wrapper
