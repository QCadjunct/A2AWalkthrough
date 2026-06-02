"""Configuration via Pydantic Version 2 (V2) settings.

Replaces the upstream ``helpers.setup_env`` (a bare ``load_dotenv`` plus
``nest_asyncio``) with a typed, validated settings object. The key feature is a
single toggle, ``provider``, that switches the whole stack between the Gemini
Developer Application Programming Interface (API) and Google Vertex Artificial
Intelligence (Vertex AI) without touching agent code.
"""

from __future__ import annotations

import warnings
from functools import lru_cache

import nest_asyncio
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from a2a_labs.enums import DEFAULT_HOST, AgentRole, Provider
from a2a_labs.vendors import VendorModel


class Settings(BaseSettings):
    """Typed application settings, populated from the environment or ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Provider selection (the single toggle) ---
    provider: Provider = Field(
        default=Provider.GEMINI,
        description="Which backend serves the Large Language Model (LLM).",
    )

    # --- Gemini Developer API ---
    gemini_api_key: str | None = Field(default=None, description="Gemini API key.")

    # --- Vertex AI ---
    google_cloud_project: str | None = Field(
        default=None, description="Google Cloud Platform (GCP) project identifier."
    )
    google_cloud_location: str = Field(
        default="global", description="Vertex AI location/region."
    )
    google_genai_use_vertexai: bool = Field(
        default=False, description="Tell google-genai / Agent Development Kit (ADK) to use Vertex AI."
    )

    # --- Network ---
    # Ports are owned by AgentRole (role.port); Settings only overrides the host.
    agent_host: str = Field(default=DEFAULT_HOST, description="Host all agents bind to.")

    @model_validator(mode="after")
    def _check_credentials(self) -> Settings:
        """Ensure the credentials needed by the selected provider are present."""
        if self.provider is Provider.GEMINI and not self.gemini_api_key:
            warnings.warn(
                "Provider is GEMINI but GEMINI_API_KEY is unset.", stacklevel=2
            )
        if self.provider is Provider.VERTEX_AI and not self.google_cloud_project:
            warnings.warn(
                "Provider is VERTEX_AI but GOOGLE_CLOUD_PROJECT is unset.",
                stacklevel=2,
            )
        return self

    def litellm_model(self, model: VendorModel) -> str:
        """Return the LiteLLM model string with the correct provider prefix.

        Composition is owned by the Enums: the Provider knows how to prefix, the
        model knows its bare name. Settings only supplies the active provider.
        Example: ``VendorModel.GEMINI_FLASH_LITE`` ->
        ``gemini/gemini-3.1-flash-lite-preview`` or the ``vertex_ai/`` form.
        """
        return self.provider.prefix(model.bare_name)

    def port_for(self, role: AgentRole) -> int:
        """The port for a role — owned by AgentRole, not rebuilt here."""
        return int(role.port)

    def url_for(self, role: AgentRole) -> str:
        """The base URL for a role — composed by the role, host from Settings."""
        return role.default_url(self.agent_host)


def setup_env() -> Settings:
    """Drop-in replacement for the upstream ``helpers.setup_env``.

    Applies ``nest_asyncio`` (needed for running async A2A code inside a
    notebook event loop), silences noisy warnings, and returns the validated
    Settings object so callers can use it directly.
    """
    nest_asyncio.apply()
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    return get_settings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance."""
    return Settings()  # type: ignore[call-arg]  # values come from the environment
