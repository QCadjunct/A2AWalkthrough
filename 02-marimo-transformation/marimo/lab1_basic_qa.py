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
        # Lab 1 — Building a Question Answering (QA) Agent with Google Gemini

        Marimo conversion of Lesson 1. You build a QA agent that reads a health
        insurance policy Portable Document Format (PDF) and answers coverage
        questions, using [LiteLLM](https://www.litellm.ai/) to call the model.
        Then you refactor it into a reusable `PolicyAgent` class — the
        groundwork for wrapping it in an Agent-to-Agent (A2A) server in Lab 2.

        **Standards applied:** configuration comes from the Pydantic Version 2
        (V2) `Settings` object, and the model name is a `Model` Enum resolved to
        the right provider prefix (Gemini or Vertex Artificial Intelligence
        (Vertex AI)) by `settings.litellm_model(...)`.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 1.1 Setup — typed settings and the provider toggle")
    return


@app.cell
def _():
    import base64
    from pathlib import Path

    import litellm

    from a2a_labs import Model, setup_env

    settings = setup_env()
    settings.provider
    return Model, Path, base64, litellm, settings


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 1.2 Load and encode the policy PDF as Base64")
    return


@app.cell
def _(Path, base64):
    with Path("data/2026AnthemgHIPSBC.pdf").open("rb") as _file:
        pdf_data = base64.standard_b64encode(_file.read()).decode("utf-8")
    f"Encoded {len(pdf_data):,} Base64 characters"
    return (pdf_data,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 1.3 Query the model

        Edit the question below. Because Marimo is reactive, the answer cell
        re-runs automatically when the prompt changes.
        """
    )
    return


@app.cell
def _(mo):
    prompt_box = mo.ui.text_area(
        value="How much would I pay for mental health therapy?",
        label="Question",
        full_width=True,
    )
    prompt_box
    return (prompt_box,)


@app.cell
def _(Model, litellm, mo, pdf_data, prompt_box, settings):
    _response = litellm.completion(
        model=settings.litellm_model(Model.FLASH_LITE),
        reasoning_effort="minimal",
        max_tokens=1000,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert insurance agent designed to assist with "
                    "coverage queries. Use the provided documents to answer "
                    "questions about insurance policies. If the information is "
                    "not available in the documents, respond with 'I don't know'"
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_box.value},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:application/pdf;base64,{pdf_data}"
                        },
                    },
                ],
            },
        ],
    )
    response_text = _response.choices[0].message.content.replace("$", r"\$")
    mo.md(response_text)
    return (response_text,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 1.4 The refactored `PolicyAgent` class

        The same logic lives in `policy_agent.py` so the A2A server in Lab 2 can
        import it unchanged. Below we test that class directly.
        """
    )
    return


@app.cell
def _(mo):
    from policy_agent import PolicyAgent

    _agent = PolicyAgent()
    _answer = _agent.answer_query("How much would I pay for mental health therapy?")
    mo.md(_answer)
    return (PolicyAgent,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 1.5 Next — Lab 2 wraps this agent in an A2A server

        The `PolicyAgent` is transport-agnostic. In Lab 2 it becomes an
        Asynchronous Server Gateway Interface (ASGI) application served by
        uvicorn on port 9999.
        """
    )
    return


if __name__ == "__main__":
    app.run()
