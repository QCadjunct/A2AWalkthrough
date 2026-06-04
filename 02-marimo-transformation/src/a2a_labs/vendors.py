"""Cascading Vendor -> Model validation, with standard Enum constraints.

Single source of truth for models. The former flat ``Model`` Enum folded in here
(Occam: one model representation). NO HARDCODED STRINGS: a model's vendor is a
real ``Vendor`` member stored on the enum, not a ``"vendor:"`` prefix parsed back
out of a literal. The bare name is the only string a model declares, and even
that is the model's single datum.

We never duplicate a value that already exists as an Enum member. ``Vendor`` is
referenced (``Vendor.GOOGLE``), never re-typed as ``"google"``.

Standard-library constraint decorators applied to every Enum:
* ``@unique`` - no two members may share a value (forbids accidental aliases).

Vendor (who OWNS the model) is distinct from Provider (who SERVES it).

Acronyms: LLM - Large Language Model; API - Application Programming Interface.
"""

from __future__ import annotations

from enum import StrEnum, Enum, unique

from pydantic import BaseModel, ConfigDict, model_validator


@unique
class Vendor(StrEnum):
    """The organization that OWNS a family of models."""

    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    META = "meta"
    MISTRAL = "mistral"


@unique
class VendorModel(Enum):
    """Every known model. Its value is a (Vendor, bare_name) pair.

    The vendor is a real ``Vendor`` member, not a string prefix. There is no
    ``"google:"`` literal to drift from ``Vendor.GOOGLE`` — the reference IS the
    vendor. ``@unique`` still forbids two members sharing the same pair.
    """

    # (owning Vendor member, bare model name)
    GEMINI_FLASH_LITE = (Vendor.GOOGLE, "gemini-2.5-flash-lite")
    GEMINI_PRO = (Vendor.GOOGLE, "gemini-2.5-pro")
    GEMINI_FLASH_2_5 = (Vendor.GOOGLE, "gemini-2.5-flash")
    CLAUDE_OPUS = (Vendor.ANTHROPIC, "claude-opus-4-8")
    CLAUDE_SONNET = (Vendor.ANTHROPIC, "claude-sonnet-4-6")
    CLAUDE_HAIKU = (Vendor.ANTHROPIC, "claude-haiku-4-5")
    GPT_5 = (Vendor.OPENAI, "gpt-5")
    GPT_5_MINI = (Vendor.OPENAI, "gpt-5-mini")
    LLAMA_4_MAVERICK = (Vendor.META, "llama-4-maverick")
    LLAMA_4_SCOUT = (Vendor.META, "llama-4-scout")
    MISTRAL_LARGE = (Vendor.MISTRAL, "mistral-large-2")

    def __init__(self, vendor: Vendor, bare_name: str) -> None:
        # The "object as enum value" pattern: store the structured parts so the
        # vendor is a reference, never a parsed string.
        self._vendor = vendor
        self._bare_name = bare_name

    @property
    def vendor(self) -> Vendor:
        """The owning vendor — a real Vendor member, not parsed from a string."""
        return self._vendor

    @property
    def bare_name(self) -> str:
        """The model name (the model's single declared string)."""
        return self._bare_name

    @property
    def qualified(self) -> str:
        """Namespaced name, COMPOSED from the parts (never stored as a literal)."""
        return f"{self.vendor.value}:{self.bare_name}"


# Occam alias: same Enum, not a second representation.
Model = VendorModel


def models_for(vendor: Vendor) -> list[VendorModel]:
    """All models owned by a vendor — derived from VendorModel, no separate dict."""
    return [m for m in VendorModel if m.vendor is vendor]


# Ownership view, derived (never hand-maintained).
VENDOR_MODELS: dict[Vendor, list[VendorModel]] = {v: models_for(v) for v in Vendor}


class VendorModelSelection(BaseModel):
    """A validated (vendor, model) pair — the cascade in one object.

    Both fields are typed by their Enums (never strings). Construction fails
    unless the model is owned by the vendor.
    """

    model_config = ConfigDict(frozen=True)

    vendor: Vendor
    model: VendorModel

    @model_validator(mode="after")
    def _cascade(self) -> VendorModelSelection:
        if self.model.vendor is not self.vendor:
            allowed = [m.bare_name for m in models_for(self.vendor)]
            raise ValueError(
                f"{self.model.bare_name!r} is not a {self.vendor.value} model. "
                f"Valid {self.vendor.value} models: {allowed}"
            )
        return self

    @classmethod
    def for_model(cls, model: VendorModel) -> VendorModelSelection:
        """Build from a model alone; the vendor is its own field, never wrong."""
        return cls(vendor=model.vendor, model=model)

    def litellm_string(self, serving_provider) -> str:
        """Compose the LiteLLM string. ``serving_provider`` is a Provider Enum."""
        # Accept a Provider Enum (preferred) or its .value; never a bare literal.
        prefix = getattr(serving_provider, "value", serving_provider)
        return f"{prefix}/{self.model.bare_name}"
