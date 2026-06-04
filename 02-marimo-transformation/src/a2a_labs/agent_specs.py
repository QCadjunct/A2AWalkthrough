"""Governed agent specifications — the segmented system as one validated registry.

Each upstream agent script hardcoded its own identity: an ``AgentSkill`` built
from inline strings, a model literal, a port via ``os.getenv``, and (for the
orchestrator) the set of agents it hands off to. This module folds all of that
into one ``AgentSpec`` per role, where every field is drawn from a governed
source — ``AgentRole`` (port/url), ``AgentFramework``, ``VendorModel``, and
``McpTool`` — and cross-object invariants are enforced by Pydantic decorators.

The result: the four-agent call graph and every skill/model/tool binding is a
single navigable registry, with zero free-form strings except the human-facing
description and examples (which are content, not identity).

Acronyms: A2A - Agent-to-Agent; MCP - Model Context Protocol; FQSN - Fully
Qualified Skills Name; SRP - Single Responsibility Principle.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from a2a_labs.agent_framework import AgentFramework
from a2a_labs.enums import AgentRole
from a2a_labs.fqsn import FQSN
from a2a_labs.mcp_tools import McpTool
from a2a_labs.vendors import VendorModel


class SkillSpec(BaseModel):
    """An agent's advertised skill — identity governed, content free.

    The skill ``identity`` is an FQSN (governed), not the upstream flat string
    id. ``name``/``description``/``examples`` are human content. ``mcp_tool`` is
    set only when the skill is backed by an MCP tool, and is an Enum member.
    """

    model_config = ConfigDict(frozen=True)

    identity: FQSN
    name: str
    description: str
    examples: tuple[str, ...] = ()
    mcp_tool: McpTool | None = None

    @property
    def id(self) -> str:
        """The A2A AgentSkill id — derived from the FQSN, never re-typed."""
        return self.identity.name


class AgentSpec(BaseModel):
    """One agent in the system: role, framework, skill, model, and handoffs.

    Every field is Enum/Model-governed. Cross-object validators enforce the
    invariants the upstream scripts left to convention:
      * the model must be servable (it carries its own vendor, validated in
        VendorModel) — referenced here, never a string;
      * handoff targets must be other known roles, never the agent itself;
      * an MCP-backed skill must name a tool whose server is known.
    """

    model_config = ConfigDict(frozen=True)

    role: AgentRole
    framework: AgentFramework
    skill: SkillSpec
    model: VendorModel
    description: str
    handoffs: tuple[AgentRole, ...] = ()  # roles this agent calls over A2A

    @model_validator(mode="after")
    def _no_self_handoff(self) -> "AgentSpec":
        if self.role in self.handoffs:
            raise ValueError(f"{self.role.value} cannot hand off to itself")
        return self

    @model_validator(mode="after")
    def _handoffs_distinct(self) -> "AgentSpec":
        if len(set(self.handoffs)) != len(self.handoffs):
            raise ValueError(f"{self.role.value}: duplicate handoff target")
        return self

    # --- derived facts, owned here (SRP), composed never re-typed ---
    @property
    def url(self) -> str:
        """This agent's base URL — from the role, host left to Settings."""
        return self.role.default_url()

    @property
    def port(self) -> int:
        return int(self.role.port)

    def litellm_model(self, settings) -> str:
        """The provider-prefixed model string — composed via Settings/Enums."""
        return settings.litellm_model(self.model)
