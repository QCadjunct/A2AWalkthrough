"""The tool menu — a tool's default and override triplets, gated at runtime.

At the Model Context Protocol (MCP) server level, each tool holds its triplets:
a **default** and an **override**, each a triplet of Enum pointers:

    (FQSN, Vendor, VendorModel)
      skill identity · who serves the model · which model

The vendor is singular per tool (the default and the override share one vendor)
so the menu does not explode into a vendor x model x skill cross product — the
override varies by skill and/or model within the one vendor, commonly keeping
the default's model and only choosing a different skill.

At runtime an ``OverrideDefault`` gate selects which triplet is in effect:
``FALSE`` (the default) uses the discovered default; ``TRUE`` uses the override.
The gate is the whole choice. ``invoke`` is non-mutating: it returns the
effective triplet and never changes the menu. The menu is immutable in-process;
it evolves only across a server restart.

Acronyms: MCP - Model Context Protocol; FQSN - Fully Qualified Skills Name.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from a2a_labs.enums import OverrideDefault
from a2a_labs.fqsn import FQSN
from a2a_labs.vendors import Vendor, VendorModel


class Triplet(BaseModel):
    """One menu option: three Enum pointers — skill, vendor, model.

    Lightweight by construction: the fields are Enum members, so a triplet is
    three references. ``model`` must be served by ``vendor`` (validated here).
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    fqsn: FQSN
    vendor: Vendor
    model: VendorModel

    @model_validator(mode="after")
    def _model_belongs_to_vendor(self) -> "Triplet":
        if self.model.vendor is not self.vendor:
            raise ValueError(
                f"model {self.model.name} is served by {self.model.vendor.name}, "
                f"not {self.vendor.name}"
            )
        return self

    def as_pointers(self) -> tuple[str, str, str]:
        """The wire form: three Enum-value tokens, nothing heavier."""
        return (self.fqsn.name, self.vendor.value, self.model.name)


class ToolMenu(BaseModel):
    """A tool's default and override triplets, sharing one vendor.

    Immutable in-process. ``invoke`` selects between the two by an
    ``OverrideDefault`` gate — the whole runtime choice — and mutates nothing.
    """

    model_config = ConfigDict(frozen=True)

    tool_name: str
    version: str
    default: Triplet
    override: Triplet

    @model_validator(mode="after")
    def _single_vendor(self) -> "ToolMenu":
        # Singular vendor per tool — no vendor x model x skill cross product.
        if self.default.vendor is not self.override.vendor:
            raise ValueError(
                f"tool {self.tool_name!r}: default vendor {self.default.vendor.name} "
                f"!= override vendor {self.override.vendor.name}; "
                f"a tool uses one vendor"
            )
        return self

    def invoke(self, gate: OverrideDefault = OverrideDefault.FALSE) -> Triplet:
        """Return the effective triplet for one invocation — non-mutating.

        ``FALSE`` (the default gate) returns the discovered default; ``TRUE``
        returns the override. The gate is the whole choice; neither triplet nor
        the menu is mutated.
        """
        return self.override if gate is OverrideDefault.TRUE else self.default

    def pointers(self) -> dict[str, tuple[str, str, str]]:
        """Both triplets as pointer tokens — the lightweight discovery form."""
        return {
            "default": self.default.as_pointers(),
            "override": self.override.as_pointers(),
        }


def menu_for(tool_name: str, version: str, default: Triplet, override: Triplet) -> ToolMenu:
    """Build a tool's menu from its default and override triplets (one vendor)."""
    return ToolMenu(tool_name=tool_name, version=version, default=default, override=override)
