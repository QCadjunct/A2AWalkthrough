import marimo

__generated_with = "0.9.0"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # A2A System Console

        The four agents — **Policy**, **Research**, **Provider**, **Healthcare**
        — were five separate framework scripts glued by environment variables.
        Here they are one governed registry: every port, framework, skill,
        model, and Model Context Protocol (MCP) tool is an Enum or validated
        model reference, navigated from `a2a_labs`. This console shows the
        system, monitors it, and launches it.
        """
    )
    return


@app.cell
def _():
    from a2a_labs import AgentRole, get_settings
    from a2a_labs.orchestrator import (
        AgentProcessManager,
        is_up,
        tier1_terminal_commands,
    )
    from a2a_labs.system_registry import SYSTEM
    from a2a_labs.mcp_tools import McpTool, SERVER_TOOLS

    settings = get_settings()
    return (
        AgentProcessManager,
        AgentRole,
        McpTool,
        SERVER_TOOLS,
        SYSTEM,
        is_up,
        settings,
        tier1_terminal_commands,
    )


@app.cell(hide_code=True)
def _(SYSTEM, mo):
    # The governed registry as a table — every identity Enum-sourced.
    _rows = [
        {
            "Role": s.role.value,
            "Port": s.port,
            "Framework": s.framework.label,
            "Skill (FQSN)": s.skill.id,
            "Model": s.model.bare_name,
            "MCP tool": s.skill.mcp_tool.value if s.skill.mcp_tool else "—",
            "Hands off to": ", ".join(h.value for h in s.handoffs) or "—",
        }
        for s in SYSTEM
    ]
    mo.vstack(
        [
            mo.md("## The system registry"),
            mo.ui.table(_rows, selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(SYSTEM, mo):
    # The A2A call graph, rendered from the orchestrator's handoffs.
    _orch = SYSTEM.orchestrator()
    _edges = "\n".join(
        f'    {_orch.role.value}["{_orch.role.value} ({_orch.framework.label})"]'
        f" --> {h.value}" for h in _orch.handoffs
    )
    mo.vstack(
        [
            mo.md("## The A2A call graph"),
            mo.mermaid(f"graph LR\n{_edges}"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    refresh = mo.ui.refresh(
        label="Re-poll agents",
        options=["off", "2s", "5s", "10s"],
        default_interval="off",
    )
    refresh
    return (refresh,)


@app.cell
def _(SYSTEM, is_up, refresh, settings):
    refresh  # reactive dependency: re-polls on press / interval
    statuses = {}
    for _spec in SYSTEM:
        _url = settings.url_for(_spec.role)
        statuses[_spec.role] = {"url": _url, "port": _spec.port, "up": is_up(_url)}
    statuses
    return (statuses,)


@app.cell(hide_code=True)
def _(SYSTEM, mo, statuses):
    def _card(spec, info):
        up = info["up"]
        dot = "🟢" if up else "🔴"
        return mo.callout(
            mo.md(
                f"### {dot} {spec.role.value.title()}\n\n"
                f"**{'reachable' if up else 'not running'}**\n\n"
                f"{spec.framework.label}  ·  `:{info['port']}`"
            ),
            kind="success" if up else "danger",
        )

    mo.hstack(
        [_card(s, statuses[s.role]) for s in SYSTEM],
        widths="equal",
        gap=1,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    start_all_btn = mo.ui.run_button(label="Start all agents")
    stop_all_btn = mo.ui.run_button(label="Stop all agents")
    mo.hstack([start_all_btn, stop_all_btn], justify="start", gap=1)
    return start_all_btn, stop_all_btn


@app.cell
def _(AgentProcessManager):
    manager = AgentProcessManager()
    return (manager,)


@app.cell
def _(manager, mo, start_all_btn, stop_all_btn):
    _msg = "Idle — press a button to start or stop the system."
    if start_all_btn.value:
        manager.start_all(wait=False)
        _msg = "Issued **start_all** — re-poll above to watch them come up."
    elif stop_all_btn.value:
        manager.stop_all()
        _msg = "Issued **stop_all** — agents terminated."
    mo.md(_msg)
    return


@app.cell(hide_code=True)
def _(McpTool, SERVER_TOOLS, mo):
    # MCP tools as governed Enums — the tool name is no longer a loose literal.
    _rows = [
        {
            "MCP tool": t.value,
            "Server": t.server.value,
            "Transport": t.server.transport.value,
            "Launch": " ".join(t.server.stdio_command()),
        }
        for s, ts in SERVER_TOOLS.items()
        for t in ts
    ]
    mo.vstack([mo.md("## MCP tools (Enum-governed)"), mo.ui.table(_rows, selection=None)])
    return


@app.cell(hide_code=True)
def _(mo, tier1_terminal_commands):
    mo.md(
        f"""
        ## Tier 1 fallback — run each agent yourself

        ```bash
        {tier1_terminal_commands()}
        ```
        """
    )
    return


if __name__ == "__main__":
    app.run()
