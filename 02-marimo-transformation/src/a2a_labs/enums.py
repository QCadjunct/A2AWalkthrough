"""Enumerations (Enums) for the Agent-to-Agent (A2A) Walkthrough.

Standing rule: free-form strings are replaced by Enums wherever a value is drawn
from a fixed, known set. This eliminates a class of typo bugs (a mistyped value
fails at import, not at runtime) and gives editors autocomplete.

KISS here means "Keep It Simple and Standard": we use the standard-library
``enum.StrEnum`` (Python 3.11+), apply the standard constraint decorators
``@unique`` and ``@verify``, and — to keep responsibilities where they belong
(Single Responsibility Principle, SRP) — each Enum owns the facts derived from
it via ``@property`` and small methods, instead of letting other classes
(notably Settings) compose those facts. An AgentRole knows its own port; a
Provider knows how to prefix a model. Callers ask the Enum; they do not rebuild
the mapping.

Every acronym is spelled out on first use:
* A2A   - Agent-to-Agent (protocol)
* ADK   - Agent Development Kit (Google)
* MCP   - Model Context Protocol
* LLM   - Large Language Model
* URL   - Uniform Resource Locator
"""

from __future__ import annotations

from enum import IntEnum, StrEnum, unique, verify, UNIQUE

# Single source for the default bind host — referenced, never re-typed inline.
DEFAULT_HOST = "localhost"

# Single source for the agent domain suffix for request fully qualified names.
AGENT_DOMAIN = "agents.local"


@verify(UNIQUE)
class AgentPort(IntEnum):
    """Default ports for each agent server (mirrors example.env).

    ``@verify(UNIQUE)`` enforces at import that no two agents share a port.
    """

    POLICY = 9999
    RESEARCH = 9998
    PROVIDER = 9997
    HEALTHCARE = 9996


@unique
class OverrideDefault(IntEnum):
    """The runtime override gate for a tool invocation.

    ``FALSE`` (the default) uses the tool's discovered default triplet;
    ``TRUE`` uses the tool's registered override triplet. An IntEnum, not a raw
    bool, so the gate is a closed, named value like every other governed choice.
    """

    FALSE = 0
    TRUE = 1


@unique
class AgentRole(StrEnum):
    """The named agents in the multi-agent healthcare system.

    Each role owns the facts derived from it: its canonical port and how to
    build its default URL. This keeps that knowledge here (SRP), out of Settings.
    """

    POLICY = "policy"          # Insurance policy Question Answering (QA)
    RESEARCH = "research"      # Health research via Google Search
    PROVIDER = "provider"      # Provider lookup via MCP server
    HEALTHCARE = "healthcare"  # Orchestrator / concierge

    @property
    def port(self) -> AgentPort:
        """The canonical port for this role — owned by the role, not Settings."""
        return AgentPort[self.name]

    def default_url(self, host: str = DEFAULT_HOST) -> str:
        """Compose this role's base URL. The role builds it, not the caller."""
        return f"http://{host}:{int(self.port)}/"

    @property
    def request_surrogate(self) -> str:
        """A stable surrogate id for requests originating at this role.

        Owned by the role so no caller hand-types a literal like 'BGD-POLICY'.
        The name is intentionally plain — this is request identity, not data
        governance.
        """
        return f"req-{self.value}"

    @property
    def request_fqdn(self) -> str:
        """The fully qualified name this role answers under (host + domain)."""
        return f"{self.value}.{AGENT_DOMAIN}"


@unique
class Provider(StrEnum):
    """Which backend SERVES the model (distinct from who OWNS it; see Vendor)."""

    GEMINI = "gemini"          # Gemini Developer Application Programming Interface (API)
    VERTEX_AI = "vertex_ai"    # Google Vertex Artificial Intelligence (Vertex AI)

    def prefix(self, bare_model_name: str) -> str:
        """Prefix a bare model name for LiteLLM. The Provider owns the format."""
        return f"{self.value}/{bare_model_name}"


@unique
class TransportMode(StrEnum):
    """A2A / MCP transport mechanisms used in the labs."""

    STDIO = "stdio"          # MCP over standard input/output (local subprocess)
    JSONRPC = "jsonrpc"      # JavaScript Object Notation Remote Procedure Call
    STARLETTE = "starlette"  # Hypertext Transfer Protocol (HTTP) via Starlette


# Derived from AgentRole itself — no separately maintained dict to drift.
AGENT_PORTS: dict[AgentRole, AgentPort] = {r: r.port for r in AgentRole}

# Occam's Razor: the former flat ``Model`` Enum is folded into ``VendorModel``
# (vendors.py). One model representation, namespaced by owning vendor.
