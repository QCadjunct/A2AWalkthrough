"""The Pydantic message object for a selected (vendor, model) pair.

Frozen and self-describing, consistent with WorkspaceState / WorkspaceResponse:
the wire form carries vendor and model; composed forms (fabric_id, litellm) are
derived, never stored. Built at the boundary; the cascade decorator validates
the pair before this is constructed.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ModelMessage(BaseModel):
    """A validated (vendor, model) selection that rides the wire."""

    model_config = ConfigDict(frozen=True)

    vendor: str
    model: str

    @property
    def fabric_id(self) -> str:
        """The ``Vendor|model`` form fabric uses — composed, not stored."""
        return f"{self.vendor}|{self.model}"

    @property
    def litellm(self) -> str:
        """The LiteLLM ``provider/model`` string — composed, not stored."""
        return f"{self.vendor.lower()}/{self.model}"

    def to_wire(self) -> dict:
        """Minimal wire form; vendor + model are the only authoritative fields."""
        return {"vendor": self.vendor, "model": self.model}

    @classmethod
    def from_wire(cls, d: dict) -> ModelMessage:
        """Rebuild from the wire."""
        return cls(vendor=d["vendor"], model=d["model"])
