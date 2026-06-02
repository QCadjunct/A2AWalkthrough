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
        # Lab 3 — Calling an A2A Agent using an A2A Client

        You use the Agent-to-Agent (A2A) Python client to talk to the Policy
        Agent you started in Lab 2. The client handles protocol details:
        discovering the agent's capabilities via its Agent Card, then sending
        messages.

        **Prerequisite:** the Policy Agent must be running on port 9999. Start
        it with the launcher notebook (`lab0_launcher.py`) or
        `uv run a2a_policy_agent.py`. The check cell below confirms it before
        you query.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 3.1 Setup — settings and the target agent URL")
    return


@app.cell
def _():
    import httpx
    from a2a.client import (
        Client,
        ClientConfig,
        ClientFactory,
        create_text_message_object,
    )
    from a2a.types import Artifact, Message, Task
    from a2a.utils.message import get_message_text

    from a2a_labs import AgentRole, setup_env
    from a2a_labs.orchestrator import is_up
    from helpers import display_agent_card

    settings = setup_env()
    target_url = settings.url_for(AgentRole.POLICY)
    target_url
    return (
        Artifact,
        Client,
        ClientConfig,
        ClientFactory,
        Message,
        Task,
        create_text_message_object,
        display_agent_card,
        get_message_text,
        httpx,
        is_up,
        settings,
        target_url,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 3.2 Confirm the agent is reachable before sending anything")
    return


@app.cell
def _(is_up, mo, target_url):
    _ok = is_up(target_url)
    mo.callout(
        mo.md(
            f"Policy Agent at `{target_url}` is "
            + (
                "**reachable**. You can query below."
                if _ok
                else "**not running**. Start it first."
            )
        ),
        kind="success" if _ok else "danger",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 3.3 Pick a prompt")
    return


@app.cell
def _(mo):
    prompt_box = mo.ui.text_area(
        value="How much would I pay for mental health therapy?",
        label="Prompt to send to the Policy Agent",
        full_width=True,
    )
    prompt_box
    return (prompt_box,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 3.4 Run the client interaction

        Connect with `ClientFactory`, discover the Agent Card, construct a text
        message, send it, and process the response stream (which may carry
        Tasks, Artifacts, or Messages).
        """
    )
    return


@app.cell
async def _(
    Artifact,
    Client,
    ClientConfig,
    ClientFactory,
    Message,
    Task,
    create_text_message_object,
    display_agent_card,
    get_message_text,
    httpx,
    prompt_box,
    target_url,
):
    text_content = ""
    async with httpx.AsyncClient(timeout=100.0) as _http:
        _client: Client = await ClientFactory.connect(
            target_url.rstrip("/"),
            client_config=ClientConfig(httpx_client=_http),
        )
        _card = await _client.get_card()
        display_agent_card(_card)

        _message = create_text_message_object(content=prompt_box.value)
        async for _resp in _client.send_message(_message):
            if isinstance(_resp, Message):
                text_content = get_message_text(_resp)
            elif isinstance(_resp, tuple):
                _task: Task = _resp[0]
                if _task.artifacts:
                    _artifact: Artifact = _task.artifacts[0]
                    text_content = get_message_text(_artifact)
    text_content
    return (text_content,)


@app.cell
def _(mo, text_content):
    mo.md(
        f"### Final Agent Response\n\n-----\n\n{text_content or '*No content received.*'}"
    )
    return


if __name__ == "__main__":
    app.run()
