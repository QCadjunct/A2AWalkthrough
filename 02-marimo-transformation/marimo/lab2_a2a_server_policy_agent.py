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
# Lesson 2 - Wrapping the QA Agent into an A2A Server

In this lesson, you will take the `PolicyAgent` created in Lesson 1 and wrap it into an Agent2Agent (A2A) server. This makes the agent discoverable and callable by other agents using the A2A protocol. You will define the agent's identity using an `AgentCard`, describe its capabilities using `AgentSkill`, and set up the request handling logic.

"""
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
## 2.1. Define the A2A Server

The server code is provided in `a2a_policy_agent.py`. This script performs the following steps:
1.  **Imports**: Loads necessary modules including the A2A SDK (`a2a.server`).
2.  **Executor**: Defines `PolicyAgentExecutor`, which bridges the A2A request context to your `PolicyAgent` class.
3.  **Metadata**: configure the `AgentSkill` (defining *what* it can do) and the `AgentCard` (defining *who* it is, including its URL).
4.  **Application**: Creates and runs an `A2AStarletteApplication` using `uvicorn`.

"""
    )
    return


@app.cell
def _():
    from IPython.display import Code, display

    display(Code("a2a_policy_agent.py"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
## 2.2. Run the Policy A2A Server

Now to activate your configured A2A agent, you would need to run your agent server. You can run the agent server using `uv`:

- Open a terminal as instructed below.
- Type `uv run a2a_policy_agent.py` to run the server and activate your A2A agent.
"""
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
<div style="background-color:#e8f0fe; padding:15px; border-left:5px solid #4285f4; border-radius:4px">
    <b>Terminal Access:</b> Please open a new terminal window in your Jupyter environment to run the server.
    <br>You can typically do this by selecting <i>File -> New -> Terminal</i> from the menu.
</div>
"""
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
## 2.3. Resources

- [Agent2Agent Protocol Documentation](https://a2a-protocol.org/)
- [A2A Python SDK Documentation](https://a2a-protocol.org/latest/sdk/python/api/)
- [Starlette Documentation](https://www.starlette.io/)
"""
    )
    return


if __name__ == "__main__":
    app.run()
