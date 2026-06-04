# 🔷 Section 3 — Hexagonal Architecture: Ports and Adapters

> **Continue, but append to a separate section from where you left off
> to avoid duplication and corruption.**
>
> This section is autonomous and self-contained.
> It covers Hexagonal Architecture (Cockburn 2005) as applied to ACES
> exclusively. It does not duplicate content from Section 1
> (Architecture Overview), Section 2 (D⁴ Methodology), or
> Sections 4–6 (forthcoming).

---

## 📋 Section 3 Table of Contents

- [3.1 What Hexagonal Architecture Is](#-31-what-hexagonal-architecture-is)
- [3.2 The ACES Hexagon — One MCP Server](#-32-the-aces-hexagon--one-mcp-server)
- [3.3 Port 1 — TransportPort](#-33-port-1--transportport)
- [3.4 Port 2 — ACESWorkspacePort](#-34-port-2--acesworkspaceport)
- [3.5 Port 3 — MessageBusPort](#-35-port-3--messagebusport)
- [3.6 Port 4 — RegistryPort](#-36-port-4--registryport)
- [3.7 Pydantic V2 as the Message Contract](#-37-pydantic-v2-as-the-message-contract)
- [3.8 MVP Adapter Implementations](#-38-mvp-adapter-implementations)
- [3.9 Port vs system.md — Interface vs Constitution](#-39-port-vs-systemmd--interface-vs-constitution)
- [3.10 Extensibility Guarantee](#-310-extensibility-guarantee)
- [3.11 Implementation Sequence](#-311-implementation-sequence)

---

## 🎯 3.1 What Hexagonal Architecture Is

**Hexagonal Architecture** — also called Ports and Adapters — was
defined by Alistair Cockburn in 2005:

> *"Allow an application to equally be driven by users, programs,
> automated tests or batch scripts, and to be developed and tested
> in isolation from its eventual run-time devices and databases."*

The central insight is deceptively simple:

> *"Define the shape of how the outside world talks to your
> application, then implement that shape as many times as needed."*

In Cockburn's model:

- The **hexagon** is the application — it contains all business logic
- The **port** is the interface contract — the shape the outside world
  must use to talk to the hexagon
- The **adapter** is a specific implementation of that port for a
  specific technology

The hexagon never imports a transport library. It never imports a
database driver. It never imports a message broker. It imports only
port contracts. Every technology concern lives in an adapter — outside
the hexagon.

**Why hexagonal architecture was already present in ACES before it
was named:**

The Navigator observed during Session A (2026-05-03) that
`TransportAdapter` and `MessageBus` were Ports and Adapters in
Cockburn's sense — before that name was applied. That is the sign
of a correct design: the pattern emerges from the problem, not from
the textbook. ADR-063 names what was already being built.

---

## 🔷 3.2 The ACES Hexagon — One MCP Server

Each MCP server in `task-group.d4-database-design` is exactly
one hexagon. The hexagon contains governed business logic and a
`system.md` behavioral contract. It exposes exactly four ports.

```mermaid
flowchart TD

    subgraph CALLERS ["📡    Inbound    Callers    —    Left    Side"]
        CL1[HTTP Client\nADR-061]
        CL2[Ray Task\nADR-062]
        CL3[stdio\nMVP default]
        CL4[gRPC Client\nplanned]
    end

    subgraph CONTEXT ["🔄    Session    Context    —    Bidirectional"]
        WS1[AdfExecutor\nadmin role\nread-write]
        WS2[All Agents\nagent role\nread-only]
    end

    subgraph HEXAGON ["🔷    MCP    Server    Hexagon    —    Business    Logic    Only"]

        subgraph TP ["🔌    TransportPort\nInbound"]
            T1[McpRequest\nvalidated by\nPydantic V2]
            T2[McpResponse\nvalidated by\nPydantic V2]
        end

        subgraph WP ["🗂️    ACESWorkspacePort\nBidirectional"]
            W1[ACESWorkspaceContext\noperator.add\nWORM append-only]
        end

        subgraph CORE ["🧠    Business    Logic    —    Governed    by    system.md"]
            BL1[ingest_glossary\nD4 taxonomy\nBLAKE3 PAIR_HASH]
            BL2[resolve_fqdn\nFQSN gate check\nthree-key lookup]
            BL3[calculate_reuse\nexpansion ratio\ncross-domain overlap]
        end

        subgraph MB ["📨    MessageBusPort\nOutbound"]
            M1[publish\nconsume\nack]
        end

        subgraph RP ["🗄️    RegistryPort\nOutbound"]
            R1[write BGD\nwrite term\nwrite overlap\ndisable\nread]
        end

    end

    subgraph DESTINATIONS ["💿    Outbound    Destinations    —    Right    Side"]
        DS1[Ray Object Store\nADR-062]
        DS2[InProcess Bus\nMVP test]
        DS3[DuckDB Registry\nPhase 1]
        DS4[PostgreSQL Registry\nADR-065 planned]
    end

    CL1 --> T1
    CL2 --> T1
    CL3 --> T1
    CL4 --> T1
    T1 --> BL1
    T1 --> BL2
    T1 --> BL3
    WS1 --> W1
    WS2 --> W1
    W1 --> BL1
    W1 --> BL2
    W1 --> BL3
    BL1 --> M1
    BL2 --> M1
    BL3 --> M1
    BL1 --> R1
    BL2 --> R1
    BL3 --> R1
    BL1 --> T2
    BL2 --> T2
    BL3 --> T2
    M1 --> DS1
    M1 --> DS2
    R1 --> DS3
    R1 --> DS4

    style CALLERS fill:#e8f4fd,stroke:#1976d2,stroke-width:2px
    style CONTEXT fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    style HEXAGON fill:#f8f0ff,stroke:#7b1fa2,stroke-width:3px
    style TP fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style WP fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    style CORE fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style MB fill:#fff4e6,stroke:#f57c00,stroke-width:2px
    style RP fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style DESTINATIONS fill:#f0f8f0,stroke:#388e3c,stroke-width:2px

    classDef callerStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef contextStyle fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef portStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef coreStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    classDef outStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef destStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px

    class CL1,CL2,CL3,CL4 callerStyle
    class WS1,WS2 contextStyle
    class T1,T2,W1,M1,R1 portStyle
    class BL1,BL2,BL3 coreStyle
    class DS1,DS2,DS3,DS4 destStyle
```

### 📐 The Four Ports at a Glance

| Port | Direction | Semantic Role | WORM | Write Authority |
|------|-----------|--------------|------|----------------|
| `TransportPort` | Inbound | Work unit delivery | No | Any caller |
| `ACESWorkspacePort` | Bidirectional | Session context propagation | Yes — append only | Admin role only |
| `MessageBusPort` | Outbound | Work result exchange | No | Hexagon only |
| `RegistryPort` | Outbound | BGD registry writes | Yes — no deletes | Admin role only |

> **The invariant:** The hexagon never knows which adapter is
> plugged into any of its four ports. It imports only port contracts.
> Technology decisions live entirely in adapters.

---

## 🔌 3.3 Port 1 — TransportPort

**Semantic role:** Work unit delivery from callers to the hexagon.

**Direction:** Inbound — callers push `McpRequest` in, the hexagon
pushes `McpResponse` out.

**Why it exists:** Without `TransportPort`, the MCP server must
import HTTP libraries, Ray libraries, or stdio handling directly.
Each import couples the business logic to a specific transport.
When the transport changes — from `stdio` to HTTP (ADR-061), from
HTTP to gRPC — the business logic must change. `TransportPort`
breaks that coupling permanently.

```mermaid
flowchart LR

    subgraph INBOUND ["📥    Inbound    —    TransportPort"]

        subgraph REQUEST ["📨    McpRequest    —    ACESBaseModel"]
            RQ1[tool_name: str\nWhich tool to invoke]
            RQ2[session_id: str\nUUIDv7 session identifier]
            RQ3[role: str\nadmin or agent or client]
            RQ4[fqsn_path: str\nGoverning skill path\nUngoverned calls rejected]
            RQ5[payload: dict\nTool-specific arguments]
        end

        subgraph RESPONSE ["📤    McpResponse    —    ACESBaseModel"]
            RS1[session_id: str\nEchoed for correlation]
            RS2[tool_name: str\nEchoed for audit]
            RS3[status: str\nok or error or rejected]
            RS4[result: dict\nTool output]
            RS5[error_msg: str\nDefault empty string\nNever NULL]
        end

    end

    subgraph ADAPTERS ["🔧    TransportPort    Adapters"]

        subgraph MVP ["🟢    MVP"]
            A1[StdioTransportAdapter\nreceive: stdin bytes\nsend: stdout bytes\nZero infrastructure]
        end

        subgraph PROD ["🔵    Production"]
            A2[HttpTransportAdapter\nRay Serve endpoint\nADR-061 implementation]
            A3[RayTransportAdapter\nRay Task as caller\nADR-062 integration]
        end

        subgraph PLANNED ["🟡    Planned"]
            A4[GrpcTransportAdapter\nACESSpawnedChain\nagent-to-agent]
        end

    end

    subgraph GATE ["🔐    Validation    Gate    —    At    the    Port"]
        G1[Pydantic V2 fires\nat deserialization\nBEFORE hexagon sees request]
        G2[ValidationError raised here\nnot inside hexagon\nMalformed requests rejected]
        G3[FQSN gate check\nresolve fqsn_path\nreject if not governed]
    end

    A1 -->|implements| RQ1
    A2 -->|implements| RQ1
    A3 -->|implements| RQ1
    A4 -.->|planned| RQ1
    RQ1 --> G1
    RQ2 --> G1
    RQ3 --> G1
    RQ4 --> G3
    RQ5 --> G1
    G1 --> G2
    G3 --> G2

    style INBOUND fill:#e8f4fd,stroke:#1976d2,stroke-width:2px
    style REQUEST fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style RESPONSE fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style ADAPTERS fill:#f0f8f0,stroke:#388e3c,stroke-width:2px
    style MVP fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    style PROD fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    style PLANNED fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    style GATE fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    classDef reqStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef respStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef mvpStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef prodStyle fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef plannedStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef gateStyle fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class RQ1,RQ2,RQ3,RQ4,RQ5 reqStyle
    class RS1,RS2,RS3,RS4,RS5 respStyle
    class A1 mvpStyle
    class A2,A3 prodStyle
    class A4 plannedStyle
    class G1,G2,G3 gateStyle
```

### 🔬 TransportPort Contract

```python
from abc import ABC, abstractmethod
from src.base import ACESBaseModel


class McpRequest(ACESBaseModel):
    """
    Governed inbound request envelope.
    Pydantic V2 validates at instantiation — before hexagon sees it.
    The port is the validation gate. Not the hexagon.
    All callers produce McpRequest. The hexagon receives only McpRequest.
    """
    tool_name:   str
    session_id:  str
    role:        str    # admin | agent | client
    fqsn_path:   str    # ungoverned calls rejected before reaching hexagon
    payload:     dict


class McpResponse(ACESBaseModel):
    """
    Governed outbound response envelope.
    Pydantic V2 validates on construction — malformed responses
    caught before they leave the hexagon.
    """
    session_id:  str
    tool_name:   str
    status:      str        # ok | error | rejected
    result:      dict
    error_msg:   str = ""   # governed default — never NULL


class TransportPort(ABC):
    """
    Inbound port — work unit delivery.
    The hexagon depends on this ABC. Never on a concrete adapter.
    Swap StdioTransportAdapter for HttpTransportAdapter:
    zero changes to hexagon code.
    """

    @abstractmethod
    def receive(self, raw: bytes) -> McpRequest:
        """
        Deserialize raw inbound bytes to validated McpRequest.
        Pydantic V2 ValidationError raised here — not in hexagon.
        """
        ...

    @abstractmethod
    def send(self, response: McpResponse) -> bytes:
        """
        Serialize governed McpResponse to raw outbound bytes.
        Pydantic V2 ensures McpResponse is valid before serialization.
        """
        ...

    @abstractmethod
    def health(self) -> dict:
        """Transport-level health. Not agent health. Not registry health."""
        ...
```

---

## 🗂️ 3.4 Port 2 — ACESWorkspacePort

**Semantic role:** Session context propagation throughout the agent
chain. `ACESWorkspaceContext` is not a message. It is the WORM-governed
session envelope that flows *alongside* messages for the entire
lifetime of a Task Group execution.

**Direction:** Bidirectional — `AdfExecutor` writes and forwards.
All agents read. No agent writes directly.

**Why it is a separate port from `MessageBusPort`:**

This is the most important architectural distinction in the system.
The six differences that make sharing a port with `MessageBusPort`
architecturally wrong:

| Concern | ACESWorkspacePort | MessageBusPort |
|---------|-----------------|----------------|
| **Lifecycle** | Session open to session close | Publish, consume, ack, gone |
| **Write discipline** | `operator.add` — append only | Destructive consume |
| **Read access** | All agents, every call | One consumer per message |
| **Write authority** | Admin role only | Any hexagon |
| **WORM audit** | Full history preserved forever | Acked messages gone |
| **On timeout** | Context still exists | Returns `None` |

**Sharing one port for both would mix two governance models on
one wire. This decision is final. It is filed in ADR-063.**

```mermaid
sequenceDiagram
    participant Nav as Navigator\nadmin role
    participant Exec as AdfExecutor
    participant WP as ACESWorkspacePort
    participant BGD as BGD Hexagon\nagent role
    participant FQDN as FQDN Hexagon\nagent role

    Note over Nav,FQDN: ACESWorkspaceContext Lifecycle

    Nav->>WP: open(ACESWorkspaceContext)\nsession_id, task_group\nmanifest_id, role=admin
    WP-->>Nav: session_id returned

    Note over Exec,WP: AdfExecutor reads before dispatch

    Exec->>WP: read(session_id)
    WP-->>Exec: ACESWorkspaceContext\ncurrent_task_id: ingest-electricity\ncompleted_tasks: empty

    Note over Exec,BGD: Forward to BGD agent — operator.add

    Exec->>WP: forward(session_id, next=ingest-electricity)
    WP->>WP: completed_tasks.append\ncurrent_task_id updated\noperator.add — no overwrite
    WP-->>Exec: ACESWorkspaceContext updated

    Exec->>BGD: McpRequest plus ACESWorkspaceContext\nBGD reads context — never writes it

    BGD->>WP: read(session_id)\nrole=agent — read only
    WP-->>BGD: ACESWorkspaceContext

    Note over Exec,WP: AdfExecutor updates after completion

    Exec->>WP: update(session_id,\ndelta=last_completed:ingest-electricity,\nrole=admin)
    WP->>WP: accumulated_state.update(delta)\noperator.add — no overwrite\nWORM audit trail appended

    Note over Exec,FQDN: Forward to FQDN agent

    Exec->>WP: forward(session_id, next=promote-universal)
    WP-->>Exec: ACESWorkspaceContext\ncompleted_tasks: ingest-electricity

    Exec->>FQDN: McpRequest plus ACESWorkspaceContext
    FQDN->>WP: read(session_id)\nrole=agent — read only
    WP-->>FQDN: ACESWorkspaceContext

    Note over Nav,FQDN: Session close — admin only

    Nav->>WP: close(session_id, role=admin)
    WP->>WP: is_terminal = True\nFinal state preserved — never deleted
    WP-->>Nav: ACESWorkspaceContext\nis_terminal: True
```

### 🔬 ACESWorkspacePort Contract

```python
from abc import ABC, abstractmethod
from src.base import ACESBaseModel


class ACESWorkspaceContext(ACESBaseModel):
    """
    WORM-governed session context — the ACES canonical name.

    Forwarded and updated — not event-triggered.
    operator.add write discipline — never overwrite.
    Persists for session lifetime — never destructively consumed.
    Read by all agents. Written only by admin role via port methods.

    Pydantic V2 governs this object at every port boundary.
    No NULL-contaminated context can cross a port boundary.
    The WORM audit trail is a list of validated snapshots.
    """
    session_id:         str
    task_group:         str
    manifest_id:        str
    initiated_at:       str       # ISO-8601
    role:               str       # admin | agent | client
    fqsn_path:          str       # governing skill for current agent
    current_task_id:    str
    completed_tasks:    list[str] # WORM audit trail — append only
    accumulated_state:  dict      # operator.add — never replace
    is_terminal:        bool = False


class ACESWorkspacePort(ABC):
    """
    Bidirectional port — ACESWorkspaceContext propagation.
    Separate from MessageBusPort — different lifecycle,
    different write discipline, different governance model.
    This separation is final. See ADR-063.
    """

    @abstractmethod
    def open(self, context: ACESWorkspaceContext) -> str:
        """Open session. Admin role only. Returns session_id."""
        ...

    @abstractmethod
    def read(self, session_id: str) -> ACESWorkspaceContext:
        """Read current context. All roles permitted."""
        ...

    @abstractmethod
    def update(self, session_id: str, delta: dict,
               role: str) -> ACESWorkspaceContext:
        """
        Merge delta into accumulated_state via operator.add.
        Admin role only. WORM audit trail preserved.
        Never replaces — always appends.
        """
        ...

    @abstractmethod
    def forward(self, session_id: str,
                next_task_id: str) -> ACESWorkspaceContext:
        """
        Forward context to next agent.
        Appends current_task_id to completed_tasks via operator.add.
        Updates current_task_id to next_task_id.
        Called by AdfExecutor at each subtask boundary.
        Not event-triggered — explicitly called.
        """
        ...

    @abstractmethod
    def close(self, session_id: str,
              role: str) -> ACESWorkspaceContext:
        """
        Close session. Sets is_terminal=True.
        Final state preserved — never deleted.
        Admin role only.
        """
        ...
```

---

## 📨 3.5 Port 3 — MessageBusPort

**Semantic role:** Work unit exchange between agents within a
Task Group. Subtask inputs published by `AdfExecutor`. Results
consumed by the aggregation gate.

**Direction:** Outbound from the hexagon. `AdfExecutor` also
consumes results from this bus — the bus is shared infrastructure,
not owned by any single hexagon.

**Why it is separate from ACESWorkspacePort:** The bus
consumes messages destructively — once acked, a work unit
message is gone. `ACESWorkspaceContext` is never destroyed.
The governance models are incompatible on a shared wire.

```mermaid
flowchart LR

    subgraph PUBLISH ["📤    Publish    Side"]
        P1[AdfExecutor\npublishes subtask inputs\ntopic: task-group.task-id.input]
        P2[BGD Hexagon\npublishes results\ntopic: task-group.task-id.output]
        P3[Any hexagon\npublishes errors\ntopic: task-group.task-id.error]
    end

    subgraph BUS ["📨    MessageBusPort    —    ABC"]
        B1[publish\ntopic: str\nmessage: dict\nreturns: message_id]
        B2[consume\ntopic: str\ntimeout_seconds: int\nreturns: dict or None]
        B3[ack\nmessage_id: str\nreturns: bool\nUnacked messages redelivered]
    end

    subgraph CONSUME ["📥    Consume    Side"]
        C1[AdfExecutor\nconsumes results\nfrom all seven workers]
        C2[Overlap Task\nconsumes BGD manifests\naggregation gate]
        C3[Error Handler\nconsumes error topics\nFailurePolicy enforced]
    end

    subgraph ADAPTERS ["🔧    MessageBusPort    Adapters"]
        A1[InProcessBus\nMVP — dict in memory\nZero infrastructure\nProves interface]
        A2[RayObjectStoreBus\nProduction intra-cluster\nADR-062 implementation]
        A3[RabbitMqBus\nExternal system integration\nAMQP — not intra-cluster]
    end

    P1 --> B1
    P2 --> B1
    P3 --> B1
    B1 --> B2
    B2 --> B3
    B2 --> C1
    B2 --> C2
    B2 --> C3
    A1 -.->|implements| B1
    A2 -.->|implements| B1
    A3 -.->|implements| B1

    style PUBLISH fill:#e8f4fd,stroke:#1976d2,stroke-width:2px
    style BUS fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style CONSUME fill:#f0f8f0,stroke:#388e3c,stroke-width:2px
    style ADAPTERS fill:#fff4e6,stroke:#f57c00,stroke-width:2px

    classDef publishStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef busStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef consumeStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef adapterStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px

    class P1,P2,P3 publishStyle
    class B1,B2,B3 busStyle
    class C1,C2,C3 consumeStyle
    class A1,A2,A3 adapterStyle
```

### 🔬 MessageBusPort Contract

```python
from abc import ABC, abstractmethod


class MessageBusPort(ABC):
    """
    Outbound port — work unit exchange.
    topic convention: task-group.task-id.input | output | error

    The bus never knows what messages contain.
    Agents never know which bus carries their messages.
    Destructive consume — acked messages are gone.
    This is what makes it different from ACESWorkspacePort.
    """

    @abstractmethod
    def publish(self, topic: str, message: dict) -> str:
        """Publish to topic. Returns message_id for ack."""
        ...

    @abstractmethod
    def consume(self, topic: str,
                timeout_seconds: int = 30) -> dict | None:
        """Consume next message. Returns None on timeout — not an error."""
        ...

    @abstractmethod
    def ack(self, message_id: str) -> bool:
        """
        Acknowledge processing. Unacked messages redelivered
        per FailurePolicy in GroupTaskManifest.
        """
        ...
```

---

## 🗄️ 3.6 Port 4 — RegistryPort

**Semantic role:** BGD registry writes — the governed persistence
layer for every term, domain, and overlap record.

**Direction:** Outbound from the hexagon. The hexagon writes
governed records. The registry stores them. No hexagon reads
back what it wrote — reads happen through the FQSN registry
or through direct registry queries by the Navigator.

**WORM enforcement:** No hard deletes. `disable()` is the only
removal primitive. Every record written to the registry is
permanently auditable. The BLAKE3-256 PAIR_HASH on every record
ensures it cannot be modified without detection.

```mermaid
flowchart TD

    subgraph WRITES ["📝    Registry    Write    Operations"]
        W1[write_bgd\nOne per glossary source\nBGD.Registry table\nReturns PairHash]
        W2[write_term\nOne per governed domain\nBGD.Term table\nReturns PairHash]
        W3[write_overlap\nOne per cross-domain pair\nBGD.Overlap table\nReturns PairHash]
        W4[disable\nBy PairHash\nSets status=DISABLED\nRecord preserved — never deleted]
        W5[read\nBy PairHash\nAll roles permitted\nReturns None if disabled]
    end

    subgraph THREE_KEY ["🗝️    Three-Key    on    Every    Write"]
        TK1[RegistryId assigned\nBIGINT IDENTITY\nsequential surrogate]
        TK2[ObfuscatedId computed\nFeistel encrypt RegistryId\nconsumer-facing]
        TK3[PairHash computed\nBLAKE3-256\nRegistryId colon ObfuscatedId\nexternal identity returned]
    end

    subgraph ADAPTERS ["🔧    RegistryPort    Adapters"]
        A1[DuckDbRegistryAdapter\nPhase 1 — no Docker\nalready on FT stack\nMVP production]
        A2[InProcessRegistryAdapter\nDev and test harness\ndict in memory\nProves interface]
        A3[PostgreSqlRegistryAdapter\nADR-065 migration trigger\nProduction at scale]
    end

    subgraph TABLES ["💾    Registry    Tables    —    DuckDB    Phase    1"]
        T1[BGD.Registry\nOne row per BGD source\nbgd_name, source_url\nterm_count, expansion_ratio]
        T2[BGD.Term\nOne row per governed domain\nfqdn, schema_name\ndomain_name, sql_data_type\ndefault_value, check_constraint]
        T3[BGD.Overlap\nOne row per cross-domain pair\nterm_id_1, term_id_2\nsimilarity, overlap_type\nproposed_fqdn]
    end

    W1 --> TK1
    W2 --> TK1
    W3 --> TK1
    TK1 --> TK2
    TK2 --> TK3
    TK3 --> T1
    TK3 --> T2
    TK3 --> T3
    A1 -.->|implements| W1
    A2 -.->|implements| W1
    A3 -.->|implements| W1

    style WRITES fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style THREE_KEY fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style ADAPTERS fill:#f0f8f0,stroke:#388e3c,stroke-width:2px
    style TABLES fill:#e8f4fd,stroke:#1976d2,stroke-width:2px

    classDef writeStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef keyStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef adapterStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef tableStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px

    class W1,W2,W3,W4,W5 writeStyle
    class TK1,TK2,TK3 keyStyle
    class A1,A2,A3 adapterStyle
    class T1,T2,T3 tableStyle
```

---

## 🏛️ 3.7 Pydantic V2 as the Message Contract

**This is a governing clause. It applies to all four ports.**

Every message object crossing any port boundary is an `ACESBaseModel`
subclass. `ACESBaseModel` inherits from `pydantic.BaseModel` V2.
Pydantic V2 is therefore not an addition to the transport layer.
It is the message contract for all four ports **by constitutional
inheritance** — already true, now named and locked.

```mermaid
flowchart TD

    subgraph INHERITANCE ["🏛️    Constitutional    Inheritance    Chain"]
        PV2[pydantic.BaseModel V2\nField validation\nJSON schema generation\nmodel_dump support]
        ACES[ACESBaseModel\nInherits pydantic.BaseModel V2\nAdds trifecta serialization\nJSON YAML MD TOON\nConstitutional base — never bypass]
        MSG[McpRequest\nMcpResponse\nACESWorkspaceContext\nAll port messages\nAll registry records]
    end

    subgraph WHAT_V2_PROVIDES ["✅    What    Pydantic    V2    Provides    at    Every    Port"]
        V1[Validated at instantiation\nField validators fire\nBEFORE hexagon sees message\nPort is the validation gate]
        V2[Type coercion\nStr to int, dict to model\nAt the boundary\nnot in business logic]
        V3[Self-documenting\nmodel_json_schema produces\nport contract as\nmachine-readable artifact]
        V4[Two-value predicate logic\nNo NULLs permitted\nRequired fields must be present\nDefaults are governed]
    end

    subgraph WHERE_FIRES ["🎯    Where    Validation    Fires    —    Port    Sequence"]
        S1[Raw bytes arrive\nat TransportPort]
        S2[TransportAdapter.receive\ndeserializes bytes\nMcpRequest validated HERE]
        S3[ValidationError raised\nif malformed\nHexagon never sees it]
        S4[Valid McpRequest\npasses to hexagon\nBusiness logic runs clean]
    end

    PV2 --> ACES
    ACES --> MSG
    MSG --> V1
    MSG --> V2
    MSG --> V3
    MSG --> V4
    S1 --> S2
    S2 --> S3
    S2 --> S4

    style INHERITANCE fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style WHAT_V2_PROVIDES fill:#f0f8f0,stroke:#388e3c,stroke-width:2px
    style WHERE_FIRES fill:#e8f4fd,stroke:#1976d2,stroke-width:2px

    classDef inheritStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef provideStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef fireStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px

    class PV2,ACES,MSG inheritStyle
    class V1,V2,V3,V4 provideStyle
    class S1,S2,S3,S4 fireStyle
```

### 📐 The Trifecta on Port Messages

Because every port message inherits `ACESBaseModel`, every message
can be serialized in all four trifecta formats without additional code:

```python
request = McpRequest(
    tool_name="ingest_glossary",
    session_id="01966f2a-7b3e-7000-8000-000000000001",
    role="admin",
    fqsn_path="skills/task.d4.bgd",
    payload={"bgd_name": "electricity", "source_format": "json"}
)

# All four trifecta formats — zero additional code
request.model_dump_to_json()   # API payloads, MCP tool arguments
request.model_dump_to_yaml()   # Config files, human review
request.model_dump_to_md()     # Obsidian documentation, narrative
request.model_dump_to_toon()   # Diff-able tabular output, flat data

# Self-documenting port contract
schema = McpRequest.model_json_schema()
# Produces machine-readable contract — same object as the schema
```

---

## 🔧 3.8 Minimum Viable Product (MVP) Adapter Implementations

The MVP adapters prove all four port contracts before any
infrastructure is involved. They are trivial implementations.
Trivial is the point — the interface is proved, the business logic
is tested, and the infrastructure can be introduced incrementally.

```mermaid
flowchart LR

    subgraph MVP ["🟢    MVP    Adapters    —    Zero    Infrastructure"]

        subgraph TA ["🔌    StdioTransportAdapter"]
            TA1[receive: json.loads stdin bytes\nreturns McpRequest validated]
            TA2[send: json.dumps McpResponse\nwrites to stdout bytes]
            TA3[health: returns dict status healthy]
        end

        subgraph WA ["🗂️    InProcessWorkspaceAdapter"]
            WA1[open: stores context in dict\nreturns session_id]
            WA2[read: returns context from dict\nall roles]
            WA3[update: delta merged via operator.add\nadmin role only\nWORM audit appended]
            WA4[forward: completed_tasks.append\ncurrent_task_id updated\noperator.add]
            WA5[close: is_terminal=True\nfinal state preserved]
        end

        subgraph BA ["📨    InProcessBus"]
            BA1[publish: appends to dict queue\nreturns uuid message_id]
            BA2[consume: returns first unacked\nNone on empty queue]
            BA3[ack: adds message_id to acked set\nconsume skips acked]
        end

        subgraph RA ["🗄️    InProcessRegistryAdapter"]
            RA1[write_bgd: stores in dict\ncomputes BLAKE3 PairHash\nreturns PairHash]
            RA2[write_term: stores in dict\nthree-key architecture]
            RA3[disable: sets status DISABLED\nnever deletes]
            RA4[read: returns None if DISABLED\nall roles]
        end

    end

    subgraph PROD ["🔵    Production    Replacements    —    Zero    Hexagon    Changes"]
        PR1[HttpTransportAdapter\nADR-061]
        PR2[RayActorWorkspaceAdapter\nADR-062]
        PR3[RayObjectStoreBus\nADR-062]
        PR4[DuckDbRegistryAdapter\nPhase 1]
    end

    TA1 -.->|replaced by| PR1
    WA1 -.->|replaced by| PR2
    BA1 -.->|replaced by| PR3
    RA1 -.->|replaced by| PR4

    style MVP fill:#f0f8f0,stroke:#388e3c,stroke-width:2px
    style TA fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    style WA fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    style BA fill:#fff4e6,stroke:#f57c00,stroke-width:2px
    style RA fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style PROD fill:#e1f5fe,stroke:#0277bd,stroke-width:2px

    classDef taStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef waStyle fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef baStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef raStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef prodStyle fill:#e1f5fe,stroke:#0277bd,stroke-width:2px

    class TA1,TA2,TA3 taStyle
    class WA1,WA2,WA3,WA4,WA5 waStyle
    class BA1,BA2,BA3 baStyle
    class RA1,RA2,RA3,RA4 raStyle
    class PR1,PR2,PR3,PR4 prodStyle
```

---

## 📜 3.9 Port vs system.md — Interface vs Constitution

This distinction is the architectural insight that connects
Hexagonal Architecture to the Navigator/Driver model and to
Article 4 of the Navigator/Driver Medium series
(*Jurisdiction, Not Inheritance*).

**The port defines the shape.**
The `system.md` defines the authority.

In Cockburn's original framing:

> *"The port defines the shape of how the outside world talks
> to the application."*

In ACES terms:

> *"The `system.md` defines what the agent must be.
> The `TransportPort` defines how the outside world speaks to it."*

The `system.md` is not a port. It is the governing authority
*inside* the hexagon. The port is what the hexagon exposes.
The `system.md` governs what the hexagon is allowed to become
in response to anything that enters through the port.

```mermaid
flowchart TD

    subgraph PORT ["🔌    Port    —    The    Interface"]
        P1[Defines the SHAPE\nof inbound communication]
        P2[Syntactic contract\nWhat fields are required\nWhat types are expected]
        P3[Enforced by Pydantic V2\nat port boundary]
        P4[Technology-agnostic\nsame contract for HTTP\nstdio and Ray]
        P5[WORM — ports do not change\nwhen adapters change]
    end

    subgraph SYSMD ["📄    system.md    —    The    Constitution"]
        S1[Defines the AUTHORITY\ninside the hexagon]
        S2[Semantic contract\nWhat the agent must BE\nWhat it cannot become]
        S3[Enforced by the agent\nat reasoning time]
        S4[Session-agnostic\nsame contract for\nevery caller role]
        S5[WORM — mounted read-only\nas Kubernetes ConfigMap\nagent cannot modify it]
    end

    subgraph TOGETHER ["🏛️    Together    —    Complete    Governed    Agent"]
        T1[Port governs\nHOW the world speaks to the agent]
        T2[system.md governs\nWHAT the agent is allowed to become]
        T3[Neither substitutes for the other\nBoth are required\nNeither is sufficient alone]
        T4[An agent with a port but no system.md\nis untyped but ungoverned]
        T5[An agent with system.md but no port\nis governed but unreachable]
    end

    P1 --> T1
    P2 --> T1
    S1 --> T2
    S2 --> T2
    T1 --> T3
    T2 --> T3
    T3 --> T4
    T3 --> T5

    style PORT fill:#e8f4fd,stroke:#1976d2,stroke-width:2px
    style SYSMD fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style TOGETHER fill:#f0f8f0,stroke:#388e3c,stroke-width:3px

    classDef portStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef sysmdStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef togetherStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px

    class P1,P2,P3,P4,P5 portStyle
    class S1,S2,S3,S4,S5 sysmdStyle
    class T1,T2,T3,T4,T5 togetherStyle
```

> **The one sentence that ties it together:**
> The port tells the world how to talk to the agent.
> The `system.md` tells the agent what it cannot become
> regardless of what the world says.
> Together they are the complete governed agent.

---

## 🔄 3.10 Extensibility Guarantee

**Cockburn's original guarantee, applied to ACES:**

> *"Implement that shape as many times as needed."*

In operational terms: **zero modified files when a new adapter
is added.** The port contract is WORM. The adapters are governed
mutable. New infrastructure plugs into an existing port. Nothing
inside the hexagon changes.

```mermaid
flowchart LR

    subgraph TODAY ["📅    Today    —    MVP    Adapters"]
        T1[StdioTransportAdapter\nproves TransportPort]
        T2[InProcessWorkspaceAdapter\nproves ACESWorkspacePort]
        T3[InProcessBus\nproves MessageBusPort]
        T4[DuckDbRegistryAdapter\nproves RegistryPort]
    end

    subgraph PHASE2 ["🔵    Phase    2    —    Production    Adapters"]
        P1[HttpTransportAdapter\nADR-061\nzero hexagon changes]
        P2[RayActorWorkspaceAdapter\nADR-062\nzero hexagon changes]
        P3[RayObjectStoreBus\nADR-062\nzero hexagon changes]
        P4[PostgreSqlRegistryAdapter\nADR-065\nzero hexagon changes]
    end

    subgraph FUTURE ["🟡    Future    —    Any    Adapter"]
        F1[GrpcTransportAdapter\nzero hexagon changes]
        F2[RedisWorkspaceAdapter\nzero hexagon changes]
        F3[RabbitMqBus\nzero hexagon changes]
        F4[SnowflakeRegistryAdapter\nzero hexagon changes]
    end

    subgraph HEXAGON ["🔷    Hexagon    —    Never    Changes"]
        H1[BGD business logic\nidentical across\nall adapter generations]
    end

    T1 -->|replaced by| P1 -->|replaced by| F1
    T2 -->|replaced by| P2 -->|replaced by| F2
    T3 -->|replaced by| P3 -->|replaced by| F3
    T4 -->|replaced by| P4 -->|replaced by| F4

    H1 -.->|unchanged across all| T1
    H1 -.->|unchanged across all| P1
    H1 -.->|unchanged across all| F1

    style TODAY fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    style PHASE2 fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    style FUTURE fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    style HEXAGON fill:#f8f0ff,stroke:#7b1fa2,stroke-width:3px

    classDef todayStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef phase2Style fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef futureStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef hexStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px

    class T1,T2,T3,T4 todayStyle
    class P1,P2,P3,P4 phase2Style
    class F1,F2,F3,F4 futureStyle
    class H1 hexStyle
```

---

## 📋 3.11 Implementation Sequence

The implementation sequence is locked by the port contracts.
`src/ports.py` must exist before any adapter can be written.
No MCP server can be refactored until all four adapters it
depends on are implemented. No integration test can run until
at least the MVP adapters are in place.

```mermaid
flowchart TD

    subgraph STEP1 ["🥇    Step    1    —    Constitutional    Base"]
        S1A[src/base.py\nACESBaseModel\nfour trifecta serializers\nJSON YAML MD TOON]
    end

    subgraph STEP2 ["🥈    Step    2    —    Port    Contracts"]
        S2A[src/ports.py\nMcpRequest ACESBaseModel\nMcpResponse ACESBaseModel\nACESWorkspaceContext ACESBaseModel\nTransportPort ABC\nACESWorkspacePort ABC\nMessageBusPort ABC\nRegistryPort ABC]
    end

    subgraph STEP3 ["🥉    Step    3    —    MVP    Adapters"]
        S3A[src/adapters/transport/stdio.py\nStdioTransportAdapter]
        S3B[src/adapters/workspace/in_process.py\nInProcessWorkspaceAdapter]
        S3C[src/adapters/bus/in_process.py\nInProcessBus]
        S3D[src/adapters/registry/duckdb.py\nDuckDbRegistryAdapter]
    end

    subgraph STEP4 ["🏅    Step    4    —    MCP    Servers    Injected"]
        S4A[src/servers/bgd.py\nBGD hexagon\nfour ports injected\nno direct tech imports]
        S4B[src/servers/fqsn_registry.py\nFQSN Registry hexagon\nfour ports injected]
        S4C[src/servers/fqdn_governance.py\nFQDN Governance hexagon\nfour ports injected]
    end

    subgraph STEP5 ["🎯    Step    5    —    Production    Adapters"]
        S5A[src/adapters/transport/http.py\nHttpTransportAdapter\nADR-061]
        S5B[src/adapters/workspace/ray_actor.py\nRayActorWorkspaceAdapter\nADR-062]
        S5C[src/adapters/bus/ray_object_store.py\nRayObjectStoreBus\nADR-062]
    end

    S1A --> S2A
    S2A --> S3A
    S2A --> S3B
    S2A --> S3C
    S2A --> S3D
    S3A --> S4A
    S3B --> S4A
    S3C --> S4A
    S3D --> S4A
    S3A --> S4B
    S3B --> S4B
    S3C --> S4B
    S3D --> S4B
    S3A --> S4C
    S3B --> S4C
    S3C --> S4C
    S3D --> S4C
    S4A --> S5A
    S4A --> S5B
    S4A --> S5C

    style STEP1 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style STEP2 fill:#e8f4fd,stroke:#1976d2,stroke-width:2px
    style STEP3 fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    style STEP4 fill:#fff4e6,stroke:#f57c00,stroke-width:2px
    style STEP5 fill:#e1f5fe,stroke:#0277bd,stroke-width:2px

    classDef step1Style fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    classDef step2Style fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef step3Style fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef step4Style fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef step5Style fill:#e1f5fe,stroke:#0277bd,stroke-width:2px

    class S1A step1Style
    class S2A step2Style
    class S3A,S3B,S3C,S3D step3Style
    class S4A,S4B,S4C step4Style
    class S5A,S5B,S5C step5Style
```

### 📐 File Creation Checklist

| Step | File | Depends On | Blocks |
|------|------|-----------|--------|
| 1 | `src/base.py` | nothing | everything |
| 2 | `src/ports.py` | `src/base.py` | all adapters |
| 3a | `src/adapters/transport/stdio.py` | `src/ports.py` | MCP servers |
| 3b | `src/adapters/workspace/in_process.py` | `src/ports.py` | MCP servers |
| 3c | `src/adapters/bus/in_process.py` | `src/ports.py` | MCP servers |
| 3d | `src/adapters/registry/duckdb.py` | `src/ports.py` | MCP servers |
| 4a | `src/servers/bgd.py` | all four adapters | integration tests |
| 4b | `src/servers/fqsn_registry.py` | all four adapters | integration tests |
| 4c | `src/servers/fqdn_governance.py` | all four adapters | integration tests |
| 5a | `src/adapters/transport/http.py` | ADR-061 filed | K8s deployment |
| 5b | `src/adapters/workspace/ray_actor.py` | ADR-062 filed | Ray cluster |
| 5c | `src/adapters/bus/ray_object_store.py` | ADR-062 filed | Ray cluster |

---

[🔝 Back to Section 3 TOC](#-section-3-table-of-contents)

[🏠 Back to Main TOC](./docs-section-1-overview-architecture.md#-table-of-contents)

---

*Section 3 of 6 — Continue, but append to a separate section from where
you left off to avoid duplication and corruption.*
