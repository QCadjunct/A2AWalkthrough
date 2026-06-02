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
# Lesson 4 - Creating an A2A Health Research Agent using Google ADK

In this lesson, you will build a second agent: a Health Research Agent. Unlike the Policy Agent which used PDF documents, this agent will use Google's Agent Development Kit (ADK) and a tool to search the web for health information. You will also see how to easily wrap an ADK agent into an A2A server using the `to_a2a` helper function.
"""
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
## 4.1. Define the Research Agent

The agent code is provided in `a2a_research_agent.py`.
- **Google ADK**: You will use `LlmAgent` from `google.adk`, which simplifies agent creation.
- **Tools**: You will equip the agent with `google_search` to allow it to fetch external information.
- **A2A Integration**: Instead of manually defining the Executor and RequestHandler as in Lesson 2, you will use `google.adk.a2a.utils.agent_to_a2a.to_a2a` to automatically wrap the ADK agent into an A2A-compliant application.
"""
    )
    return


@app.cell
def _():
    from IPython.display import Code, display

    display(Code("a2a_research_agent.py"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
## 4.2. Run the Research Agent Server

Now, activate your new Research Agent.
- Open a terminal (Terminal 2) as instructed below.
- Type `uv run a2a_research_agent.py`.
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
## 4.3. Resources

- [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/)
- [ADK A2A Integration](https://google.github.io/adk-docs/a2a/)

"""
    )
    return


if __name__ == "__main__":
    app.run()
