# Architecture — The Multi-Agent Healthcare System

The eight labs build up to one system: a Healthcare Concierge that coordinates
three specialist agents over the Agent-to-Agent (A2A) protocol. Each agent is an
Asynchronous Server Gateway Interface (ASGI) server on its own port.

```mermaid
flowchart LR
    User([User / A2A Client])

    subgraph Orchestrator [Lab 8 · Router]
        Concierge["Healthcare Concierge<br/>(BeeAI RequirementAgent)<br/>:9996"]
    end

    subgraph Specialists [A2A Agent Servers]
        direction TB
        Policy["Policy Agent<br/>(A2A SDK · Lab 2)<br/>:9999"]
        Research["Research Agent<br/>(Google ADK · Lab 4)<br/>:9998"]
        Provider["Provider Agent<br/>(LangGraph · Lab 6)<br/>:9997"]
    end

    subgraph Tools [Data & Tools]
        PDF["Policy PDF"]
        Search["Google Search"]
        MCP["FastMCP Server<br/>doctors.json"]
    end

    User -->|A2A| Concierge
    Concierge -->|A2A handoff| Policy
    Concierge -->|A2A handoff| Research
    Concierge -->|A2A handoff| Provider
    Policy -->|reads| PDF
    Research -->|calls| Search
    Provider -->|MCP stdio| MCP

    classDef orch fill:#7C3AED,stroke:#4C1D95,color:#fff;
    classDef agent fill:#EDE9FE,stroke:#7C3AED,color:#1E1B4B;
    classDef tool fill:#FEF3C7,stroke:#F59E0B,color:#1E1B4B;
    class Concierge orch;
    class Policy,Research,Provider agent;
    class PDF,Search,MCP tool;
```

## How the labs build toward this

```mermaid
flowchart TD
    L1["Lab 1<br/>QA Agent (class)"] --> L2["Lab 2<br/>A2A Server :9999"]
    L2 --> L3["Lab 3<br/>A2A Client"]
    L3 --> L4["Lab 4<br/>ADK Research :9998"]
    L4 --> L5["Lab 5<br/>Sequential chain"]
    L5 --> L6["Lab 6<br/>Provider + MCP :9997"]
    L6 --> L7["Lab 7<br/>Microsoft client"]
    L7 --> L8["Lab 8<br/>BeeAI Orchestrator :9996"]

    style L1 fill:#EDE9FE,stroke:#7C3AED,color:#1E1B4B
    style L8 fill:#7C3AED,stroke:#4C1D95,color:#fff
```

## Two protocols, two jobs

The Model Context Protocol (MCP) connects an agent to **tools** (the Provider
agent calls the doctor-lookup tool over MCP stdio). The A2A protocol connects
agents to **each other** (the Concierge hands off to the three specialists). The
Provider agent plays both roles at once: an MCP client to its tool, and an A2A
server to the world.

## Ports (from `AgentPort` IntEnum / `example.env`)

| Agent | Port | Framework | Lab |
|-------|------|-----------|-----|
| Policy | 9999 | A2A SDK | 2 |
| Research | 9998 | Google ADK | 4 |
| Provider | 9997 | LangGraph + MCP | 6 |
| Healthcare (orchestrator) | 9996 | BeeAI | 8 |

All four must be running before the orchestrator starts. Use the parallel
launcher (`marimo/lab0_launcher.py`) — see `STANDARDS_AND_MARIMO.md`.
