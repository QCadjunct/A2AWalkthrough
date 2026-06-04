"""Agent frameworks for the Agent-to-Agent (A2A) Walkthrough.

Standing rule (mirrors enums.py): free-form strings are replaced by Enums
wherever a value is drawn from a fixed, known set. The upstream system is
segmented by framework — each agent is written against a different stack — and
that choice lived implicitly in each script's imports. Here it is a closed
Enum, so the unified application can reason about "which framework serves this
role" without parsing import lines.

KISS here means "Keep It Simple and Standard": standard-library ``enum.StrEnum``
with the standard constraint decorator ``@unique``, and — to keep
responsibilities where they belong (Single Responsibility Principle, SRP) — the
Enum owns the facts derived from it via ``@property``, instead of letting
callers rebuild a mapping. A framework knows its own display label and its
signature construct. Callers ask the Enum.

Every acronym is spelled out on first use:
* A2A   - Agent-to-Agent (protocol)
* ADK   - Agent Development Kit (Google)
* MCP   - Model Context Protocol
* SDK   - Software Development Kit
* SRP   - Single Responsibility Principle
"""

from __future__ import annotations

from enum import StrEnum, unique


@unique
class AgentFramework(StrEnum):
    """Which stack implements an agent server. One member per framework.

    Each member owns the facts derived from it: its human display label and the
    signature construct that identifies the stack in code. This keeps that
    knowledge here (SRP), out of the console and the registry.
    """

    RAW_A2A = "raw_a2a"          # a2a-sdk: hand-rolled AgentExecutor + Starlette
    ADK = "adk"                  # Google ADK: LlmAgent + to_a2a()
    LANGGRAPH_MCP = "langgraph"  # LangGraph create_agent + MCP tools
    MICROSOFT = "microsoft"      # agent_framework.a2a.A2AAgent (client / interop)
    BEEAI = "beeai"              # BeeAI RequirementAgent orchestrator

    @property
    def label(self) -> str:
        """Human display name — owned by the member, not hand-typed by callers."""
        return {
            AgentFramework.RAW_A2A: "Raw A2A SDK",
            AgentFramework.ADK: "Google ADK",
            AgentFramework.LANGGRAPH_MCP: "LangGraph + MCP",
            AgentFramework.MICROSOFT: "Microsoft Agent Framework",
            AgentFramework.BEEAI: "BeeAI",
        }[self]

    @property
    def signature_construct(self) -> str:
        """The construct that identifies this stack in source — owned here.

        Lets a reader or a teaching deck name the give-away API for each
        framework without re-typing it at the call site.
        """
        return {
            AgentFramework.RAW_A2A: "AgentExecutor + A2AStarletteApplication",
            AgentFramework.ADK: "LlmAgent + to_a2a()",
            AgentFramework.LANGGRAPH_MCP: "create_agent + MultiServerMCPClient",
            AgentFramework.MICROSOFT: "agent_framework.a2a.A2AAgent",
            AgentFramework.BEEAI: "RequirementAgent + HandoffTool",
        }[self]


# Derived from AgentFramework itself — no separately maintained dict to drift.
FRAMEWORK_LABELS: dict[AgentFramework, str] = {f: f.label for f in AgentFramework}
