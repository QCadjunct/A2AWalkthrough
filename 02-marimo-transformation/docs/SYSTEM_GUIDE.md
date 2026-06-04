# 🏗️ A2A Unified System — Module Guide

> The four healthcare agents — **Policy**, **Research**, **Provider**, **Healthcare** — were five separate framework scripts glued together by environment variables. This guide documents the modules that fold them into **one governed, Enum-driven application** served through Marimo + uvicorn, with zero hardcoding of identity.

**Mermaid dialect note:** all diagrams use `classDef` + `class` for node styling (no fragile `linkStyle` index-counting) and `style` only for subgraph backgrounds, for the lowest render-error surface.

---

## 📑 Table of Contents

1. [🗺️ Overview — How It All Fits Together](#overview)
2. [🧩 agent_framework.py — The Framework Enum](#agent-framework)
3. [🔧 mcp_tools.py — Governed MCP Tools](#mcp-tools)
4. [📇 agent_specs.py — Validated Agent Specifications](#agent-specs)
5. [🗂️ system_registry.py — The WORM System Registry](#system-registry)
6. [🖥️ system_console.py — The Marimo System Console](#system-console)
7. [📊 console_monitor.py — The Focused Monitor](#console-monitor)
8. [🚀 console_asgi.py — The Uvicorn ASGI Entry](#console-asgi)

---

<a id="overview"></a>

## 🗺️ Overview — How It All Fits Together

### 🎯 The Problem This Solves

The upstream A2A Walkthrough is a **segmented application**: each of the four agents is written against a different framework (raw A2A Software Development Kit, Google Agent Development Kit, LangGraph, Microsoft Agent Framework, BeeAI), and each agent script independently hardcodes its own identity — its port via `os.getenv`, its model as a string literal, its skill metadata inline, and (for the orchestrator) the set of agents it calls. The Model Context Protocol (MCP) tool name `"find_healthcare_providers"` appears as a free-form string in three places, while the MCP server actually names the tool `list_doctors` — a mismatch held together only by convention.

The unified application removes every one of those loose strings. **Identity becomes governed:** ports come from an Enum, models from a validated Enum, frameworks from an Enum, MCP tool names from an Enum, and skill identities from a Fully Qualified Skills Name (FQSN). The four agents are assembled once into a single immutable registry whose call graph is validated at import. A **prompt remains input** — it is the one string a user supplies at runtime — but nothing about *identity* is ever hand-typed.

### 🧱 The Layered Architecture

The application is built in layers, each depending only on the layer beneath it. The foundation (`a2a_labs`) supplies governed primitives; the new modules compose them into a system; the Marimo console consumes the system without ever touching a literal.

```mermaid
graph TB
    subgraph PRIMITIVES ["🔵    Foundation    Primitives    (a2a_labs)"]
        A1[enums.py<br/>AgentRole · AgentPort · Provider]
        A2[vendors.py<br/>Vendor · VendorModel]
        A3[fqsn.py<br/>FQSN · SkillResolver]
        A4[config.py<br/>Settings · url_for]
        A5[orchestrator.py<br/>is_up · launch tiers]
    end

    subgraph GOVERNANCE ["🟣    System    Governance    Layer"]
        B1[agent_framework.py<br/>AgentFramework Enum]
        B2[mcp_tools.py<br/>McpTool · McpServer]
        B3[agent_specs.py<br/>AgentSpec · SkillSpec]
        B4[system_registry.py<br/>SYSTEM · call graph]
    end

    subgraph PRESENTATION ["🟠    Presentation    Layer    (Marimo)"]
        C1[system_console.py<br/>registry · monitor · launch]
        C2[console_monitor.py<br/>focused monitor]
        C3[console_asgi.py<br/>uvicorn entry]
    end

    %% Foundation feeds governance
    A1 --> B3
    A2 --> B3
    A3 --> B3
    B1 --> B3
    B2 --> B3
    B3 --> B4

    %% Governance + foundation feed presentation
    B4 --> C1
    A4 --> C1
    A5 --> C1
    B4 --> C2
    C1 --> C3

    classDef foundationStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    classDef governanceStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef presentationStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000

    class A1,A2,A3,A4,A5 foundationStyle
    class B1,B2,B3,B4 governanceStyle
    class C1,C2,C3 presentationStyle

    style PRIMITIVES fill:#e8f4fd,stroke:#1976d2,stroke-width:3px,color:#000
    style GOVERNANCE fill:#f8f0ff,stroke:#7b1fa2,stroke-width:3px,color:#000
    style PRESENTATION fill:#fff4e6,stroke:#f57c00,stroke-width:3px,color:#000
```

**Reading the layers:** the foundation primitives (blue) are the closed sets and validated models that already shipped in `a2a_labs`. The governance layer (purple) is what this work adds — it composes those primitives into agent specifications and a validated registry. The presentation layer (orange) is the Marimo console, which reads the registry to render the system, monitor reachability, and launch agents. **Dependency flows strictly downward**: the console never imports an agent script or a literal; it imports the registry.

[↑ Back to TOC](#-table-of-contents)

### 🔄 The Runtime Workflow — Healthcare Concierge Round Trip

At runtime the Healthcare agent (the BeeAI orchestrator) is the front door. A user prompt arrives, the orchestrator consults its handoff list — which is governed by the registry, not hardcoded — and calls the Policy, Research, and Provider agents over A2A. The Provider agent in turn calls the MCP doctor server. This sequence shows the full path a single concierge query travels.

```mermaid
sequenceDiagram
    actor User
    participant H as 🧠 Healthcare<br/>(BeeAI orchestrator)
    participant P as 📋 Policy<br/>(raw A2A)
    participant R as 🔬 Research<br/>(ADK)
    participant V as 🏥 Provider<br/>(LangGraph)
    participant M as 🔧 MCP doctorserver

    User->>H: prompt (input, not hardcoded)
    Note over H: consults registry handoffs:<br/>POLICY · RESEARCH · PROVIDER

    H->>P: A2A: what does the policy cover?
    P-->>H: coverage answer (correlated)

    H->>R: A2A: research the condition
    R-->>H: web-sourced findings

    H->>V: A2A: find providers nearby
    V->>M: MCP call: list_doctors(state, city)
    M-->>V: matching doctors
    V-->>H: provider list

    H-->>User: aggregated concierge answer
```

**Why this matters for the design:** the orchestrator's three handoff edges are not written into the BeeAI agent as literals — they are declared once on the Healthcare `AgentSpec` and validated by the registry to point at real, registered roles. Change the call graph by editing one spec; the workflow above reshapes automatically.

[↑ Back to TOC](#-table-of-contents)

### 🧩 Extensibility — Adding to the System

The governance layer is designed so that each kind of addition touches exactly one place and never the UI. The following workflow shows what a developer does for each type of extension, and which single module absorbs the change.

```mermaid
graph LR
    subgraph TRIGGER ["📥    Extension    Trigger"]
        E1[Add an agent]
        E2[Add a framework]
        E3[Add an MCP tool]
        E4[Add a model]
    end

    subgraph TARGET ["🟣    Single    Module    Touched"]
        T1[new AgentSpec<br/>in system_registry]
        T2[new member<br/>in AgentFramework]
        T3[new member<br/>in McpTool]
        T4[new member<br/>in VendorModel]
    end

    subgraph RESULT ["🟢    Automatic    Propagation"]
        Z1[registry validates<br/>+ console renders]
        Z2[validators re-run<br/>at import]
    end

    E1 --> T1
    E2 --> T2
    E3 --> T3
    E4 --> T4

    T1 --> Z1
    T2 --> Z2
    T3 --> Z2
    T4 --> Z2
    Z2 --> Z1

    classDef triggerStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    classDef targetStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef resultStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000

    class E1,E2,E3,E4 triggerStyle
    class T1,T2,T3,T4 targetStyle
    class Z1,Z2 resultStyle

    style TRIGGER fill:#e8f4fd,stroke:#1976d2,stroke-width:3px,color:#000
    style TARGET fill:#f8f0ff,stroke:#7b1fa2,stroke-width:3px,color:#000
    style RESULT fill:#f0f8f0,stroke:#388e3c,stroke-width:3px,color:#000
```

**The extensibility contract, stated plainly:**

- **A new agent** is one `AgentSpec` added to the registry tuple. If it declares a handoff to an unregistered role, the registry refuses to build — the error surfaces at import, not at runtime.
- **A new framework** is one `AgentFramework` member. The console's framework labels and the per-agent cards pick it up with no further change.
- **A new MCP tool** is one `McpTool` member that names its server; the `SERVER_TOOLS` view and the console's MCP table derive it automatically.
- **A new model** is one `VendorModel` member carrying its owning vendor; the cascade validation guarantees no agent can pair a model with the wrong vendor.

Because every addition is a closed-set member or a validated model, **a typo fails at import, not in production** — the same discipline the foundation already enforces, now extended to the whole system.

[↑ Back to TOC](#-table-of-contents)

### 📈 Scaling — From Four Agents to Many

The registry pattern scales along three independent axes without architectural change, because the system is data (a tuple of specs) governed by validators, not a hand-wired graph.

| 📐 Scaling Axis | What Grows | What Stays Fixed |
|---|---|---|
| **More agents** | The `SYSTEM` tuple grows; ports come from `AgentPort` | Console, monitor, and launch logic — they iterate the registry |
| **More MCP servers** | `McpServer` / `McpTool` gain members; fan-out is derived | The Provider-style consumption pattern — one client, many tools |
| **Deeper call graphs** | Handoff tuples lengthen; multiple orchestrators allowed | Graph-closure validation — every edge still proven at import |
| **Horizontal instances** | Each agent is an independent uvicorn process | `is_up` health-probing; the monitor polls whatever exists |

The scaling story rests on one structural fact: **the registry is the single source of truth, navigated rather than copied.** The console does not contain a list of agents — it iterates `SYSTEM`. The monitor does not know four ports — it asks each spec for its role's port. The launch manager does not hardcode four scripts — it maps roles to scripts in one place. Add a fifth, sixth, or tenth agent, and every consumer scales with it because none of them holds a private copy of the agent list.

```mermaid
graph TB
    subgraph SOURCE ["🔷    Single    Source    of    Truth"]
        S1[SYSTEM registry<br/>tuple of AgentSpec]
    end

    subgraph CONSUMERS ["🟢    Consumers    Iterate,    Never    Copy"]
        D1[Console table]
        D2[Monitor probes]
        D3[Launch manager]
        D4[Call-graph render]
    end

    subgraph GROWTH ["🟠    Scales    Without    Edits"]
        G1[N agents]
        G2[N MCP servers]
        G3[N handoff edges]
    end

    S1 --> D1
    S1 --> D2
    S1 --> D3
    S1 --> D4

    G1 --> S1
    G2 --> S1
    G3 --> S1

    classDef sourceStyle fill:#e0f2f1,stroke:#00695c,stroke-width:3px,color:#000
    classDef consumerStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    classDef growthStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000

    class S1 sourceStyle
    class D1,D2,D3,D4 consumerStyle
    class G1,G2,G3 growthStyle

    style SOURCE fill:#f0fffe,stroke:#00695c,stroke-width:3px,color:#000
    style CONSUMERS fill:#f0f8f0,stroke:#388e3c,stroke-width:3px,color:#000
    style GROWTH fill:#fff4e6,stroke:#f57c00,stroke-width:3px,color:#000
```

[↑ Back to TOC](#-table-of-contents)

### 🗂️ The Seven Modules at a Glance

| Module | Layer | Responsibility |
|---|---|---|
| `agent_framework.py` | Governance | The five frameworks as a closed Enum |
| `mcp_tools.py` | Governance | MCP tool + server names as Enums; eliminates the repeated literal |
| `agent_specs.py` | Governance | `AgentSpec` / `SkillSpec` with cross-object validators |
| `system_registry.py` | Governance | The four specs as one validated, immutable registry |
| `system_console.py` | Presentation | Full Marimo console: registry, call graph, monitor, launch |
| `console_monitor.py` | Presentation | Focused reachability monitor page |
| `console_asgi.py` | Presentation | Uvicorn ASGI entry that serves the console |

Each of the following sections documents one module in depth, with the workflow or sequence diagram that clarifies its internal behavior.

[↑ Back to TOC](#-table-of-contents)

---
