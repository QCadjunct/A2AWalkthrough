"""A2A-compliant workspace message objects.

This module brings the ACES WorkspaceState concept into Agent-to-Agent (A2A)
protocol compliance, aligned with Labs 1-8. It defines:

* WorkspaceEnvelope  - the COMMON base both request and response share. Carries
  the BLAKE3 identity chain (Business Glossary Definition (BGD) surrogate,
  Fully Qualified Domain Name (FQDN), BLAKE3 PAIR_HASH) that every message in a
  chain inherits. This is the "common message object."
* WorkspaceState           - the REQUEST-side informative payload (existing).
* WorkspaceResponseObject  - the RESPONSE-side mirror (new).

Normative / Informative framing (unchanged from the TC56 work):
    NLIPMessageBase   -> normative abstract (what SHALL exist)
      NLIPMessage     -> informative concrete (one valid fulfillment)
        content       -> carries a WorkspaceEnvelope subclass
          Workspace*  -> informative application content, invisible to protocol

A2A alignment: where the Natural Language Interaction Protocol (NLIP) wraps the
payload in an NLIPMessage, the A2A protocol wraps it in a Message / Task /
Artifact. These objects ride inside BOTH envelopes unchanged, because the
identity chain is payload, not protocol. That is the whole point: the object is
protocol-agnostic, so the same WorkspaceState works in Lab 2's hand-built A2A
server, Lab 4's Agent Development Kit (ADK) agent, Lab 6's LangGraph agent, and
Lab 8's BeeAI orchestrator.

Acronyms: A2A - Agent-to-Agent; NLIP - Natural Language Interaction Protocol;
BGD - Business Glossary Definition; FQDN - Fully Qualified Domain Name;
FQSN - Fully Qualified Skill Name; WORM - Write Once Reuse Many; ADK - Agent
Development Kit; JSON - JavaScript Object Notation.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Identity helper — the BLAKE3 PAIR_HASH (SHA-256 fallback if blake3 absent)
# ---------------------------------------------------------------------------
def pair_hash(bgd_surrogate: str, fqdn: str) -> str:
    """Return the deterministic identity hash for a (BGD, FQDN) pair.

    Uses BLAKE3 when available; falls back to SHA-256 so the module imports and
    runs everywhere (the labs do not ship blake3 by default). The hash format is
    stable either way: it is the spoke identity in the D-to-the-4th hub-spoke
    governance chain.
    """
    payload = f"{bgd_surrogate}|{fqdn}".encode()
    try:
        import blake3  # type: ignore

        return "blake3:" + blake3.blake3(payload).hexdigest()
    except ImportError:
        return "sha256:" + hashlib.sha256(payload).hexdigest()


class MessageDirection(str, Enum):
    """Whether a workspace payload is a request or a response.

    Replaces a free-form string, per the standing Enum rule.
    """

    REQUEST = "request"
    RESPONSE = "response"


class ResponseStatus(str, Enum):
    """Outcome of an agent's handling of a request."""

    OK = "ok"
    PARTIAL = "partial"        # some sub-tasks answered, some not
    NEED_INPUT = "need_input"  # agent requires clarification
    ERROR = "error"
    UNKNOWN = "unknown"        # the policy-agent "I don't know" path


# ===========================================================================
# COMMON BASE — the shared message object
# ===========================================================================
class WorkspaceEnvelope(BaseModel):
    """COMMON base for every workspace payload, request or response.

    This is the "common message object" shared across the Model Context Protocol
    (MCP) client/server boundary and the A2A agent/agent boundary. Both the
    request payload (WorkspaceState) and the response payload
    (WorkspaceResponseObject) inherit the identity chain from here, so a reply
    can always be traced back to its request by PAIR_HASH.

    Write Once Reuse Many (WORM): frozen=True. Once created, the identity is
    immutable — you build a new envelope for the next hop, you never mutate one.
    """

    model_config = ConfigDict(frozen=True, use_enum_values=True)

    # --- Identity chain (the governance spine) ---
    bgd_surrogate: str = Field(..., description="Business Glossary Definition surrogate (the hub).")
    fqdn: str = Field(..., description="Fully Qualified Domain Name (the spoke target).")
    blake3_pair_hash: str = Field(default="", description="Identity hash of (BGD, FQDN); auto-filled.")

    # --- Chain / provenance ---
    direction: MessageDirection = Field(..., description="request or response.")
    chain_depth: int = Field(default=0, ge=0, description="Hops from the originating user message.")
    correlation_id: str = Field(default="", description="Links a response to its originating request.")
    created_at: str = Field(default="", description="ISO 8601 UTC timestamp; auto-filled.")

    @model_validator(mode="before")
    @classmethod
    def _fill_derived(cls, data: Any) -> Any:
        """Fill the identity hash and timestamp before the frozen model is built.

        Runs in 'before' mode so it can populate derived fields even though the
        instance is frozen (you cannot assign to a frozen instance afterward).
        Only fills when absent, so an explicitly supplied hash/timestamp wins.
        """
        if not isinstance(data, dict):
            return data
        if not data.get("blake3_pair_hash") and data.get("bgd_surrogate") and data.get("fqdn"):
            data["blake3_pair_hash"] = pair_hash(data["bgd_surrogate"], data["fqdn"])
        if not data.get("created_at"):
            data["created_at"] = datetime.now(timezone.utc).isoformat()
        return data

    # --- A2A bridge: payload <-> the protocol's content field ---
    def to_content(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for an A2A/NLIP content field.

        The protocol (A2A or NLIP) sees only this JSON object. What it means is
        above the normative surface. This is the single serialization point both
        envelopes share.
        """
        return self.model_dump(exclude_none=True)

    def to_wire(self) -> str:
        """INFORMATIVE: conformant JSON wire form."""
        return self.model_dump_json(exclude_none=True)


# ===========================================================================
# REQUEST side — WorkspaceState (now inheriting the common base)
# ===========================================================================
class WorkspaceState(WorkspaceEnvelope):
    """INFORMATIVE: the request-side ACES session context.

    Unchanged in spirit from the TC56 design: it carries the task content into
    an agent. Now it inherits the identity chain from WorkspaceEnvelope and is
    pinned to direction=REQUEST, so its A2A-compliant reply
    (WorkspaceResponseObject) can be matched back to it by correlation_id /
    PAIR_HASH.
    """

    direction: MessageDirection = Field(default=MessageDirection.REQUEST, frozen=True)
    task_content: Any = Field(..., description="The instruction or payload for the agent.")
    skill_id: Optional[str] = Field(
        default=None,
        description="Fully Qualified Skill Name (FQSN) the request targets, if any.",
    )

    def respond(
        self,
        result: Any,
        status: ResponseStatus = ResponseStatus.OK,
        source_agent: str = "",
    ) -> WorkspaceResponseObject:
        """Build the matching A2A-compliant response, preserving identity.

        This is the request->response link: the response inherits the same BGD,
        FQDN, and PAIR_HASH, increments chain_depth, and sets correlation_id to
        this request's PAIR_HASH so the orchestrator (Lab 8) can attribute every
        answer to the request that produced it.
        """
        return WorkspaceResponseObject(
            bgd_surrogate=self.bgd_surrogate,
            fqdn=self.fqdn,
            chain_depth=self.chain_depth + 1,
            correlation_id=self.blake3_pair_hash,
            result=result,
            status=status,
            source_agent=source_agent,
            answered_skill_id=self.skill_id,
        )


# ===========================================================================
# RESPONSE side — WorkspaceResponseObject (the new mirror)
# ===========================================================================
class WorkspaceResponseObject(WorkspaceEnvelope):
    """INFORMATIVE: the response-side mirror of WorkspaceState.

    The structural twin of the request payload. It rides back inside an A2A
    Artifact (or a direct Message) exactly as WorkspaceState rides in. Because
    it shares the common base, a client or orchestrator can verify a reply
    belongs to its request by comparing correlation_id to the request's
    PAIR_HASH — provenance is structural, not by convention.
    """

    direction: MessageDirection = Field(default=MessageDirection.RESPONSE, frozen=True)
    result: Any = Field(..., description="The agent's answer payload.")
    status: ResponseStatus = Field(default=ResponseStatus.OK, description="Outcome of handling.")
    source_agent: str = Field(default="", description="Name of the agent that produced this (Lab 8 attribution).")
    answered_skill_id: Optional[str] = Field(
        default=None, description="The FQSN that was actually exercised."
    )

    @property
    def is_terminal(self) -> bool:
        """True if this response needs no further agent hop."""
        return self.status in (ResponseStatus.OK, ResponseStatus.ERROR, ResponseStatus.UNKNOWN)
