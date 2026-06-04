"""The system registry — the four agents as one validated call graph.

This is where the segmented upstream system becomes one object. The four
``AgentSpec`` instances are assembled once (Write Once Reuse Many — WORM), and a
registry-level validator proves the call graph is closed: every handoff target
is a registered role. Built at import; immutable; navigated, never copied.

The only free-form strings are human content (descriptions, examples). Every
identity — role, framework, model, MCP tool, skill FQSN — is an Enum or governed
model reference.

Acronyms: A2A - Agent-to-Agent; MCP - Model Context Protocol; WORM - Write Once
Reuse Many; FQSN - Fully Qualified Skills Name.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator

from a2a_labs.agent_framework import AgentFramework
from a2a_labs.agent_specs import AgentSpec, SkillSpec
from a2a_labs.enums import AgentRole
from a2a_labs.fqsn import FQSN
from a2a_labs.mcp_tools import McpTool
from a2a_labs.vendors import VendorModel


# --- The four governed specs (identities Enum-sourced; text is content) ------

_POLICY = AgentSpec(
    role=AgentRole.POLICY,
    framework=AgentFramework.RAW_A2A,
    model=VendorModel.GEMINI_FLASH_LITE,
    description="Provides information about insurance policy coverage options.",
    skill=SkillSpec(
        identity=FQSN.parse("policy.insurance_coverage"),
        name="Insurance coverage",
        description="Insurance coverage options and details.",
        examples=("What does my policy cover?", "Are mental health services included?"),
    ),
)

_RESEARCH = AgentSpec(
    role=AgentRole.RESEARCH,
    framework=AgentFramework.ADK,
    model=VendorModel.GEMINI_PRO,
    description="Healthcare research on symptoms, conditions, treatments via web.",
    skill=SkillSpec(
        identity=FQSN.parse("research.health_research"),
        name="Health research",
        description="Web-sourced information on conditions and treatments.",
        examples=("What are treatments for migraine?", "Symptoms of vitamin D deficiency?"),
    ),
)

_PROVIDER = AgentSpec(
    role=AgentRole.PROVIDER,
    framework=AgentFramework.LANGGRAPH_MCP,
    model=VendorModel.GEMINI_FLASH_LITE,
    description="Find healthcare providers by location and specialty.",
    skill=SkillSpec(
        identity=FQSN.parse("provider.find_providers"),
        name="Find healthcare providers",
        description="Finds providers based on location/specialty.",
        examples=("Psychiatrists near Boston, MA?", "Find a pediatrician in Springfield, IL."),
        mcp_tool=McpTool.LIST_DOCTORS,  # Enum, not a repeated literal
    ),
)

_HEALTHCARE = AgentSpec(
    role=AgentRole.HEALTHCARE,
    framework=AgentFramework.BEEAI,
    model=VendorModel.GEMINI_FLASH_2_5,
    description="A personal concierge for healthcare information, customized to your policy.",
    skill=SkillSpec(
        identity=FQSN.parse("healthcare.concierge"),
        name="Healthcare concierge",
        description="Orchestrates policy, research, and provider agents.",
        examples=("I'm in Boston with anxiety — what's covered and who can I see?",),
    ),
    handoffs=(AgentRole.POLICY, AgentRole.RESEARCH, AgentRole.PROVIDER),
)


# Default bound on cyclic (Directed Cyclic Graph, DCG) call depth. A cycle is
# permitted but must terminate; this caps how many hops a cyclic conversation
# may traverse before it is cut off. Parameterized, never hardcoded at a call
# site — override per-registry via SystemRegistry(..., max_call_depth=N).
DEFAULT_MAX_CALL_DEPTH = 4


class Topology(StrEnum):
    """How the agent call graph is shaped, by the handoff edges."""

    DAG = "dag"  # Directed Acyclic Graph — no agent reaches itself via handoffs
    DCG = "dcg"  # Directed Cyclic Graph — at least one cycle exists


class CallPath(BaseModel):
    """A typed, validated sequence of agent hops through the call graph.

    The roles tuple is Enum-governed AND Pydantic-enforced: passing anything
    that is not an AgentRole is rejected at construction, so a path can never
    silently carry a raw string. ``hops`` are edges, so an N-role path is N-1
    hops. Used by the registry to reason about cyclic call depth.
    """

    model_config = ConfigDict(frozen=True)

    roles: tuple[AgentRole, ...]

    @model_validator(mode="after")
    def _non_empty(self) -> "CallPath":
        if not self.roles:
            raise ValueError("a CallPath needs at least one role")
        return self

    @property
    def hops(self) -> int:
        """Edge count: an N-role path is N-1 hops."""
        return len(self.roles) - 1


class SystemRegistry:
    """The agents as one immutable, validated registry (WORM).

    Supports both a Directed Acyclic Graph (DAG) and a Directed Cyclic Graph
    (DCG) call topology over the Agent-to-Agent (A2A) protocol. Closure is
    always enforced; acyclicity is opt-in. Cyclic conversations are bounded by
    ``max_call_depth`` (default ``DEFAULT_MAX_CALL_DEPTH``) so a cycle must
    terminate rather than loop without end.
    """

    def __init__(
        self,
        specs: tuple[AgentSpec, ...],
        *,
        acyclic: bool = False,
        max_call_depth: int = DEFAULT_MAX_CALL_DEPTH,
    ) -> None:
        by_role = {s.role: s for s in specs}
        if len(by_role) != len(specs):
            raise ValueError("duplicate role in system registry")
        # Graph closure: every handoff target must be a registered role.
        for spec in specs:
            for target in spec.handoffs:
                if target not in by_role:
                    raise ValueError(
                        f"{spec.role.value} hands off to unregistered "
                        f"{target.value}"
                    )
        if max_call_depth < 1:
            raise ValueError("max_call_depth must be >= 1")
        self._by_role = by_role
        self._specs = specs
        self._max_call_depth = max_call_depth
        # Acyclic enforcement is opt-in; DCG is supported by default.
        if acyclic and self.topology() is Topology.DCG:
            raise ValueError(
                f"registry declared acyclic but a cycle exists: "
                f"{self.find_cycle()}"
            )

    # --- navigation -----------------------------------------------------
    def __iter__(self):
        return iter(self._specs)

    def spec(self, role: AgentRole) -> AgentSpec:
        """The spec for a role — navigated, raises if absent."""
        return self._by_role[role]

    @property
    def roles(self) -> tuple[AgentRole, ...]:
        return tuple(self._by_role)

    @property
    def max_call_depth(self) -> int:
        """The configured bound on cyclic call depth (parameterized)."""
        return self._max_call_depth

    def orchestrator(self) -> AgentSpec:
        """The single front-door agent, when the system is tree-shaped.

        Convenience accessor for a single-orchestrator DAG; raises if the
        system has zero or many agents with handoffs. Not a structural
        constraint — DCG systems may have several entry points.
        """
        orchestrators = [s for s in self._specs if s.handoffs]
        if len(orchestrators) != 1:
            raise ValueError("system must have exactly one orchestrator")
        return orchestrators[0]

    # --- topology -------------------------------------------------------
    def find_cycle(self) -> tuple[AgentRole, ...] | None:
        """Return one cycle as a role path, or None if the graph is acyclic.

        Depth-first search with a recursion stack — real detection, not a
        guess. The first back-edge found yields the cycle path.
        """
        WHITE, GREY, BLACK = 0, 1, 2
        color = {r: WHITE for r in self._by_role}
        stack: list[AgentRole] = []

        def visit(role: AgentRole) -> tuple[AgentRole, ...] | None:
            color[role] = GREY
            stack.append(role)
            for nxt in self._by_role[role].handoffs:
                if color[nxt] == GREY:  # back-edge -> cycle
                    i = stack.index(nxt)
                    return tuple(stack[i:]) + (nxt,)
                if color[nxt] == WHITE:
                    found = visit(nxt)
                    if found:
                        return found
            stack.pop()
            color[role] = BLACK
            return None

        for r in self._by_role:
            if color[r] == WHITE:
                found = visit(r)
                if found:
                    return found
        return None

    def topology(self) -> Topology:
        """Classify the call graph as DAG or DCG by real cycle detection."""
        return Topology.DCG if self.find_cycle() else Topology.DAG

    def within_depth(self, path: "CallPath") -> bool:
        """True if a typed CallPath respects the configured max_call_depth.

        The path is a validated CallPath (Enum-enforced), not a bare tuple, so
        a non-AgentRole element cannot reach this check. A cyclic system uses
        this at runtime to cut a conversation that exceeds the bound.
        """
        return path.hops <= self._max_call_depth


# Built once at import — the WORM system registry. The default healthcare
# system is a DAG; acyclic enforcement is left off so a DCG variant is a
# one-flag change. The cyclic call-depth bound is parameterized.
SYSTEM = SystemRegistry((_POLICY, _RESEARCH, _PROVIDER, _HEALTHCARE))
