"""A2A protocol bridge + governed Agent Card builder.

Two responsibilities, both about making the workspace objects first-class
citizens of the Agent-to-Agent (A2A) protocol used in Labs 1-8:

1. Bridge functions that embed a WorkspaceState / WorkspaceResponseObject into
   the A2A message envelope (Message / Task / Artifact) and extract it back —
   the A2A analogue of WorkspaceState.embed_in_message() for the Natural
   Language Interaction Protocol (NLIP).

2. A governed Agent Card builder. Upstream, each lab hand-writes an AgentCard
   with free-form strings. Here the card is built from typed Enums and a Fully
   Qualified Skill Name (FQSN) registry, so identity, skills, and addressing all
   come from one source of truth and the SAME card builder serves all of Labs
   1-8.

Acronyms: A2A - Agent-to-Agent; FQSN - Fully Qualified Skill Name;
ADK - Agent Development Kit; URL - Uniform Resource Locator; JSON - JavaScript
Object Notation.

NOTE: a2a-sdk types are imported lazily inside functions so this module imports
even in environments where the heavy SDK is not installed (e.g. running unit
tests on the workspace objects alone).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, Field

from a2a_labs.enums import AgentRole
from a2a_labs.workspace import (
    ResponseStatus,
    WorkspaceResponseObject,
    WorkspaceState,
)

if TYPE_CHECKING:
    from a2a.types import AgentCard


# ===========================================================================
# FQSN registry — the governed skill catalog
# ===========================================================================
class SkillSpec(BaseModel):
    """One Fully Qualified Skill Name (FQSN) registry entry.

    Upstream, an AgentSkill is assembled inline per agent with free-form id,
    name, tags, and examples. Here a skill is a registry record with a fully
    qualified id, so the SAME skill definition can be referenced by an agent's
    card, by a WorkspaceState.skill_id request, and by the orchestrator's
    routing — without re-typing strings.
    """

    fqsn: str = Field(..., description="Fully Qualified Skill Name, e.g. 'policy.insurance_coverage'.")
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)

    def to_agent_skill(self) -> Any:
        """Materialize this registry entry as an A2A AgentSkill."""
        from a2a.types import AgentSkill

        # The short id is the segment after the last dot of the FQSN.
        short_id = self.fqsn.rsplit(".", 1)[-1]
        return AgentSkill(
            id=short_id,
            name=self.name,
            description=self.description,
            tags=self.tags,
            examples=self.examples,
        )


# The registry: every skill in the system, defined once. Labs reference these
# by FQSN instead of re-declaring AgentSkill objects.
SKILL_REGISTRY: dict[AgentRole, list[SkillSpec]] = {
    AgentRole.POLICY: [
        SkillSpec(
            fqsn="policy.insurance_coverage",
            name="Insurance coverage",
            description="Provides information about insurance coverage options and details.",
            tags=["insurance", "coverage"],
            examples=["What does my policy cover?", "Are mental health services included?"],
        )
    ],
    AgentRole.RESEARCH: [
        SkillSpec(
            fqsn="research.health_lookup",
            name="Health research",
            description="Provides healthcare information using up-to-date web resources.",
            tags=["healthcare", "research", "web"],
            examples=["What are treatments for X?", "What are the symptoms of Y?"],
        )
    ],
    AgentRole.PROVIDER: [
        SkillSpec(
            fqsn="provider.find_providers",
            name="Find healthcare providers",
            description="Finds providers based on location and specialty.",
            tags=["healthcare", "providers", "doctor"],
            examples=["Psychiatrists near Boston, MA?", "Find a pediatrician in Springfield, IL."],
        )
    ],
    AgentRole.HEALTHCARE: [
        SkillSpec(
            fqsn="healthcare.concierge",
            name="Healthcare concierge",
            description="Coordinates policy, research, and provider agents to answer a question.",
            tags=["healthcare", "orchestrator", "concierge"],
            examples=["How do I get therapy near me and what does insurance cover?"],
        )
    ],
}


# ===========================================================================
# Governed Agent Card builder — one builder for all of Labs 1-8
# ===========================================================================
def build_agent_card(
    role: AgentRole,
    settings: Any,
    *,
    streaming: bool = False,
    version: str = "1.0.0",
    name_override: Optional[str] = None,
    description_override: Optional[str] = None,
) -> AgentCard:
    """Build a conformant A2A AgentCard for a role from the governed registry.

    Replaces the per-lab hand-written card. Skills come from SKILL_REGISTRY, the
    URL comes from settings.url_for(role), capabilities are explicit. The same
    function produces the card for the Policy agent (Lab 2), the Research agent
    (Lab 4, when not auto-generated by ADK), the Provider agent (Lab 6), and the
    orchestrator (Lab 8).
    """
    from a2a.types import AgentCapabilities, AgentCard

    specs = SKILL_REGISTRY.get(role, [])
    skills = [spec.to_agent_skill() for spec in specs]

    default_names = {
        AgentRole.POLICY: "InsurancePolicyCoverageAgent",
        AgentRole.RESEARCH: "HealthResearchAgent",
        AgentRole.PROVIDER: "HealthcareProviderAgent",
        AgentRole.HEALTHCARE: "HealthcareConciergeAgent",
    }
    name = name_override or default_names.get(role, f"{role.value.title()}Agent")
    description = description_override or (specs[0].description if specs else name)

    return AgentCard(
        name=name,
        description=description,
        url=settings.url_for(role),
        version=version,
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=streaming),
        skills=skills,
    )


# ===========================================================================
# A2A message bridge — embed / extract the workspace payload
# ===========================================================================
def state_to_message(state: WorkspaceState, instruction: str) -> Any:
    """Embed a WorkspaceState into an A2A user Message.

    The A2A analogue of WorkspaceState.embed_in_message() for NLIP. The protocol
    carries a structured text part; the workspace identity rides in its data.
    """
    from a2a.utils import new_agent_text_message

    # The instruction is the visible text; the workspace payload travels as a
    # JSON string the receiving executor can parse back out.
    envelope = {"instruction": instruction, "workspace": state.to_content()}
    return new_agent_text_message(json.dumps(envelope))


def response_to_artifact_text(response: WorkspaceResponseObject) -> str:
    """Serialize a response payload for return inside an A2A Artifact/Message.

    Lab 2's executor returns text via new_agent_text_message; Lab 6 returns
    Artifacts. Either way the response object serializes to this JSON string so
    the client (Lab 3) or orchestrator (Lab 8) can reconstruct it and verify
    correlation_id against the original request's PAIR_HASH.
    """
    return response.to_wire()


def response_from_text(text: str) -> Optional[WorkspaceResponseObject]:
    """Reconstruct a WorkspaceResponseObject from an A2A message/artifact text.

    Returns None if the text is a plain string answer (an upstream agent that
    does not yet emit workspace objects), so adoption is incremental: a governed
    client can talk to both governed and ungoverned agents.
    """
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict) or data.get("direction") != "response":
        return None
    try:
        return WorkspaceResponseObject(**data)
    except Exception:  # noqa: BLE001 - malformed payload -> treat as plain text
        return None


def verify_correlation(
    request: WorkspaceState, response: WorkspaceResponseObject
) -> bool:
    """Confirm a response belongs to its request by identity, not convention."""
    return response.correlation_id == request.blake3_pair_hash
