"""Governed Agent-to-Agent (A2A) executors.

The upstream executor returns a bare text message: the reply carries no identity,
no correlation to its request, and no source. ``GovernedExecutor`` wraps any
agent's ``answer_query``-style call so the A2A server emits a governed
``WorkspaceResponseObject`` — a response that inherits the request's identity and
is BLAKE3-correlated back to it — serialized into the A2A message via the bridge.

No hardcoded identity: the request surrogate and fully qualified name are owned
by ``AgentRole`` (``role.request_surrogate`` / ``role.request_fqdn``), and
``handle`` derives them from ``self.role``. There is no parameter for a caller to
hand-type a literal into, so a value like ``"req-policy"`` can only come from the
Enum, never from a string at a call site.

Acronyms: A2A - Agent-to-Agent; SDK - Software Development Kit;
FQSN - Fully Qualified Skill Name.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from a2a_labs.a2a_bridge import SKILL_REGISTRY, response_to_artifact_text
from a2a_labs.enums import AgentRole
from a2a_labs.fqsn import FQSN
from a2a_labs.workspace import ResponseStatus, WorkspaceState

if TYPE_CHECKING:  # pragma: no cover - typing only
    from a2a_labs.workspace import WorkspaceResponseObject

# An agent is any callable that turns a prompt string into an answer string.
AgentCallable = Callable[[str], str]

try:  # the a2a-sdk is only installed with the [server] extra
    from a2a.server.agent_execution import AgentExecutor as _ExecutorBase
except ImportError:  # core install: no SDK, executor stays importable
    _ExecutorBase = object


class GovernedExecutor(_ExecutorBase):
    """Bridge an A2A request to an agent, emitting a governed response.

    Construct with the role (an ``AgentRole`` Enum member) and the agent's answer
    callable. The role supplies the request identity and the governed skill id;
    nothing is hand-typed.
    """

    def __init__(self, role: AgentRole, agent_call: AgentCallable) -> None:
        if not isinstance(role, AgentRole):
            raise TypeError("role must be an AgentRole member, not a string")
        self.role = role
        self._agent_call = agent_call
        skills = SKILL_REGISTRY[role]
        # The governed skill identity (FQSN) this role answers.
        self.skill_id = skills[0].fqsn if skills else FQSN.parse(f"{role.value}.default")

    def _new_request(self, prompt: str) -> WorkspaceState:
        """Build the request envelope, with identity DERIVED from the role."""
        return WorkspaceState(
            bgd_surrogate=self.role.request_surrogate,  # from the Enum, not a literal
            fqdn=self.role.request_fqdn,                # from the Enum, not a literal
            task_content=prompt,
            skill_id=self.skill_id.name,                # FQSN -> dotted string for the wire layer
        )

    # ----- transport-agnostic core (testable without the SDK or a network) -----
    def handle(self, prompt: str) -> "WorkspaceResponseObject":
        """Turn a prompt into a governed, correlated response.

        Needs no A2A SDK and no hand-typed identity: the request envelope is
        derived from ``self.role``, the agent is called, and ``respond`` returns
        a response that inherits identity and is BLAKE3-correlated.
        """
        request = self._new_request(prompt)
        try:
            answer = self._agent_call(prompt)
        except Exception as exc:  # noqa: BLE001 - surfaced as a governed error response
            return request.respond(
                result=f"{type(exc).__name__}: {exc}",
                status=ResponseStatus.ERROR,
                source_agent=self.role.value,
            )
        return request.respond(
            result=answer,
            status=ResponseStatus.OK,
            source_agent=self.role.value,
        )

    def expected_request(self, prompt: str) -> WorkspaceState:
        """The request a client/test can reconstruct to verify correlation.

        Same derivation as ``handle`` uses internally, exposed so a caller can
        check ``response.correlation_id == expected_request(p).blake3_pair_hash``
        without hand-typing identity values.
        """
        return self._new_request(prompt)

    # ----- A2A SDK adapter (only used when serving live) -----
    async def execute(self, context, event_queue) -> None:  # pragma: no cover - needs SDK
        """A2A AgentExecutor entry point: adapt context -> handle() -> message."""
        from a2a.utils import new_agent_text_message

        prompt = context.get_user_input()
        response = self.handle(prompt)
        await event_queue.enqueue_event(
            new_agent_text_message(response_to_artifact_text(response))
        )

    async def cancel(self, context, event_queue) -> None:  # pragma: no cover - needs SDK
        """A2A requires a cancel hook; this agent has no cancellable work."""
        return None


def make_policy_executor(agent_call: AgentCallable) -> GovernedExecutor:
    """The Lab 2 Policy executor — governed by AgentRole.POLICY."""
    return GovernedExecutor(AgentRole.POLICY, agent_call)
