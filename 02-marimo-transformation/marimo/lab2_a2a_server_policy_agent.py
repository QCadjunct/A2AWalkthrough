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
        # Lab 2 — A Governed, Choosable Tool

        Lab 1 built the governed objects in a Read-Eval-Print Loop (REPL). Lab 2
        normalizes the next step and adds, in depth, three enhancements over the
        upstream Policy agent:

        1. **Correlation** — the response is BLAKE3-correlated to its request.
        2. **Fully Qualified Skills Name (FQSN)** — a polymorphic skill identity.
        3. **A default and an override** — two triplets, one vendor, gated at
           runtime by `OverrideDefault`.

        Everything runs with `uv`; the live server section runs on the cluster.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 2.1 — Correlation: the response carries its identity

        `handle()` takes ONLY the prompt; identity is derived from the role, so
        nothing is hand-typed. `respond()` returns a `WorkspaceResponseObject`
        whose `correlation_id` is the request's BLAKE3 pair hash.
        """
    )
    return


@app.cell
def _():
    from a2a_labs import make_policy_executor

    def demo_agent(prompt: str) -> str:
        return "In-network therapy: \\$25 copay per session."

    executor = make_policy_executor(demo_agent)
    response = executor.handle("How much does therapy cost?")
    {
        "status": str(response.status),
        "source_agent": response.source_agent,
        "correlation_id": response.correlation_id,
    }


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ### Fitness test — the response correlates to its request

        `expected_request()` rebuilds the request the executor used, so we can
        check correlation without hand-typing any identity.
        """
    )
    return


@app.cell
def _():
    from a2a_labs import make_policy_executor as _mpe

    ex = _mpe(lambda p: "answer")
    resp = ex.handle("How much does therapy cost?")
    expected = ex.expected_request("How much does therapy cost?")
    {"correlated": resp.correlation_id == expected.blake3_pair_hash}


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 2.2 — FQSN: a polymorphic skill identity

        A Fully Qualified Skills Name (FQSN) is the governed skill identity. It is
        substrate-independent: the SAME identity resolves through a filesystem
        adapter or a database adapter via one `SkillResolver` port.
        """
    )
    return


@app.cell
def _():
    from a2a_labs import FQSN, FilesystemAdapter, DatabaseAdapter, SkillResolver

    fqsn = FQSN.parse("policy.insurance_coverage")
    fs = FilesystemAdapter(root=".")    # resolves to a hierarchical trifecta folder
    db = DatabaseAdapter()              # same port, not implemented in the labs
    {
        "identity": fqsn.name,
        "segments": fqsn.segments,
        "fs_is_resolver": isinstance(fs, SkillResolver),
        "db_is_resolver": isinstance(db, SkillResolver),
    }


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 2.3 — A default and an override, gated by OverrideDefault

        A tool holds two triplets `(FQSN, Vendor, VendorModel)` sharing ONE
        vendor: a default and an override. The `OverrideDefault` gate (FALSE/TRUE)
        is the whole runtime choice. The override commonly keeps the default's
        vendor and model, choosing a different skill.
        """
    )
    return


@app.cell
def _():
    from a2a_labs import FQSN, Vendor, VendorModel, Triplet, ToolMenu, OverrideDefault, menu_for

    default = Triplet(
        fqsn=FQSN.parse("policy.insurance_coverage"),
        vendor=Vendor.GOOGLE,
        model=VendorModel.GEMINI_FLASH_LITE,
    )
    override = Triplet(
        fqsn=FQSN.parse("policy.claims_status"),
        vendor=Vendor.GOOGLE,
        model=VendorModel.GEMINI_FLASH_LITE,
    )
    menu = menu_for("policy_tool", "v2026.06.02", default, override)
    {
        "default": menu.invoke(OverrideDefault.FALSE).as_pointers(),
        "override": menu.invoke(OverrideDefault.TRUE).as_pointers(),
        "one_vendor": menu.default.vendor is menu.override.vendor,
    }


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## 2.4 — Serving it live (on the cluster)

        The `AgentCard` is built from the registry, the executor serves over
        uvicorn on `AgentRole.POLICY.port`. Needs the Agent-to-Agent (A2A)
        software development kit, a model key, and the policy Portable Document
        Format (PDF), so run on the cluster:

        ```bash
        uv run python -m a2a_labs.servers.policy_server
        #   Policy A2A server (governed) on http://localhost:9999/
        ```

        On the cluster, replace `demo_agent` with the governed agent:

        ```python
        from a2a_labs.agents.policy_agent import PolicyAgent
        agent = PolicyAgent()                       # reads PDF via data_path()
        executor = make_policy_executor(agent.answer_query)
        ```

        The returned artifact text is the `WorkspaceResponseObject` serialized to
        JSON (the serializable form); YAML / Token-Optimized Object Notation
        (TOON) / Markdown are informative companions.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## What Lab 2 added (one normalized increment)

        - Correlated `WorkspaceResponseObject` instead of bare text.
        - A polymorphic FQSN skill identity instead of an inline string.
        - A default/override tool menu, one vendor, gated by `OverrideDefault`.

        **Next — Lab 3:** the client that consumes the correlated response and
        verifies the correlation on its own side.
        """
    )
    return


if __name__ == "__main__":
    app.run()
