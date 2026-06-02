# A2A Walkthrough — Standards Layer, Marimo Notebooks & Parallel Launcher

This document covers the additions layered on top of the upstream
[A2AWalkthrough](https://github.com/QCadjunct/A2AWalkthrough) course repository:
a typed standards package, Marimo conversions of all eight lab notebooks, a
three-tier parallel agent launcher, and eight presentation decks.

Every acronym is spelled out on first use. Key ones: Agent-to-Agent (A2A);
Asynchronous Server Gateway Interface (ASGI); Model Context Protocol (MCP);
Agent Development Kit (ADK); Large Language Model (LLM); Hypertext Transfer
Protocol (HTTP); Uniform Resource Locator (URL).

## What was added, and why

The upstream repo is excellent teaching code, but it uses patterns that are
fine for a lesson and risky for production: hardcoded model strings, ports as
scattered magic numbers, and a bare `load_dotenv` for configuration. The
additions here keep the upstream files untouched and add a parallel,
standards-compliant path beside them.

| Concern | Upstream baseline | Standards layer |
|---------|-------------------|-----------------|
| Model names | `"gemini/gemini-3.1-flash-lite-preview"` string | `Model` Enum |
| Provider | Gemini, with Vertex AI commented out | `Provider` Enum + one-env-var toggle |
| Ports | `int(os.getenv("POLICY_AGENT_PORT"))` | `AgentPort` IntEnum, `settings.port_for(role)` |
| Config | `helpers.setup_env()` (bare `load_dotenv`) | Pydantic Version 2 `Settings` |
| Prereq checks | none — fails mid-call | `@requires(...)` probes the Agent Card first |
| Notebooks | Jupyter `.ipynb` | Marimo `.py` (reactive, diff-able, lint-able) |

## The standards package (`src/a2a_labs/`)

`enums.py` defines `Provider`, `Model`, `AgentRole`, `AgentPort`,
`TransportMode`, replacing free-form strings with fixed, autocomplete-friendly
sets. `config.py` provides the Pydantic Version 2 `Settings` object whose single
`provider` field flips the whole stack between Gemini and Vertex AI; its
`litellm_model(model)` helper prepends the correct provider prefix.
`decorators.py` adds `@lab_step`, `@async_lab_step`, and `@requires(...)` for
self-documenting, prerequisite-checked lab steps. `orchestrator.py` holds the
three launcher tiers (below).

The one-line drop-in replacement for the upstream helper is:

```python
# upstream:            from helpers import setup_env
from a2a_labs import setup_env   # returns a validated Settings object
settings = setup_env()
model = settings.litellm_model(Model.FLASH_LITE)
```

## ASGI vs. Marimo — the architectural rule

Each agent is an ASGI application run by uvicorn on its own port. A Marimo
notebook is a reactive Python program, **not** an ASGI host. A blocking
`uvicorn.run()` would freeze a notebook's event loop, and four of them cannot
share one process across four ports.

Therefore: **agents run as separate processes; notebooks are clients.** The
launcher starts the agent processes; the lab notebooks reach them over HTTP via
the A2A client, exactly as upstream Lab 3 does. The `@requires(...)` decorator
turns a missing prerequisite server into a clear message instead of a buried
connection error.

## Three ways to launch the four agents

All four servers must be up before the orchestrator (Lab 8) can run. The
`marimo/lab0_launcher.py` notebook offers three tiers, simplest to most complex.

### Tier 1 — Terminal commands (no process management)

Paste one line per terminal. Simplest possible; logs stay separated; Ctrl-C
stops exactly one server. Fully manual — a notebook cannot start or stop
anything.

```bash
uv run a2a_policy_agent.py      # policy    :9999
uv run a2a_research_agent.py    # research  :9998
uv run a2a_provider_agent.py    # provider  :9997
uv run a2a_healthcare_agent.py  # healthcare:9996
```

### Tier 2 — Subprocess manager (one object, one button)

`AgentProcessManager` spawns each agent as an independent operating-system
process, so one crashing does not take the others down and you can restart a
single agent. Logs go to files under `logs/`.

```python
from a2a_labs.orchestrator import AgentProcessManager
manager = AgentProcessManager()
manager.start_all(wait=True)   # bring the system up, block until reachable
manager.status()               # {'policy': 'running', ...}
manager.stop_all()             # tear everything down
```

### Tier 3 — Asyncio supervisor (concurrent startup, one log feed)

`AsyncAgentSupervisor` boots all four servers in parallel with
`asyncio.create_subprocess_exec` and multiplexes every server's output into one
feed, each line tagged with the agent name. Most code; needs a running event
loop (Marimo provides one). Best for a full demo.

```python
from a2a_labs.orchestrator import AsyncAgentSupervisor
supervisor = AsyncAgentSupervisor()
await supervisor.start_all()
ready = await supervisor.wait_ready()   # {'policy': True, ...}
# ... run client queries ...
await supervisor.stop_all()
```

### Choosing a tier

| Tier | Startup | Logs | Notebook control | Best for |
|------|---------|------|------------------|----------|
| 1 Terminal | manual, 4 shells | live, separate | none | first run, debugging one agent |
| 2 Subprocess | one `start_all()` | per-agent files | start/stop/restart each | incremental notebook testing |
| 3 Asyncio | concurrent | one tagged feed | full async control | full demo / class presentation |

## The Marimo notebooks (`marimo/`)

| File | Source | Notes |
|------|--------|-------|
| `lab0_launcher.py` | new | the three launcher tiers + a live health-check cell |
| `lab1_basic_qa.py` | hand-authored | reactive dataflow; editable prompt re-runs the query |
| `lab2_a2a_server_policy_agent.py` | converted | source-viewing + run instructions |
| `lab3_a2a_client.py` | hand-authored | `is_up()` pre-flight callout; async client cell |
| `lab4`–`lab8` | converted | faithful conversions, pass `marimo check` |

Labs 1 and 3 are authored by hand because they run real code with variables
shared across cells, which requires explicit Marimo reactive dataflow (values
passed via cell parameters and returns). The rest are display/source-viewing
oriented and were converted by `tools/convert_to_marimo.py`.

Run any notebook:

```bash
uv run marimo edit marimo/lab1_basic_qa.py     # interactive
uv run marimo run  marimo/lab1_basic_qa.py     # app mode (read-only)
PYTHONPATH=src uv run marimo check marimo/*.py # static validation
```

## Presentation decks (`slides/`)

Eight decks, one per lab, each with built-in speaker notes. Each deck teaches
both the upstream baseline (amber cards) and the standards refactor (violet
cards). Regenerate with:

```bash
cd slides && npm install pptxgenjs && node build_all_decks.js
```
