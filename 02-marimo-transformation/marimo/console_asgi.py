"""Asynchronous Server Gateway Interface (ASGI) entry for the system console.

Serves the unified A2A system console as a uvicorn-run Marimo app (run mode,
not the editor). The four agents remain separate uvicorn processes; this is the
console that shows the registry, monitors reachability, and launches them.

Run:
    uv run uvicorn console_asgi:app --port 5650   # from the marimo/ directory
Then open http://localhost:5650/

Acronyms: ASGI - Asynchronous Server Gateway Interface; A2A - Agent-to-Agent.
"""

from __future__ import annotations

from pathlib import Path

import marimo

_HERE = Path(__file__).parent

server = (
    marimo.create_asgi_app()
    .with_app(path="", root=str(_HERE / "system_console.py"))
)

app = server.build()
