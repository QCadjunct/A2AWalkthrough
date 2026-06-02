"""Lab 2 — the governed Policy agent, served live over A2A on port 9999.

Run:  uv run python -m a2a_labs.servers.policy_server
Needs: uv sync --extra server, and GEMINI_API_KEY.
"""

from __future__ import annotations

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from a2a_labs.a2a_bridge import build_agent_card
from a2a_labs.config import setup_env
from a2a_labs.enums import AgentRole
from a2a_labs.executor import make_policy_executor
from a2a_labs.policy_agent import PolicyAgent


def build_app() -> A2AStarletteApplication:
    """Assemble the governed Policy A2A application (card + handler)."""
    settings = setup_env()
    agent = PolicyAgent()
    executor = make_policy_executor(agent.answer_query)
    card = build_agent_card(AgentRole.POLICY, settings)
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    return A2AStarletteApplication(agent_card=card, http_handler=handler)


def main() -> None:
    """Serve the governed Policy agent on AgentRole.POLICY.port."""
    settings = setup_env()
    role = AgentRole.POLICY
    app = build_app()
    print(
        f"Policy A2A server (governed) on "
        f"http://{settings.agent_host}:{int(role.port)}/"
    )
    uvicorn.run(app.build(), host=settings.agent_host, port=int(role.port))


if __name__ == "__main__":
    main()
