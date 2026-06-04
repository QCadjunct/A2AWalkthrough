# ⚡ Section 4 — Agentic Distribution Framework (ADF) and Ray

> **Continue, but append to a separate section from where you left off
> to avoid duplication and corruption.**
>
> This section is autonomous and self-contained.
> It covers the ADF execution layer and Ray cluster architecture
> exclusively. It does not duplicate content from Sections 1–3
> or Sections 5–6 (forthcoming).

---

## 📋 Section 4 Table of Contents

- [4.1 What the ADF Is — and What It Is Not](#-41-what-the-adf-is--and-what-it-is-not)
- [4.2 The Three-Layer Responsibility Boundary](#-42-the-three-layer-responsibility-boundary)
- [4.3 Ray Cluster Topology](#-43-ray-cluster-topology)
- [4.4 ACES Primitive to Ray Primitive Mapping](#-44-aces-primitive-to-ray-primitive-mapping)
- [4.5 GroupTaskManifest — The WORM Decomposition Document](#-45-grouptaskmanifest--the-worm-decomposition-document)
- [4.6 FailurePolicy — Eliminating Ambiguity](#-46-failurepolicy--eliminating-ambiguity)
- [4.7 AdfExecutor — The Group Task Orchestrator](#-47-adfexecutor--the-group-task-orchestrator)
- [4.8 Ray Actors — Stateful Singleton Agents](#-48-ray-actors--stateful-singleton-agents)
- [4.9 Ray Tasks — Parallel BGD Ingest Workers](#-49-ray-tasks--parallel-bgd-ingest-workers)
- [4.10 Ray Serve — MCP HTTP Transport](#-410-ray-serve--mcp-http-transport)
- [4.11 Node Affinity and Work Routing](#-411-node-affinity-and-work-routing)
- [4.12 The EIA Full Ingest Group Task End-to-End](#-412-the-eia-full-ingest-group-task-end-to-end)

---

## 🎯 4.1 What the ADF Is — and What It Is Not

**ADF — Agentic Distribution Framework** is the execution layer
that sits between the Task Group coordinator (Kubernetes) and
the inference substrate (MaaS). It answers four questions that
neither K8s nor MaaS can answer:

1. **How is a Group Task decomposed into subtasks?**
   K8s schedules Pods to nodes. It does not know what work
   a Pod should do or in what order.

2. **Which cluster node executes which subtask?**
   K8s node affinity applies to Pods at deployment time.
   ADF node affinity applies to work units at runtime —
   based on FQSN, data locality, and task dependencies.

3. **How do partial results aggregate into a governed output?**
   K8s has no concept of aggregation. The ADF defines the
   aggregation contract via `GroupTaskManifest`.

4. **What happens when a subtask fails?**
   K8s restarts Pods. The ADF enforces `FailurePolicy` —
   `CONTINUE_PARTIAL`, `WAIT_RETRY`, or `ABORT` — per
   manifest specification.

**What ADF is NOT:**

| Confusion | Clarification |
|-----------|--------------|
| ADF is not MaaS | MaaS serves LLM inference. ADF distributes work. They are different layers. |
| ADF is not K8s | K8s schedules Pods. ADF schedules work units. Both are required. |
| ADF is not a message queue | RabbitMQ routes messages. ADF governs work decomposition and aggregation. |
| ADF is not an agent framework | LangGraph, CrewAI orchestrate agents inside a process. ADF distributes across a cluster. |

**Ray is the correct ADF substrate** because Ray Tasks map directly
to ACES Tasks, Ray Actors map to stateful singleton agents, Ray DAGs
are the Group Task execution engine, and Ray Serve provides the HTTP
transport layer — fulfilling ADR-064 in the same implementation that
fulfills ADR-062.

---

## 🏛️ 4.2 The Three-Layer Responsibility Boundary

Each layer owns exactly one concern. No layer reaches into another.

```mermaid
flowchart TD

    subgraph L3 ["☸️    Layer    3    —    Task    Group    Coordinator"]
        K1[Kubernetes Namespace\nd4-database-design]
        K2[Pod lifecycle\nstartup sequence\nhealth gating]
        K3[Swim lane isolation\nNetworkPolicy]
        K4[Replica scaling\nHPA maxReplicas 7]
        K5[WORM contract mount\nConfigMap read-only]
    end

    subgraph L2 ["⚡    Layer    2    —    ADF    Execution    Engine"]
        R1[Ray Cluster\nFreedomTower head\nTheBeast MiniBeast Teacher workers]
        R2[Work decomposition\nGroupTaskManifest\nSubTaskSpec DAG]
        R3[Node assignment\nNodeAffinity per subtask\nnot per Pod]
        R4[Parallel execution\nRay Tasks fired simultaneously\nseven BGD workers]
        R5[Aggregation contract\nray.get blocks at DAG gate\ncross-domain overlap]
        R6[Failure policy\nCONTINUE_PARTIAL\nWAIT_RETRY\nABORT]
    end

    subgraph L1 ["🤖    Layer    1    —    Inference    Substrate"]
        M1[MaaS endpoints\nTheBeast dual RTX 5090\nMiniBeast dual RTX 4090]
        M2[LLM model serving\nGPU allocation\ninference scaling]
        M3[No agent orchestration\nno work routing\nno task governance]
    end

    subgraph BOUNDARY ["🚧    Boundary    Rules    —    Non-Negotiable"]
        B1[K8s schedules Pods to nodes\nADF schedules work units to agents\nDifferent levels — both required]
        B2[ADF uses Ray object store\nfor intra-cluster messaging\nRabbitMQ for external only]
        B3[MaaS receives inference requests\nfrom Ray workers\nnot from K8s directly]
    end

    K1 --> R1
    R1 --> M1
    K2 -.->|does NOT govern| R2
    R2 -.->|does NOT govern| M2
    K3 -.->|does NOT govern| R3
    B1 --> K1
    B1 --> R1
    B2 --> R5
    B3 --> M1

    style L3 fill:#e8eaf6,stroke:#3f51b5,stroke-width:3px
    style L2 fill:#f0f8f0,stroke:#388e3c,stroke-width:3px
    style L1 fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    style BOUNDARY fill:#fff4e6,stroke:#f57c00,stroke-width:2px

    classDef k8sStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef rayStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef maasStyle fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef boundaryStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px

    class K1,K2,K3,K4,K5 k8sStyle
    class R1,R2,R3,R4,R5,R6 rayStyle
    class M1,M2,M3 maasStyle
    class B1,B2,B3 boundaryStyle
```

---

## 🖥️ 4.3 Ray Cluster Topology

The Ray cluster runs on existing FreedomTower cluster hardware
over Tailscale mesh. No new infrastructure required for Phase 1.

```mermaid
flowchart LR

    subgraph TAILSCALE ["🔒    Tailscale    Mesh    Network"]

        subgraph HEAD ["🖥️    FreedomTower    —    Ray    Head    Node"]
            FT1[RTX 5080\nWSL2 Ubuntu\nRay head process]
            FT2[FqsnRegistryActor\nnamed singleton\nalways-on]
            FT3[BgdRegistryActor\nDuckDB writer\npersistent]
            FT4[AdfExecutor\nGroupTaskManifest\norchestrator]
        end

        subgraph BEAST ["⚡    TheBeast    —    Worker    Node    A"]
            TB1[Dual RTX 5090\nGPU_HIGH affinity\nMaaS inference]
            TB2[bgd-worker-2\nbgd-worker-3\nRay Tasks]
        end

        subgraph MINI ["💪    MiniBeast    —    Worker    Node    B"]
            MB1[Dual RTX 4090\nGPU_HIGH affinity\nMaaS inference]
            MB2[bgd-worker-4\nbgd-worker-5\nRay Tasks]
        end

        subgraph TEACH ["🎓    Teacher    —    Worker    Node    C"]
            TC1[GTX 1060\nCPU_ANY affinity\nlightweight tasks]
            TC2[bgd-worker-6\nbgd-worker-7\nRay Tasks]
        end

        subgraph NAS ["💾    Synology    DS920+"]
            SY1[NFS PersistentVolume\nDuckDB registry files\nobsidian vault storage]
        end

    end

    FT3 --> SY1
    FT2 --> TB2
    FT2 --> MB2
    FT2 --> TC2
    FT4 --> TB2
    FT4 --> MB2
    FT4 --> TC2

    style TAILSCALE fill:#e8f4fd,stroke:#1976d2,stroke-width:2px
    style HEAD fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style BEAST fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style MINI fill:#fff4e6,stroke:#f57c00,stroke-width:2px
    style TEACH fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    style NAS fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px

    classDef headStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef beastStyle fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef miniStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef teachStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef nasStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px

    class FT1,FT2,FT3,FT4 headStyle
    class TB1,TB2 beastStyle
    class MB1,MB2 miniStyle
    class TC1,TC2 teachStyle
    class SY1 nasStyle
```

### 📐 Ray Bootstrap Commands

```bash
# On FreedomTower — start Ray head node
ray start --head \
  --port=6379 \
  --dashboard-host=0.0.0.0 \
  --dashboard-port=8265

# On TheBeast — connect as worker
ray start --address='freedomtower:6379' \
  --num-gpus=2 \
  --num-cpus=32

# On MiniBeast — connect as worker
ray start --address='freedomtower:6379' \
  --num-gpus=2 \
  --num-cpus=16

# On Teacher — connect as worker
ray start --address='freedomtower:6379' \
  --num-gpus=1 \
  --num-cpus=8

# Verify cluster
ray status

# Initialize in Python
import ray
ray.init(address="ray://freedomtower:10001")
```

---

## 🗺️ 4.4 ACES Primitive to Ray Primitive Mapping

Every ACES architectural concept maps to a specific Ray primitive.
This is not a translation layer — it is a direct correspondence
that makes Ray the natural ADF substrate.

```mermaid
flowchart LR

    subgraph ACES ["🔷    ACES    Primitives"]
        A1[Task\nStateless execution unit\ngoverned by FQSN\nreturns governed output]
        A2[Stateful Agent\nPersistent state\nnamed singleton\naddressable]
        A3[Group Task\nDAG of subtasks\nwith dependencies\nand aggregation]
        A4[ADF Manifest\nGroupTaskManifest\nACESBaseModel WORM]
        A5[FQSN Registry\nSingleton\nalways-on\ngoverned mutable]
        A6[BGD Registry\nSingleton\nDuckDB writer\npersistent]
        A7[MCP server endpoint\nHTTP transport\nADR-064]
    end

    subgraph RAY ["⚡    Ray    Primitives"]
        R1[ray.remote function\nstateless\nparallelizable\nmax_retries governed]
        R2[ray.remote class\nActor\nnamed handle\nray.get_actor]
        R3[ray.dag\nDAG topology\nray.get blocks\nat dependency gates]
        R4[GroupTaskManifest\nloaded by AdfExecutor\nnot modified at runtime]
        R5[FqsnRegistryActor\nray.remote class\nnamed fqsn-registry-singleton]
        R6[BgdRegistryActor\nray.remote class\nDuckDB connection\npersistent across tasks]
        R7[Ray Serve deployment\nHTTP endpoint\nnum_replicas governed\nby HPA]
    end

    A1 -->|maps to| R1
    A2 -->|maps to| R2
    A3 -->|maps to| R3
    A4 -->|maps to| R4
    A5 -->|maps to| R5
    A6 -->|maps to| R6
    A7 -->|maps to| R7

    style ACES fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style RAY fill:#f0f8f0,stroke:#388e3c,stroke-width:2px

    classDef acesStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef rayStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px

    class A1,A2,A3,A4,A5,A6,A7 acesStyle
    class R1,R2,R3,R4,R5,R6,R7 rayStyle
```

---

## 📋 4.5 GroupTaskManifest — The WORM Decomposition Document

The `GroupTaskManifest` is the most important artifact in the ADF
layer. It is written once per Group Task design. Execution instances
carry their own `session_id` and audit trail but do not modify the
manifest.

> **The manifest is the constitution of the Group Task.
> Execution instances are citizens bound by it.**

This sentence connects directly to Article 4 of the Navigator/Driver
series (*Jurisdiction, Not Inheritance*) — the manifest governs
by jurisdiction, not by inheritance. Every subtask is a citizen
bound by the manifest. No subtask can override the manifest's
failure policy, node affinity, or aggregation contract.

```mermaid
flowchart TD

    subgraph MANIFEST ["📋    GroupTaskManifest    —    ACESBaseModel    WORM"]

        subgraph META ["📌    Manifest    Metadata"]
            M1[manifest_id: UUIDv7\nManifest identity]
            M2[manifest_version: str\n1.0.0 — SemVer]
            M3[task_group: str\ntask-group.d4-database-design]
            M4[group_task_name: str\neia-full-glossary-ingest]
            M5[failure_policy: FailurePolicy\nWAIT_RETRY default]
            M6[authored_at: str\nISO-8601 timestamp]
            M7[authored_by: str\nPeter Heller]
        end

        subgraph SUBTASKS ["🔲    SubTaskSpec    —    One    per    ACES    Task"]
            ST1[task_id: str\nUnique within manifest\ningest-electricity]
            ST2[fqsn_path: str\nskills/task.d4.bgd]
            ST3[node_affinity: NodeAffinity\nCPU_ANY or GPU_HIGH]
            ST4[depends_on: list of str\ntask_ids that must complete first\nempty = parallel]
            ST5[max_retries: int\n0 to 10\ndefault 3]
            ST6[timeout_seconds: int\n30 to 3600\ndefault 300]
            ST7[input_schema: str\nACESBaseModel class name]
            ST8[output_schema: str\nACESBaseModel class name]
        end

        subgraph AGG ["🔗    AggregationSpec    —    One    per    Manifest"]
            AG1[aggregator_fqsn: str\nFQSN of aggregation agent]
            AG2[wait_for_all: bool\nTrue — gate until all complete\nFalse — CONTINUE_PARTIAL]
            AG3[output_schema: str\nEiaFullIngestResult]
            AG4[dedup_field: str optional\nterm_text for overlap dedup]
        end

    end

    subgraph WORM_RULE ["🔒    WORM    Rule    —    Manifest    Immutability"]
        W1[Manifest written ONCE\nby Navigator at design time]
        W2[AdfExecutor reads manifest\nNEVER modifies it]
        W3[Execution instances carry\nown session_id and audit trail]
        W4[Manifest version locked\nNew design = new manifest_id]
    end

    M1 --> ST1
    M5 --> ST3
    ST4 --> AG2
    AG2 --> AG3
    W1 --> W2
    W2 --> W3

    style MANIFEST fill:#f8f0ff,stroke:#7b1fa2,stroke-width:3px
    style META fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style SUBTASKS fill:#e8f4fd,stroke:#1976d2,stroke-width:2px
    style AGG fill:#f0f8f0,stroke:#388e3c,stroke-width:2px
    style WORM_RULE fill:#e0f2f1,stroke:#00695c,stroke-width:2px

    classDef metaStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef subtaskStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef aggStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef wormStyle fill:#e0f2f1,stroke:#00695c,stroke-width:2px

    class M1,M2,M3,M4,M5,M6,M7 metaStyle
    class ST1,ST2,ST3,ST4,ST5,ST6,ST7,ST8 subtaskStyle
    class AG1,AG2,AG3,AG4 aggStyle
    class W1,W2,W3,W4 wormStyle
```

### 🔬 GroupTaskManifest Python Implementation

```python
from enum import Enum
from typing import Optional
from src.base import ACESBaseModel
from pydantic import Field


class FailurePolicy(str, Enum):
    """
    ADF failure policy — three governed states, no ambiguity.
    No NULL-equivalent fallback. No undeclared behavior.
    """
    CONTINUE_PARTIAL = "CONTINUE_PARTIAL"  # run on, aggregate available
    WAIT_RETRY       = "WAIT_RETRY"        # retry N times, others wait
    ABORT            = "ABORT"             # any failure cancels all


class NodeAffinity(str, Enum):
    """
    Work unit routing — per subtask, not per Pod.
    K8s node affinity applies to Pods at deployment time.
    ADF node affinity applies to work units at runtime.
    """
    CPU_ANY   = "CPU_ANY"    # any node — BGD ingest, metadata
    GPU_HIGH  = "GPU_HIGH"   # TheBeast or MiniBeast — LLM inference
    GPU_LOW   = "GPU_LOW"    # Teacher — lightweight inference
    HEAD_ONLY = "HEAD_ONLY"  # FreedomTower — coordinator tasks


class SubTaskSpec(ACESBaseModel):
    """One subtask within a Group Task — governed by ACESBaseModel."""
    task_id:         str
    fqsn_path:       str
    node_affinity:   NodeAffinity = NodeAffinity.CPU_ANY
    depends_on:      list[str]    = Field(default_factory=list)
    max_retries:     int          = Field(default=3, ge=0, le=10)
    timeout_seconds: int          = Field(default=300, ge=30, le=3600)
    input_schema:    str          = "GlossaryIngestionRequest"
    output_schema:   str          = "BgdManifest"


class AggregationSpec(ACESBaseModel):
    """Aggregation contract — how N parallel results merge."""
    aggregator_fqsn: str
    wait_for_all:    bool          = True
    output_schema:   str           = "EiaFullIngestResult"
    dedup_field:     Optional[str] = None


class GroupTaskManifest(ACESBaseModel):
    """
    WORM decomposition document — the constitution of the Group Task.
    Written once. Read many times. Never modified at runtime.
    Execution instances are citizens bound by it.
    """
    manifest_id:      str
    manifest_version: str               = "1.0.0"
    task_group:       str               = "task-group.d4-database-design"
    group_task_name:  str
    description:      str
    failure_policy:   FailurePolicy     = FailurePolicy.WAIT_RETRY
    subtasks:         list[SubTaskSpec] = Field(..., min_length=2)
    aggregation:      AggregationSpec
    authored_at:      str
    authored_by:      str               = "Peter Heller"
```

---

## 🚦 4.6 FailurePolicy — Eliminating Ambiguity

`FailurePolicy` is a governed enum — three states, no NULL,
no undeclared behavior. Every `GroupTaskManifest` declares
exactly one. The ADF enforces it without interpretation.

```mermaid
flowchart TD

    subgraph FP ["🚦    FailurePolicy    —    Three    Governed    States"]

        subgraph CP ["🟡    CONTINUE_PARTIAL"]
            CP1[Subtask fails]
            CP2[Remaining subtasks continue\nrunning on other nodes]
            CP3[Aggregation runs on\navailable results only]
            CP4[Failure recorded in\nmanifest audit trail]
            CP5[Use case: best-effort ingest\nacceptable partial BGD]
        end

        subgraph WR ["🟠    WAIT_RETRY"]
            WR1[Subtask fails]
            WR2[Retry up to max_retries\ndefault 3 attempts]
            WR3[Other subtasks wait\nat aggregation boundary]
            WR4[After max retries\naggregation gate escalates]
            WR5[Use case: EIA BGD ingest\nall 7 fuel groups required]
        end

        subgraph AB ["🔴    ABORT"]
            AB1[Any subtask fails]
            AB2[All in-flight tasks cancelled\nray.cancel on all refs]
            AB3[No aggregation executed]
            AB4[Session closed immediately]
            AB5[Use case: atomic operations\nall-or-nothing requirement]
        end

    end

    subgraph DEFAULT ["✅    Default    is    WAIT_RETRY"]
        D1[WAIT_RETRY is the most governed choice\nfor BGD ingest operations]
        D2[Seven parallel ingest tasks\nall seven required for\ncross-domain overlap]
        D3[Three retries before\naggregation gate escalates]
    end

    CP1 --> CP2 --> CP3 --> CP4 --> CP5
    WR1 --> WR2 --> WR3 --> WR4 --> WR5
    AB1 --> AB2 --> AB3 --> AB4 --> AB5
    WR5 --> D1
    D1 --> D2
    D2 --> D3

    style FP fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style CP fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    style WR fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style AB fill:#ffebee,stroke:#b71c1c,stroke-width:2px
    style DEFAULT fill:#e8f5e8,stroke:#388e3c,stroke-width:2px

    classDef cpStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef wrStyle fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef abStyle fill:#ffebee,stroke:#b71c1c,stroke-width:2px
    classDef defaultStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px

    class CP1,CP2,CP3,CP4,CP5 cpStyle
    class WR1,WR2,WR3,WR4,WR5 wrStyle
    class AB1,AB2,AB3,AB4,AB5 abStyle
    class D1,D2,D3 defaultStyle
```

---

## 🎯 4.7 AdfExecutor — The Group Task Orchestrator

`AdfExecutor` is the class that reads `GroupTaskManifest` and
dispatches Ray Tasks accordingly. It owns the dependency ordering,
failure policy enforcement, and aggregation contract. It does not
own the business logic — that lives in the hexagons.

```mermaid
sequenceDiagram
    participant Nav as Navigator
    participant Exec as AdfExecutor
    participant Reg as FqsnRegistryActor
    participant W1 as bgd-worker-1\nRay Task
    participant W7 as bgd-worker-7\nRay Task
    participant Agg as overlap-task\nRay Task
    participant WP as ACESWorkspacePort
    participant DB as DuckDB Registry

    Note over Nav,DB: AdfExecutor — Group Task Execution Flow

    Nav->>Exec: execute(session_id)\nGroupTaskManifest loaded\nFailurePolicy WAIT_RETRY

    Exec->>WP: read(session_id)
    WP-->>Exec: ACESWorkspaceContext

    Note over Exec,W7: Phase 1 — Parallel dispatch\nAll subtasks with empty DependsOn fired simultaneously

    Exec->>Reg: resolve(skills/task.d4.bgd)
    Reg-->>Exec: fqsn_record governed

    Exec->>WP: forward(session_id, ingest-electricity)
    WP-->>Exec: context updated operator.add

    Exec->>W1: ingest_bgd_task.remote\nelectricity payload\nfqsn_registry handle
    Exec->>W7: ingest_bgd_task.remote\nalternative-fuels payload\nfqsn_registry handle

    Note over W1,W7: Workers run in parallel across cluster\nFreedomTower TheBeast MiniBeast Teacher

    W1->>Reg: resolve(skills/task.d4.bgd)\ngate check before work
    Reg-->>W1: governed
    W1-->>Exec: BgdManifest ref electricity

    W7-->>Exec: BgdManifest ref alternative-fuels

    Exec->>WP: update(session_id,\nlast_completed ingest-electricity,\nadmin role)

    Note over Exec,Agg: Phase 2 — Aggregation gate\nray.get blocks until ALL 7 refs resolved

    Exec->>Agg: compute_overlap_task.remote\nall 7 manifest refs\nfqsn_registry handle

    Agg->>Agg: ray.get all 7 refs\nmaterialize BGD manifests\ncompute cross-domain overlap\nBTU maps to Energy.ThermalUnit

    Agg->>DB: RegistryPort.write_overlap\nBLAKE3 PairHash\nadmin role
    DB-->>Agg: PairHash confirmed

    Agg-->>Exec: CrossDomainOverlapResult ref

    Note over Exec,DB: Phase 3 — Promotion

    Exec->>DB: RegistryPort.write_term\nEnergy.ThermalUnit\nBLAKE3 PairHash
    DB-->>Exec: PairHash confirmed

    Exec->>WP: close(session_id, admin)
    WP-->>Exec: ACESWorkspaceContext is_terminal True

    Exec-->>Nav: EiaFullIngestResult\n7 BGDs ingested\nOverlap computed\nUniversal domains promoted
```

---

## 🎭 4.8 Ray Actors — Stateful Singleton Agents

Ray Actors are the Ray primitive for stateful singleton agents.
They are instantiated once, named, and addressable across all
cluster nodes. The `FqsnRegistryActor` and `BgdRegistryActor`
are the two singleton actors in this Task Group.

```mermaid
flowchart TD

    subgraph ACTORS ["🎭    Ray    Actors    —    Stateful    Singletons"]

        subgraph FQSN_ACT ["🔑    FqsnRegistryActor"]
            FA1[Named: fqsn-registry-singleton\nAddressable from any node\nAlways-on — never shut down]
            FA2[resolve: returns fqsn_record or None\nAll roles read]
            FA3[register: adds new FQSN\nAdmin role only]
            FA4[disable: sets status DISABLED\nAdmin role only\nNever deletes]
            FA5[health: returns status dict\nreadinessProbe target]
        end

        subgraph BGD_ACT ["💾    BgdRegistryActor"]
            BA1[Named: bgd-registry-singleton\nDuckDB connection persistent\nSynology NAS mount]
            BA2[write: governed record\nthree-key architecture\nBLAKE3 PairHash]
            BA3[disable: by PairHash\nAdmin role only\nNever deletes]
            BA4[read: by PairHash\nAll roles\nNone if disabled]
        end

    end

    subgraph LIFECYCLE ["♻️    Actor    Lifecycle"]
        L1[Created once at cluster start\nray.remote class instantiation]
        L2[Named handle registered\nray.get_actor accessible\nfrom any Ray Task]
        L3[State persists across\nall Task Group executions\nacross all sessions]
        L4[Restart policy: always\nK8s Pod restart triggers\nRay Actor re-registration]
    end

    subgraph PATTERN ["🔬    Usage    Pattern"]
        P1[registry = ray.get_actor\nname fqsn-registry-singleton]
        P2[result = ray.get\nregistry.resolve.remote\nfqsn_path]
        P3[FQSN gate check in\nevery Ray Task\nbefore any work executes]
    end

    FA1 --> L1
    BA1 --> L1
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L2 --> P1
    P1 --> P2
    P2 --> P3

    style ACTORS fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style FQSN_ACT fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style BGD_ACT fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style LIFECYCLE fill:#f0f8f0,stroke:#388e3c,stroke-width:2px
    style PATTERN fill:#fff4e6,stroke:#f57c00,stroke-width:2px

    classDef fqsnStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef bgdStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef lifecycleStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef patternStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px

    class FA1,FA2,FA3,FA4,FA5 fqsnStyle
    class BA1,BA2,BA3,BA4 bgdStyle
    class L1,L2,L3,L4 lifecycleStyle
    class P1,P2,P3 patternStyle
```

### 🔬 Ray Actor Implementation Skeleton

```python
import ray
from src.base import ACESBaseModel


@ray.remote(num_cpus=0.5)
class FqsnRegistryActor:
    """
    Singleton FQSN registry — governed mutable.
    Named and addressable across all cluster nodes.
    Admin: read/update/disable.
    Agent/Client: read only.
    No hard deletes — disable is the governance primitive.
    """

    def __init__(self):
        self._registry: dict[str, dict] = {}

    def resolve(self, fqsn_path: str) -> dict | None:
        record = self._registry.get(fqsn_path)
        if record and record.get("status") == "DISABLED":
            return None
        return record

    def register(self, fqsn_path: str,
                 record: dict, role: str) -> bool:
        if role != "admin":
            raise PermissionError("Registration requires admin role")
        self._registry[fqsn_path] = record
        return True

    def disable(self, fqsn_path: str, role: str) -> bool:
        if role != "admin":
            raise PermissionError("Disable requires admin role")
        if fqsn_path in self._registry:
            self._registry[fqsn_path]["status"] = "DISABLED"
            return True
        return False

    def health(self) -> dict:
        return {
            "status":           "healthy",
            "registered_count": len(self._registry),
            "disabled_count":   sum(
                1 for r in self._registry.values()
                if r.get("status") == "DISABLED"
            )
        }


# Instantiate as named singleton on cluster start
fqsn_registry = FqsnRegistryActor.options(
    name="fqsn-registry-singleton",
    lifetime="detached",        # survives driver restart
    get_if_exists=True          # idempotent — reuses existing actor
).remote()
```

---

## ⚙️ 4.9 Ray Tasks — Parallel BGD Ingest Workers

Ray Tasks are stateless, parallelizable execution units. They
map directly to ACES Tasks. Seven Ray Tasks fire simultaneously —
one per EIA fuel group — each governed by the same FQSN.

```mermaid
flowchart LR

    subgraph DISPATCH ["🚀    Parallel    Dispatch    —    Seven    Tasks    Simultaneous"]
        D1[AdfExecutor\nfires all 7\nsimultaneously]
    end

    subgraph WORKERS ["⚙️    Ray    Tasks    —    BGD    Ingest    Workers"]
        W1[bgd-worker-1\nelectricity\nFreedomTower\nCPU_ANY]
        W2[bgd-worker-2\ncoal\nTheBeast\nCPU_ANY]
        W3[bgd-worker-3\nnatural-gas\nTheBeast\nCPU_ANY]
        W4[bgd-worker-4\nnuclear\nMiniBeast\nCPU_ANY]
        W5[bgd-worker-5\npetroleum\nMiniBeast\nCPU_ANY]
        W6[bgd-worker-6\nrenewable\nTeacher\nCPU_ANY]
        W7[bgd-worker-7\nalternative-fuels\nTeacher\nCPU_ANY]
    end

    subgraph PIPELINE ["🔄    Each    Worker    Runs    Governed    Pipeline"]
        P1[FQSN gate check\nresolve before any work\nungoverned = reject]
        P2[Harvest\nsource URL\nPlaywright or file]
        P3[Parse\nterm-definition pairs\nGlossaryIngestionRequest]
        P4[Govern\nD4 taxonomy\nBLAKE3 PairHash\nCHECK constraints]
        P5[Write\nBGD.Registry\nBGD.Term\nDuckDB via Actor]
        P6[Return\nBgdManifest\nRay object ref]
    end

    subgraph GATE ["🔗    Aggregation    Gate    —    ray.get    All    7"]
        G1[compute_overlap_task\nDependsOn all 7\nBlocks until all refs ready]
    end

    D1 --> W1 & W2 & W3 & W4 & W5 & W6 & W7
    W1 --> P1
    P1 --> P2 --> P3 --> P4 --> P5 --> P6
    W1 & W2 & W3 & W4 & W5 & W6 & W7 --> G1

    style DISPATCH fill:#e8f4fd,stroke:#1976d2,stroke-width:2px
    style WORKERS fill:#f0f8f0,stroke:#388e3c,stroke-width:2px
    style PIPELINE fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style GATE fill:#fff4e6,stroke:#f57c00,stroke-width:3px

    classDef workerStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef pipelineStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef gateStyle fill:#fff8e1,stroke:#f57c00,stroke-width:3px

    class W1,W2,W3,W4,W5,W6,W7 workerStyle
    class P1,P2,P3,P4,P5,P6 pipelineStyle
    class G1 gateStyle
```

### 🔬 Ray Task Implementation Skeleton

```python
import ray
from src.harvester import harvest
from src.parser import parse
from src.governer import govern
from src.base import ACESBaseModel


@ray.remote(num_cpus=1)
def ingest_bgd_task(
    glossary_request: dict,
    fqsn_registry: ray.actor.ActorHandle
) -> dict:
    """
    Stateless BGD ingest task — one per fuel group.
    Resolves FQSN before executing — ungoverned calls rejected.
    Returns BgdManifest as dict for Ray object store.
    Governance rule: FQSN gate check is always first.
    No exceptions. No shortcuts.
    """
    # Gate check — ungoverned calls rejected before any work
    fqsn_path = "skills/task.d4-database-design.bgd"
    fqsn_record = ray.get(fqsn_registry.resolve.remote(fqsn_path))

    if fqsn_record is None:
        raise RuntimeError(
            f"Ungoverned call rejected — FQSN not resolvable: {fqsn_path}"
        )

    # Governed pipeline — four stages
    raw     = harvest(glossary_request["source_url"],
                      glossary_request["source_format"])
    parsed  = parse(raw)
    governed_manifest = govern(parsed, glossary_request["bgd_name"])

    # Write to registry via Actor — not directly to DuckDB
    bgd_actor = ray.get_actor("bgd-registry-singleton")
    ray.get(bgd_actor.write.remote(governed_manifest.model_dump(),
                                   role="admin"))

    return governed_manifest.model_dump()
```

---

## 🌐 4.10 Ray Serve — MCP HTTP Transport

Ray Serve is the HTTP endpoint layer for all three MCP servers.
It fulfills the ADR-064 HTTP transport prerequisite within the
same implementation that fulfills ADR-062. One implementation,
two ADRs satisfied.

```mermaid
sequenceDiagram
    participant Client as HTTP Client\nor K8s Pod
    participant Serve as Ray Serve\nBgdMcpServer
    participant Adapter as HttpTransportAdapter\nADR-064
    participant Hexagon as BGD Hexagon\nbusiness logic
    participant Reg as FqsnRegistryActor\nsingleton

    Note over Client,Reg: Ray Serve — HTTP Transport Flow

    Client->>Serve: POST /tools/ingest_glossary\nJSON body McpRequest

    Note over Serve: Ray Serve routes to\navailable replica\nload balanced

    Serve->>Adapter: raw bytes
    Adapter->>Adapter: McpRequest validated\nPydantic V2 fires here\nValidationError if malformed

    Adapter->>Reg: resolve(fqsn_path)\nFQSN gate check
    Reg-->>Adapter: fqsn_record or None

    alt FQSN not resolvable
        Adapter-->>Client: McpResponse status=rejected\nerror_msg=Ungoverned call
    else FQSN resolved — governed
        Adapter->>Hexagon: McpRequest validated
        Hexagon->>Hexagon: ingest_glossary\nbusiness logic runs clean
        Hexagon-->>Adapter: McpResponse status=ok
        Adapter-->>Serve: bytes
        Serve-->>Client: HTTP 200\nJSON McpResponse
    end

    Note over Client,Reg: health check — readinessProbe target
    Client->>Serve: GET /health
    Serve-->>Client: HTTP 200\nstatus healthy transport http
```

### 🔬 Ray Serve Deployment

```python
from ray import serve
from src.ports import TransportPort, McpRequest, McpResponse
from src.adapters.transport.http import HttpTransportAdapter
from src.adapters.workspace.ray_actor import RayActorWorkspaceAdapter
from src.adapters.bus.ray_object_store import RayObjectStoreBus
from src.adapters.registry.duckdb import DuckDbRegistryAdapter


@serve.deployment(
    name="bgd-mcp-server",
    num_replicas=3,              # matches HPA minReplicas in ADR-061
    ray_actor_options={"num_cpus": 1}
)
class BgdMcpServer:
    """
    BGD MCP server as Ray Serve deployment.
    HTTP transport — fulfills ADR-064 prerequisite.
    Four ports injected — fulfills ADR-063 hexagonal pattern.
    Each replica is a stateless hexagon. Actors are shared.
    """

    def __init__(self):
        # Four ports injected — hexagon never imports tech directly
        self._transport  = HttpTransportAdapter()
        self._workspace  = RayActorWorkspaceAdapter()
        self._message_bus = RayObjectStoreBus()
        self._registry   = DuckDbRegistryAdapter()

    async def __call__(self, request):
        raw = await request.body()

        # Port 1 — TransportPort receives and validates
        mcp_request = self._transport.receive(raw)

        # Port 2 — ACESWorkspacePort provides session context
        ctx = self._workspace.read(mcp_request.session_id)

        # Hexagon business logic — governed, clean
        result = self._dispatch(mcp_request, ctx)

        response = McpResponse(
            session_id=mcp_request.session_id,
            tool_name=mcp_request.tool_name,
            status="ok",
            result=result
        )

        # Port 1 — TransportPort sends response
        return self._transport.send(response)

    async def health(self, request):
        return {"status": "healthy", "transport": "http",
                "adr": "ADR-064", "replicas": 3}

    def _dispatch(self, request: McpRequest, ctx) -> dict:
        """Route to correct business logic by tool_name."""
        if request.tool_name == "ingest_glossary":
            from src.servers.bgd import ingest_glossary
            return ingest_glossary(request.payload, ctx,
                                   self._registry)
        raise ValueError(f"Unknown tool: {request.tool_name}")
```

---

## 📍 4.11 Node Affinity and Work Routing

Node affinity in the ADF operates at the work unit level —
not at the Pod level. K8s node affinity assigns Pods to nodes
at deployment time based on labels. ADF `NodeAffinity` assigns
Ray Tasks to nodes at runtime based on FQSN and task type.

| NodeAffinity | Target Nodes | Task Types | Ray Resource |
|-------------|-------------|-----------|-------------|
| `CPU_ANY` | Any node | BGD ingest, metadata extraction, overlap computation | `num_cpus=1` |
| `GPU_HIGH` | TheBeast, MiniBeast | LLM inference, embedding generation | `num_gpus=1` |
| `GPU_LOW` | Teacher | Lightweight inference, classification | `num_gpus=0.5` |
| `HEAD_ONLY` | FreedomTower | Coordinator tasks, manifest loading | `resources={"head": 1}` |

```python
# NodeAffinity applied in AdfExecutor._dispatch()

NODE_AFFINITY_OPTIONS = {
    NodeAffinity.CPU_ANY:   {"num_cpus": 1},
    NodeAffinity.GPU_HIGH:  {"num_gpus": 1, "num_cpus": 2},
    NodeAffinity.GPU_LOW:   {"num_gpus": 0.5, "num_cpus": 1},
    NodeAffinity.HEAD_ONLY: {"resources": {"node:freedomtower": 1}},
}

def _dispatch(self, subtask: SubTaskSpec) -> ray.ObjectRef:
    options = NODE_AFFINITY_OPTIONS[subtask.node_affinity]
    return ingest_bgd_task.options(
        **options,
        max_retries=subtask.max_retries,
        name=subtask.task_id
    ).remote(
        {"bgd_name": subtask.task_id,
         "source_url": "https://www.eia.gov/tools/glossary/",
         "source_format": "html-dynamic"},
        self._fqsn_registry
    )
```

---

## 🔄 4.12 The EIA Full Ingest Group Task End-to-End

The canonical Group Task that proves the complete ADF architecture:
seven glossaries in parallel, cross-domain overlap computed at the
aggregation gate, universal domains promoted to the `Energy.` schema.

```mermaid
flowchart TD

    subgraph MANIFEST ["📋    GroupTaskManifest    —    eia-full-glossary-ingest"]
        MF1[manifest_id: UUIDv7\nfailure_policy: WAIT_RETRY\n9 subtasks total]
    end

    subgraph PARALLEL ["🔀    Phase    1    —    Seven    Parallel    Ingest    Tasks"]
        T1[ingest-electricity\nCPU_ANY\ndepends_on empty]
        T2[ingest-coal\nCPU_ANY\ndepends_on empty]
        T3[ingest-natural-gas\nCPU_ANY\ndepends_on empty]
        T4[ingest-nuclear\nCPU_ANY\ndepends_on empty]
        T5[ingest-petroleum\nCPU_ANY\ndepends_on empty]
        T6[ingest-renewable\nCPU_ANY\ndepends_on empty]
        T7[ingest-alternative-fuels\nCPU_ANY\ndepends_on empty]
    end

    subgraph GATE ["🔗    Aggregation    Gate    —    ray.get    All    Seven"]
        AG[compute-cross-domain-overlap\nCPU_ANY\ndepends_on all 7\nBTU maps to Energy.ThermalUnit\nSimilarity score 0.0 to 1.0]
    end

    subgraph PROMOTE ["🏆    Phase    3    —    Sequential    Promotion"]
        PR[promote-universal-domains\nCPU_ANY\ndepends_on overlap result\nEnergy.ThermalUnit\nMarkets.SpotPrice\nEnvironment.EmissionsFactor]
    end

    subgraph OUTPUT ["📤    Final    Output    —    EiaFullIngestResult"]
        OUT1[7 BGDs ingested\n127 to 600+ terms each\n6.7x expansion ratio]
        OUT2[Cross-domain overlap computed\nBGD.Overlap table populated\nBTU in all 7 fuel groups]
        OUT3[Universal domains promoted\nEnergy schema layer created\nBLAKE3 PairHash on each]
    end

    MF1 --> T1 & T2 & T3 & T4 & T5 & T6 & T7
    T1 & T2 & T3 & T4 & T5 & T6 & T7 --> AG
    AG --> PR
    PR --> OUT1
    PR --> OUT2
    PR --> OUT3

    style MANIFEST fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style PARALLEL fill:#f0f8f0,stroke:#388e3c,stroke-width:2px
    style GATE fill:#fff4e6,stroke:#f57c00,stroke-width:3px
    style PROMOTE fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style OUTPUT fill:#e8f4fd,stroke:#1976d2,stroke-width:2px

    classDef manifestStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef parallelStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef gateStyle fill:#fff8e1,stroke:#f57c00,stroke-width:3px
    classDef promoteStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef outputStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px

    class MF1 manifestStyle
    class T1,T2,T3,T4,T5,T6,T7 parallelStyle
    class AG gateStyle
    class PR promoteStyle
    class OUT1,OUT2,OUT3 outputStyle
```

---

[🔝 Back to Section 4 TOC](#-section-4-table-of-contents)

[🏠 Back to Main TOC](./docs-section-1-overview-architecture.md#-table-of-contents)

---

*Section 4 of 6 — Continue, but append to a separate section from where
you left off to avoid duplication and corruption.*
