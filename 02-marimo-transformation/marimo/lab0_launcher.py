import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # Parallel Agent Launcher

        The four agents in this project are **Asynchronous Server Gateway
        Interface (ASGI)** applications, each run by uvicorn on its own port.
        A Marimo notebook is a reactive Python program, **not** an ASGI host —
        so the agents run as separate processes, and this notebook (and the lab
        notebooks) act as **clients** that reach them over Hypertext Transfer
        Protocol (HTTP).

        This notebook offers three ways to bring the system up, simplest to most
        complex. Pick the tier that matches how much control you need.
        """
    )
    return


@app.cell
def _():
    from a2a_labs import AgentRole, setup_env
    from a2a_labs.orchestrator import (
        AgentProcessManager,
        AsyncAgentSupervisor,
        TIER_COMPARISON,
        is_up,
        tier1_terminal_commands,
    )

    settings = setup_env()
    return (
        AgentProcessManager,
        AgentRole,
        AsyncAgentSupervisor,
        TIER_COMPARISON,
        is_up,
        settings,
        tier1_terminal_commands,
    )


@app.cell(hide_code=True)
def _(TIER_COMPARISON, mo):
    mo.md(
        f"""
        ## The three tiers at a glance

        ```
        {TIER_COMPARISON}
        ```

        | Tier | Startup | Logs | Notebook control | Best for |
        |------|---------|------|------------------|----------|
        | **1 Terminal** | manual, 4 shells | live, separate | none | first run, debugging one agent |
        | **2 Subprocess** | one `start_all()` | per-agent files | start/stop/restart each | incremental notebook testing |
        | **3 Asyncio** | concurrent | one tagged feed | full async control | full demo / class presentation |
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Tier 1 — Terminal commands (no process management)

        Simplest possible. Paste each line into its own terminal in the project
        root. Each agent's logs stay cleanly separated and Ctrl-C stops exactly
        one server. The cost: fully manual, and the notebook cannot start or
        stop anything.
        """
    )
    return


@app.cell
def _(mo, tier1_terminal_commands):
    mo.md(f"```bash\n{tier1_terminal_commands()}\n```")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Tier 2 — Subprocess manager (one object, one button)

        A middle ground for incremental testing. One `AgentProcessManager`
        spawns each agent as an independent operating-system process (clean
        isolation — one crashing does not take the others down, and you can
        restart a single one). Logs are written to files under `logs/`, so you
        tail a file to watch a server.

        Uncomment the calls below to drive it. They are commented so this
        notebook is safe to open without launching anything.
        """
    )
    return


@app.cell
def _(AgentProcessManager):
    manager = AgentProcessManager()
    # manager.start_all(wait=True)      # bring the whole system up
    # manager.status()                  # {'policy': 'running', ...}
    # manager.stop("policy")            # restart just one: stop then start
    # manager.start(AgentRole.POLICY)
    # manager.stop_all()                # tear everything down
    manager
    return (manager,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Tier 3 — Asyncio supervisor (concurrent startup, one log feed)

        The most capable tier. `AsyncAgentSupervisor` boots all four servers in
        parallel with `asyncio.create_subprocess_exec` and multiplexes every
        agent's output into a single feed, each line tagged with the agent name.
        The cost: most code, and it needs a running event loop (Marimo provides
        one; `setup_env()` already applied `nest_asyncio`).

        ```python
        supervisor = AsyncAgentSupervisor()
        await supervisor.start_all()        # parallel spawn
        ready = await supervisor.wait_ready()  # {'policy': True, 'research': True, ...}
        # ... run lab notebooks / client queries against the live agents ...
        await supervisor.stop_all()
        ```
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Health check — are the agents up?

        Run this any time to see live status. It probes each Agent Card. Safe to
        run whether or not anything is started; it simply reports what is up.
        """
    )
    return


@app.cell
def _(AgentRole, is_up, mo, settings):
    _rows = [
        f"| {role.value} | {settings.url_for(role)} | "
        f"{'\u2705 up' if is_up(settings.url_for(role)) else '\u2014 down'} |"
        for role in AgentRole
    ]
    mo.md(
        "| Agent | URL | Status |\n|---|---|---|\n" + "\n".join(_rows)
    )
    return


if __name__ == "__main__":
    app.run()
