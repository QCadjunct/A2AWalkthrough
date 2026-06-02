"""Three tiers of launching the four Agent-to-Agent (A2A) servers.

Every agent in this project is an Asynchronous Server Gateway Interface (ASGI)
application run by uvicorn on its own port. A Marimo notebook is a reactive
Python program, NOT an ASGI host — so the agents must run as separate
processes, and the notebooks act as clients/test harnesses that reach them over
Hypertext Transfer Protocol (HTTP).

This module offers three ways to start those processes, simplest to most
complex. Pick the tier that matches how much control you need.

Tier 1 - terminal commands  : you run four shells yourself. Zero magic.
Tier 2 - subprocess manager : one Python object spawns/kills each server.
Tier 3 - asyncio supervisor : concurrent startup + streamed log multiplexing.

Acronyms: A2A - Agent-to-Agent; ASGI - Asynchronous Server Gateway Interface;
HTTP - Hypertext Transfer Protocol; URL - Uniform Resource Locator;
PID - Process Identifier.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import time
from dataclasses import dataclass, field

import httpx

from a2a_labs.config import get_settings
from a2a_labs.enums import AgentRole

# Which script implements each agent server. These are the upstream files.
AGENT_SCRIPTS: dict[AgentRole, str] = {
    AgentRole.POLICY: "a2a_policy_agent.py",
    AgentRole.RESEARCH: "a2a_research_agent.py",
    AgentRole.PROVIDER: "a2a_provider_agent.py",
    AgentRole.HEALTHCARE: "a2a_healthcare_agent.py",
}


# ---------------------------------------------------------------------------
# Shared helper: health-check an agent by fetching its Agent Card.
# ---------------------------------------------------------------------------
def is_up(url: str, timeout: float = 2.0) -> bool:
    """Return True if the agent at ``url`` serves its Agent Card."""
    card_url = url.rstrip("/") + "/.well-known/agent-card.json"
    try:
        return httpx.get(card_url, timeout=timeout).status_code == 200
    except Exception:  # noqa: BLE001 - any failure means "not up yet"
        return False


def wait_until_up(url: str, attempts: int = 30, delay: float = 1.0) -> bool:
    """Poll ``url`` until its Agent Card responds or attempts run out."""
    for _ in range(attempts):
        if is_up(url):
            return True
        time.sleep(delay)
    return False


# ===========================================================================
# TIER 1 — Terminal commands (no process management at all)
# ===========================================================================
def tier1_terminal_commands() -> str:
    """Return the four shell commands to paste into four terminals.

    Simplest possible approach. Each agent runs in its own shell, so logs are
    naturally separated and Ctrl-C stops exactly one server. The cost: it is
    fully manual — you open and babysit four terminals yourself, and a notebook
    cannot start or stop anything.

    Best for: first run-through, debugging one agent in isolation, or any time
    you want to *see* each server's raw output without multiplexing.
    """
    lines = ["# Open one terminal per agent, in project root:"]
    for role in (
        AgentRole.POLICY,
        AgentRole.RESEARCH,
        AgentRole.PROVIDER,
        AgentRole.HEALTHCARE,
    ):
        lines.append(f"uv run {AGENT_SCRIPTS[role]}   # {role.value} agent")
    return "\n".join(lines)


# ===========================================================================
# TIER 2 — Subprocess manager (one object spawns/kills each server)
# ===========================================================================
@dataclass
class AgentProcessManager:
    """Spawn each agent as a child process and manage them as a group.

    A middle ground: a notebook cell creates one manager, calls ``start_all()``,
    runs its tests, then ``stop_all()``. Each agent is an independent OS process
    (clean isolation — one crashing does not take down the others, and you can
    restart a single one). The cost over Tier 1: logs are written to files
    rather than streamed live, so you tail a file to watch a server.

    Best for: incremental notebook testing where you want one button to bring
    the whole system up and another to tear it down.
    """

    log_dir: str = "logs"
    _procs: dict[AgentRole, subprocess.Popen] = field(default_factory=dict)

    def start(self, role: AgentRole) -> None:
        """Start a single agent if it is not already running."""
        import os

        os.makedirs(self.log_dir, exist_ok=True)
        if role in self._procs and self._procs[role].poll() is None:
            print(f"{role.value}: already running (PID {self._procs[role].pid})")
            return
        log_path = f"{self.log_dir}/{role.value}.log"
        log_file = open(log_path, "w")  # noqa: SIM115 - lifetime tied to process
        proc = subprocess.Popen(
            ["uv", "run", AGENT_SCRIPTS[role]],
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        self._procs[role] = proc
        print(f"{role.value}: started (PID {proc.pid}) -> {log_path}")

    def start_all(self, wait: bool = True) -> None:
        """Start every agent, optionally blocking until each is reachable."""
        settings = get_settings()
        for role in AGENT_SCRIPTS:
            self.start(role)
        if wait:
            for role in AGENT_SCRIPTS:
                url = settings.url_for(role)
                status = "up" if wait_until_up(url) else "DID NOT START"
                print(f"{role.value}: {status} ({url})")

    def stop(self, role: AgentRole) -> None:
        """Terminate a single agent."""
        proc = self._procs.get(role)
        if proc and proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)
            print(f"{role.value}: stopped")

    def stop_all(self) -> None:
        """Terminate every managed agent."""
        for role in list(self._procs):
            self.stop(role)

    def status(self) -> dict[str, str]:
        """Return a role -> 'running'/'stopped' map."""
        return {
            role.value: ("running" if p.poll() is None else "stopped")
            for role, p in self._procs.items()
        }


# ===========================================================================
# TIER 3 — Asyncio supervisor (concurrent startup, multiplexed logs)
# ===========================================================================
class AsyncAgentSupervisor:
    """Start all agents concurrently and stream their logs into one feed.

    The most capable tier. Uses ``asyncio.create_subprocess_exec`` so the four
    servers boot in parallel rather than one after another, and each line of
    every server's output is tagged with the agent name and printed to a single
    multiplexed stream. The cost: it is the most code and requires a running
    event loop (fine in Marimo / Jupyter via nest_asyncio).

    Best for: the full demo or class presentation where fast, parallel startup
    and a single readable log feed matter.
    """

    def __init__(self) -> None:
        self._procs: dict[AgentRole, asyncio.subprocess.Process] = {}
        self._tasks: list[asyncio.Task] = []

    async def _pump(self, role: AgentRole, proc: asyncio.subprocess.Process) -> None:
        """Tag and print each line from one agent's combined output."""
        assert proc.stdout is not None
        async for raw in proc.stdout:
            print(f"[{role.value:10}] {raw.decode().rstrip()}")

    async def start_all(self) -> None:
        """Spawn every agent concurrently and begin pumping their logs."""
        for role, script in AGENT_SCRIPTS.items():
            proc = await asyncio.create_subprocess_exec(
                "uv",
                "run",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            self._procs[role] = proc
            self._tasks.append(asyncio.create_task(self._pump(role, proc)))
            print(f"{role.value}: spawned (PID {proc.pid})")

    async def wait_ready(self) -> dict[str, bool]:
        """Concurrently wait for every Agent Card to come up."""
        settings = get_settings()

        async def probe(role: AgentRole) -> tuple[str, bool]:
            url = settings.url_for(role)
            card = url.rstrip("/") + "/.well-known/agent-card.json"
            async with httpx.AsyncClient() as client:
                for _ in range(30):
                    try:
                        r = await client.get(card, timeout=2.0)
                        if r.status_code == 200:
                            return role.value, True
                    except Exception:  # noqa: BLE001
                        pass
                    await asyncio.sleep(1.0)
            return role.value, False

        results = await asyncio.gather(*(probe(r) for r in AGENT_SCRIPTS))
        return dict(results)

    async def stop_all(self) -> None:
        """Terminate every agent and cancel the log pumps."""
        for role, proc in self._procs.items():
            if proc.returncode is None:
                proc.terminate()
                await proc.wait()
                print(f"{role.value}: stopped")
        for task in self._tasks:
            task.cancel()


# ---------------------------------------------------------------------------
# Tradeoff summary, printable from a notebook cell.
# ---------------------------------------------------------------------------
TIER_COMPARISON = """\
Tier 1  Terminal commands   | manual    | live separate logs | no notebook control
Tier 2  Subprocess manager  | one call  | logs to files      | per-agent restart, OS isolation
Tier 3  Asyncio supervisor  | parallel  | one tagged feed    | most code, needs event loop
"""


if __name__ == "__main__":
    if "--commands" in sys.argv:
        print(tier1_terminal_commands())
    else:
        print(TIER_COMPARISON)
