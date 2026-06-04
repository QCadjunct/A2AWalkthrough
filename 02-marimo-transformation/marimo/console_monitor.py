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
        # A2A Operator Console — Server Monitor

        The four agents are **Asynchronous Server Gateway Interface (ASGI)**
        applications, each run by uvicorn on its own port. A Marimo notebook is
        a reactive program, **not** an ASGI host — so this console is a
        **client**: it probes each agent's Agent Card, shows status, and drives
        the Tier 2 subprocess manager from `a2a_labs.orchestrator`.

        This page reuses the foundation only — no agent code is duplicated here.
        """
    )
    return


@app.cell
def _():
    from a2a_labs import AgentRole, get_settings
    from a2a_labs.orchestrator import (
        AGENT_SCRIPTS,
        AgentProcessManager,
        TIER_COMPARISON,
        is_up,
        tier1_terminal_commands,
    )

    settings = get_settings()
    return (
        AGENT_SCRIPTS,
        AgentProcessManager,
        AgentRole,
        TIER_COMPARISON,
        is_up,
        settings,
        tier1_terminal_commands,
    )


@app.cell(hide_code=True)
def _(mo):
    # A manual refresh button — reactive: pressing it re-runs every cell that
    # references `refresh`, which is how the monitor re-polls on demand.
    refresh = mo.ui.refresh(
        label="Re-poll agents",
        options=["off", "2s", "5s", "10s"],
        default_interval="off",
    )
    refresh
    return (refresh,)


@app.cell
def _(AgentRole, is_up, settings, refresh):
    # Depend on `refresh` so this re-polls when the button fires or the chosen
    # interval elapses. One probe per role via the real orchestrator.is_up,
    # which checks /.well-known/agent-card.json.
    refresh  # reactive dependency
    statuses = {}
    for _role in AgentRole:
        _url = settings.url_for(_role)
        statuses[_role] = {
            "url": _url,
            "port": int(_role.port),
            "up": is_up(_url),
        }
    statuses
    return (statuses,)


@app.cell(hide_code=True)
def _(mo, statuses):
    # Status cards — one per agent role, green if its Agent Card answers.
    def _card(role, info):
        up = info["up"]
        dot = "🟢" if up else "🔴"
        state = "reachable" if up else "not running"
        accent = "#2E9E6B" if up else "#C9302C"
        return mo.callout(
            mo.md(
                f"### {dot} {role.value.title()} Agent\n\n"
                f"**{state}**\n\n"
                f"`{info['url']}`  ·  port `{info['port']}`"
            ),
            kind="success" if up else "danger",
        )

    mo.hstack(
        [_card(r, info) for r, info in statuses.items()],
        widths="equal",
        gap=1,
    )
    return


@app.cell(hide_code=True)
def _(mo, statuses):
    # A compact roll-up table beneath the cards.
    _rows = [
        {
            "Agent": r.value,
            "Port": info["port"],
            "URL": info["url"],
            "Status": "up" if info["up"] else "down",
        }
        for r, info in statuses.items()
    ]
    _up = sum(1 for i in statuses.values() if i["up"])
    mo.vstack(
        [
            mo.md(f"**{_up} / {len(statuses)} agents reachable**"),
            mo.ui.table(_rows, selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Launch control (Tier 2 — subprocess manager)

        The console drives `AgentProcessManager` from the foundation. Each agent
        is an independent operating-system process; logs go to `logs/<role>.log`.
        The buttons are wired but **start nothing until pressed**, so opening the
        console launches no servers.
        """
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
    # One manager for the console session. Created once; reused by the buttons.
    manager = AgentProcessManager()
    return (manager)


@app.cell
def _(manager, mo, start_all_btn, stop_all_btn):
    # React to whichever button was pressed. run_button.value is True on the
    # run that the press triggers, then resets — so each branch fires once.
    _msg = "Idle — press a button to start or stop the agents."
    if start_all_btn.value:
        manager.start_all(wait=False)  # non-blocking; poll status above
        _msg = "Issued **start_all** — re-poll above to watch them come up."
    elif stop_all_btn.value:
        manager.stop_all()
        _msg = "Issued **stop_all** — agents terminated."
    mo.md(_msg)
    return


@app.cell(hide_code=True)
def _(manager, mo):
    # Process-level view from the manager (running/stopped), distinct from the
    # network probe above: this is "did we spawn it", the probe is "does it answer".
    _status = manager.status()
    if _status:
        mo.vstack(
            [
                mo.md("### Managed processes"),
                mo.ui.table(
                    [{"Agent": k, "Process": v} for k, v in _status.items()],
                    selection=None,
                ),
            ]
        )
    else:
        mo.md("*No processes managed yet this session.*")
    return


@app.cell(hide_code=True)
def _(mo, tier1_terminal_commands):
    mo.md(
        f"""
        ## Tier 1 fallback — run them yourself

        If you'd rather run each agent in its own terminal (live, separate logs,
        no notebook control), paste these in the project root:

        ```bash
        {tier1_terminal_commands()}
        ```
        """
    )
    return


if __name__ == "__main__":
    app.run()
