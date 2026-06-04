# 🚀 A2A Unified System — Setup & Test Guide

How to run and test the governed A2A application on FreedomTower.

---

## 📋 Prerequisites

- Python ≥ 3.12, `uv` installed
- You are in the project root: `02-marimo-transformation/`
- `.env` present (ports + `GEMINI_API_KEY`) — already configured

---

## 1️⃣  Install dependencies

```bash
cd /mnt/e/WSLData/Projects/A2AWalkthrough/02-marimo-transformation

# foundation + marimo UI (enough to run the console)
uv sync --extra marimo

# add the agent-server stack only when you want live agents
uv sync --extra marimo --extra server
```

---

## 2️⃣  Smoke-test the foundation (no servers needed)

Confirms the governed layer imports and the registry assembles:

```bash
uv run python -c "
from a2a_labs.system_registry import SYSTEM, CallPath, Topology
from a2a_labs.mcp_tools import McpTool, SERVER_TOOLS
from a2a_labs.agent_framework import AgentFramework
print('topology:', SYSTEM.topology().value, '| max_call_depth:', SYSTEM.max_call_depth)
for s in SYSTEM:
    print(f'  {s.role.value:11} :{s.port}  {s.framework.label:26} {s.skill.id}')
print('MCP:', McpTool.LIST_DOCTORS.value, '->', McpTool.LIST_DOCTORS.server.stdio_command())
"
```

Expected: four agents listed, `topology: dag`, `max_call_depth: 4`.

---

## 3️⃣  TIER A — Run the console UI (recommended first test)

Serve the system console as a web app. Agents will read **down** until you
start them (Tier B) — that is correct.

```bash
cd marimo
uv run uvicorn console_asgi:app --port 5650
# open http://localhost:5650/
```

You should see: the **registry table** (4 agents, ports, frameworks, skills),
the **call-graph** (Healthcare → Policy/Research/Provider), **status cards**
(red = not running), the **MCP-tools table**, and **Start/Stop** buttons.

Edit-mode alternative (shows the code cells too):

```bash
cd marimo
uv run marimo edit system_console.py
```

---

## 4️⃣  TIER B — Bring the four agents up (live system)

The four agent servers live in `../01-a2a-original/` and use the upstream
helpers. Run them the upstream (Tier 1) way, each in its own terminal, from
that directory:

```bash
cd /mnt/e/WSLData/Projects/A2AWalkthrough/01-a2a-original
uv run a2a_policy_agent.py       # terminal 1  -> :9999
uv run a2a_research_agent.py     # terminal 2  -> :9998
uv run a2a_provider_agent.py     # terminal 3  -> :9997
uv run a2a_healthcare_agent.py   # terminal 4  -> :9996
```

Now refresh the console (Tier A): the **status cards turn green** as each
agent's Agent Card answers on its port. This exercises the real `is_up`
health-check end to end.

> **Live model calls** require a Gemini API key the SDK accepts. The current
> `.env` key is the `AQ.`-prefixed type your account issues; if model calls
> fail, that is the known account-credential limitation, *not* a console bug —
> the console, monitoring, and health-checks all work regardless.

---

## 5️⃣  Verify the registry features (DAG / DCG / CallPath)

```bash
uv run python -c "
from a2a_labs.system_registry import SystemRegistry, SYSTEM, CallPath
from a2a_labs.enums import AgentRole
# current system is a DAG
print('topology:', SYSTEM.topology().value)
print('cycle:', SYSTEM.find_cycle())
# typed, enforced call path
cp = CallPath(roles=(AgentRole.HEALTHCARE, AgentRole.POLICY))
print('hops:', cp.hops, 'within_depth:', SYSTEM.within_depth(cp))
"
```

---

## 🧭 What each entry point is

| File | Purpose | Command |
|---|---|---|
| `console_asgi.py` | serve the console (run mode) | `uv run uvicorn console_asgi:app --port 5650` |
| `system_console.py` | full console notebook | `uv run marimo edit system_console.py` |
| `console_monitor.py` | focused monitor notebook | `uv run marimo edit console_monitor.py` |

---

## ✅ Test checklist

- [ ] `uv sync --extra marimo` succeeds
- [ ] Foundation smoke-test prints 4 agents + `topology: dag`
- [ ] Console serves at `http://localhost:5650/`
- [ ] Registry table + call graph + MCP table render
- [ ] Status cards show (red before agents, green after)
- [ ] Tier B: agents start and cards turn green on refresh
- [ ] DAG/DCG/CallPath verification runs clean
