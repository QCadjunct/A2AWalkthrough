# A2A Walkthrough — Standards Additions

This is a standards-compliant overlay on the upstream
[QCadjunct/A2AWalkthrough](https://github.com/QCadjunct/A2AWalkthrough) course
repository (itself a fork of `holtskinner/A2AWalkthrough`, basis for the
DeepLearning.AI Agent-to-Agent (A2A) course). The upstream lesson files are left
untouched; everything here is additive.

## What's here

```
src/a2a_labs/          Typed standards layer (Enums, Pydantic V2 Settings, decorators, launcher)
  ├── enums.py         Provider, Model, AgentRole, AgentPort, TransportMode
  ├── config.py        Settings + Gemini/Vertex AI toggle; setup_env() drop-in
  ├── decorators.py    @lab_step, @async_lab_step, @requires(...)
  └── orchestrator.py  Three launcher tiers + health checks
marimo/                All 8 labs as Marimo notebooks + lab0_launcher
tools/convert_to_marimo.py   The Jupyter->Marimo converter
slides/                8 PowerPoint decks (one per lab) + build scripts
docs/                  STANDARDS_AND_MARIMO.md, ARCHITECTURE.md
```

## Quick start

```bash
uv sync                                  # install from upstream pyproject.toml
cp example.env .env                      # add GEMINI_API_KEY (or Vertex settings)

# Bring up the agents (pick a tier — see docs/STANDARDS_AND_MARIMO.md)
uv run a2a_policy_agent.py               # Tier 1: one terminal each
# or open the launcher notebook:
uv run marimo edit marimo/lab0_launcher.py

# Work through a lab
uv run marimo edit marimo/lab1_basic_qa.py
```

## The one idea to take away

Each agent is an Asynchronous Server Gateway Interface (ASGI) server run by
uvicorn on its own port. Marimo notebooks are **clients** that reach those
servers over Hypertext Transfer Protocol (HTTP) — they do not host them. The
launcher starts the agent processes; the notebooks test against them
incrementally, with `@requires(...)` reporting any missing prerequisite by name.

See `docs/ARCHITECTURE.md` for the system diagram and `docs/STANDARDS_AND_MARIMO.md`
for the full walkthrough.

## Switching Gemini ↔ Vertex AI

One environment variable flips the entire stack:

```bash
# .env
PROVIDER=gemini        # gemini/<model>
# PROVIDER=vertex_ai   # vertex_ai/<model>  (also set GOOGLE_CLOUD_PROJECT etc.)
```
