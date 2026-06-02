# Lab Status — A2AWalkthrough (Marimo Transformation)

Snapshot for the 11:00 AM EST meeting. Status is stated plainly: "verified"
means run successfully; "import-clean" means it compiles and passes structural
checks but has not been executed against live agents in this build environment
(the heavy dependencies — Agent Development Kit (ADK), BeeAI, LangGraph — were
not installed here). Runtime verification of Labs 2+ happens on the cluster with
credentials.

## Foundation: `a2a_labs`
**Verified.** 33 exports resolve, every module compiles, full smoke test green.
Includes the Write Once Reuse Many (WORM) Enum-keyed cascade, the `fabric -L`-derived
model registry (78 models / 4 vendors), the `ModelMessage` wire object, and the
no-hardcode Enumerations (Enums) / Pydantic Version 2 (V2) settings.

## Labs

| Lab | Title | Notebook | Deck | Status |
|---|---|---|---|---|
| 1 | Basic Question Answering (QA) Agent | `lab1_basic_qa.py` | `Lab1_Darwinian_Reorder.pptx` (canonical) | **Verified** — foundation path runs end to end; deck finalized |
| 2 | A2A Server (Policy executor) | `lab2_a2a_server_policy_agent.py` | `Lab2_A2A_Server.pptx` | Import-clean, marimo-valid; live uvicorn run pending on cluster |
| 3 | A2A Client | `lab3_a2a_client.py` | `Lab3_A2A_Client.pptx` | Import-clean, marimo-valid; hand-authored; live run pending |
| 4 | ADK Research Agent | `lab4_adk_research_agent.py` | `Lab4_ADK_Research_Agent.pptx` | Import-clean, marimo-valid; needs ADK + key on cluster |

Labs 5–8 (ADK sequential, LangGraph + Model Context Protocol (MCP), Microsoft
client, BeeAI orchestrator) are present in `marimo/` and `slides/` and are
import-clean, to be runtime-verified after Lab 4.

## What is true to present
- The foundation is real, tested, and reused across all labs.
- Lab 1 runs and its deck is finished.
- Labs 2–4 are structurally complete and compile; they await live runs with
  credentials and heavy dependencies on the cluster.
- Nothing here is marked "done" that has not been checked at the stated level.

## Next (tomorrow afternoon, after the meeting)
Enhanced documentation across the package; runtime verification of Labs 2–4 on
the cluster; then Lab 2 build-out (Policy executor emitting a real
`ModelMessage` and `WorkspaceResponseObject` over live uvicorn).
