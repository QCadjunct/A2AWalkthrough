"""Fully Qualified Skills Name (FQSN) — a polymorphic governed skill identity.

A FQSN names a skill. The governance is invariant; the substrate is a pluggable
adapter (the Hexagonal ports-and-adapters pattern at the naming layer). A FQSN is
NOT a filesystem path and NOT a dotted ``schema.skill`` string — those are two of
its materializations. The identity is the thing; the substrate is how it is
stored and resolved.

Three materializations exist (ADR-029-AMD4):
  1. Filesystem registry — a hierarchical folder taxonomy holding the skill
     trifecta (``system.md`` / ``system.yaml`` / ``system.toon``), surviving the
     Fabric destructive update cycle. Implemented here as ``FilesystemAdapter``.
  2. Standalone database taxonomy — governed as a domain taxonomy in a database.
  3. Multiple interrelated taxonomies — related through Domain-Driven Database
     Design (D⁴) governance.

This module ships the filesystem adapter for the labs. The database and
multi-taxonomy adapters are present as the port they plug into, not implemented.

Acronyms: FQSN - Fully Qualified Skills Name; D⁴ - Domain-Driven Database Design.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

# The skill trifecta filenames — the three-file skill standard. One source.
TRIFECTA = ("system.md", "system.yaml", "system.toon")


class FQSN(BaseModel):
    """A Fully Qualified Skills Name — the governed skill identity.

    Substrate-agnostic: the same identity whether it lives in the filesystem,
    one database taxonomy, or many. ``segments`` is the hierarchical path of the
    name (e.g. ``("policy", "insurance_coverage")``); ``name`` is the dotted
    for display, never the storage form.
    """

    model_config = ConfigDict(frozen=True)

    segments: tuple[str, ...]

    @classmethod
    def parse(cls, dotted: str) -> "FQSN":
        """Build a FQSN from a dotted display name (e.g. 'policy.insurance_coverage')."""
        parts = tuple(part for part in dotted.split(".") if part)
        if not parts:
            raise ValueError("FQSN requires at least one non-empty segment")
        return cls(segments=parts)

    @property
    def name(self) -> str:
        """Dotted display rendering — for showing, not for storage."""
        return ".".join(self.segments)

    def __str__(self) -> str:
        return self.name


class SkillTrifecta(BaseModel):
    """The resolved skill: the three governed files of a materialized FQSN."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    fqsn: FQSN
    system_md: Path
    system_yaml: Path
    system_toon: Path


@runtime_checkable
class SkillResolver(Protocol):
    """The port: resolve a FQSN to its skill trifecta, regardless of substrate.

    Every adapter (filesystem, database, multi-taxonomy) implements this. The
    caller depends on this protocol, never on a concrete substrate.
    """

    def resolve(self, fqsn: FQSN) -> SkillTrifecta:
        """Materialize the FQSN into its trifecta, or raise if it is unknown."""
        ...

    def exists(self, fqsn: FQSN) -> bool:
        """Whether this substrate can resolve the FQSN."""
        ...


class FilesystemAdapter:
    """Filesystem materialization: FQSN -> a hierarchical trifecta folder.

    The hierarchy mirrors the name's segments under a root (e.g.
    ``skills/policy/insurance_coverage/`` for ``FQSN("policy","insurance_coverage")``),
    and the folder holds the trifecta. This is the form that survives Fabric's
    destructive pattern update.
    """

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    def _folder(self, fqsn: FQSN) -> Path:
        return self._root.joinpath(*fqsn.segments)

    def exists(self, fqsn: FQSN) -> bool:
        folder = self._folder(fqsn)
        return folder.is_dir() and all((folder / f).is_file() for f in TRIFECTA)

    def resolve(self, fqsn: FQSN) -> SkillTrifecta:
        folder = self._folder(fqsn)
        if not folder.is_dir():
            raise FileNotFoundError(f"FQSN {fqsn} not found at {folder}")
        md, yaml, toon = (folder / f for f in TRIFECTA)
        missing = [f for f in (md, yaml, toon) if not f.is_file()]
        if missing:
            raise FileNotFoundError(
                f"FQSN {fqsn} incomplete trifecta; missing {[m.name for m in missing]}"
            )
        return SkillTrifecta(fqsn=fqsn, system_md=md, system_yaml=yaml, system_toon=toon)


class DatabaseAdapter:
    """Database-taxonomy materialization of FQSN.

    Present as the port it plugs into; the governed in-database taxonomy is
    Domain-Driven Database Design (D⁴) work and is not implemented in the labs.
    """

    def exists(self, fqsn: FQSN) -> bool:  # noqa: ARG002
        raise NotImplementedError("FQSN database adapter is not part of the labs")

    def resolve(self, fqsn: FQSN) -> SkillTrifecta:  # noqa: ARG002
        raise NotImplementedError("FQSN database adapter is not part of the labs")
