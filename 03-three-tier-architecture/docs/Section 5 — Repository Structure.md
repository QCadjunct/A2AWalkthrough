# 📁 Section 5 — Repository Structure

> **Continue, but append to a separate section from where you left off
> to avoid duplication and corruption.**
>
> This section is autonomous and self-contained.
> It covers the `aces-d4-database-design` repository layout,
> file inventory, naming conventions, and src map exclusively.
> It does not duplicate content from Sections 1–4 or Section 6.

---

## 📋 Section 5 Table of Contents

- [5.1 Repository Identity](#-51-repository-identity)
- [5.2 Top-Level Directory Map](#-52-top-level-directory-map)
- [5.3 src/ — Implementation Layer](#-53-src--implementation-layer)
- [5.4 src/adapters/ — Port Implementations](#-54-srcadapters--port-implementations)
- [5.5 src/servers/ — MCP Server Hexagons](#-55-srcservers--mcp-server-hexagons)
- [5.6 skills/ — Behavioral Contracts](#-56-skills--behavioral-contracts)
- [5.7 references/ — Governed Reference Material](#-57-references--governed-reference-material)
- [5.8 tests/ — Test Architecture](#-58-tests--test-architecture)
- [5.9 File Creation Sequence](#-59-file-creation-sequence)
- [5.10 Naming Conventions](#-510-naming-conventions)

---

## 🏠 5.1 Repository Identity

| Field | Value |
|-------|-------|
| **Repo name** | `aces-d4-database-design` |
| **GitHub** | `QCadjunct/aces-d4-database-design` |
| **Synology** | `/volume1/git/aces-d4-database-design.git` |
| **WSL path** | `/mnt/e/WSLData/Projects/aces-d4-database-design/` |
| **Windows path** | `E:\WSLData\Projects\aces-d4-database-design\` |
| **HEAD** | `87f7665` (both remotes in sync) |
| **Package manager** | `uv` exclusively — no pip, no conda |
| **Linter** | `ruff` exclusively |
| **Base class** | `ACESBaseModel` — never raw `pydantic.BaseModel` |
| **Git interface** | WSL authoritative — dual remote always |

---

## 🗺️ 5.2 Top-Level Directory Map

```mermaid
flowchart TD

    subgraph ROOT ["📁    aces-d4-database-design    —    Repository    Root"]

        subgraph TOP ["📄    Root    Files"]
            RF1[README.md\nProject system prompt\nNavigator/Driver governing context]
            RF2[pyproject.toml\nuv managed\nruff configured\ntool.uv package=false]
            RF3[.python-version\nPython version pin]
            RF4[.gitignore\nstandard Python\nplus DuckDB files]
        end

        subgraph SRC ["🔷    src/\nImplementation layer\nAll governed Python"]
            SRC1[base.py\nACESBaseModel\ntrifecta serializers]
            SRC2[ports.py\nFour port ABCs\nACESWorkspaceContext]
            SRC3[harvester.py\nSource fetcher\nPlaywright and file]
            SRC4[parser.py\nTerm extraction\nGlossaryIngestionRequest]
            SRC5[governer.py\nD4 taxonomy\nBLAKE3 PairHash\ntype mapping]
            SRC6[dag_processor.py\nKahn topological sort\nfrom Contoso pipeline]
            SRC7[registry.py\nDuckDB writer\nthree-key architecture]
            SRC8[adapters/\nPort implementations\nMVP and production]
            SRC9[servers/\nMCP server hexagons\nthree swim lanes]
            SRC10[models/\nDomain models\nACESBaseModel subclasses]
        end

        subgraph SKILLS ["📄    skills/\nBehavioral contracts\nFQSN resolution targets"]
            SK1[task.d4-database-design.fully-qualified-skill-name-registry/\nsystem.md user.md SKILL.md]
            SK2[task.d4-database-design.business-glossary-domain/\nsystem.md user.md SKILL.md]
            SK3[task.d4-database-design.fully-qualified-domain-name-governance/\nsystem.md user.md SKILL.md]
        end

        subgraph REFS ["📚    references/\nGoverned reference material\nnever generated never modified"]
            REF1[bgd/\nBGD JSON and CSV\nelectricity reference]
            REF2[pipelines/\nT-SQL extraction files\nContoso pipeline]
            REF3[manifests/\nGroupTaskManifest YAML\neia-full-glossary-ingest]
            REF4[adrs/\nADR summaries\nlinks to obsidian-adr]
        end

        subgraph TESTS ["🧪    tests/\nTest suite\nMVP adapter first"]
            TST1[unit/\nPort contract tests\nAdapter unit tests]
            TST2[integration/\nServer hexagon tests\nFour ports injected]
            TST3[fixtures/\nTest data\nelectricity BGD sample]
        end

        subgraph DOCS ["📖    docs/\nArchitecture documentation\nSections 1 through 6"]
            DOC1[section-1-overview-architecture.md]
            DOC2[section-2-d4-methodology.md]
            DOC3[section-3-hexagonal-architecture.md]
            DOC4[section-4-adf-and-ray.md]
            DOC5[section-5-repository-structure.md]
            DOC6[section-6-governance.md]
        end

    end

    RF1 --> SRC1
    RF2 --> SRC1
    SRC2 --> SRC8
    SRC2 --> SRC9
    SK1 --> SRC9
    REF1 --> TST3

    style ROOT fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style TOP fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style SRC fill:#e8f4fd,stroke:#1976d2,stroke-width:2px
    style SKILLS fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    style REFS fill:#fff4e6,stroke:#f57c00,stroke-width:2px
    style TESTS fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style DOCS fill:#f0f8f0,stroke:#388e3c,stroke-width:2px

    classDef rootStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef srcStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef skillStyle fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef refStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef testStyle fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef docStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px

    class RF1,RF2,RF3,RF4 rootStyle
    class SRC1,SRC2,SRC3,SRC4,SRC5,SRC6,SRC7,SRC8,SRC9,SRC10 srcStyle
    class SK1,SK2,SK3 skillStyle
    class REF1,REF2,REF3,REF4 refStyle
    class TST1,TST2,TST3 testStyle
    class DOC1,DOC2,DOC3,DOC4,DOC5,DOC6 docStyle
```

### 📐 Flat Directory Listing

```
aces-d4-database-design/
│
├── README.md                          ← Project system prompt
├── pyproject.toml                     ← uv managed, ruff configured
├── .python-version                    ← Python version pin
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── base.py                        ← ACESBaseModel — everything depends on this
│   ├── ports.py                       ← Four port ABCs + message models
│   ├── harvester.py                   ← Source fetcher (static/dynamic/file)
│   ├── parser.py                      ← Term extraction → GlossaryIngestionRequest
│   ├── governer.py                    ← D⁴ taxonomy + BLAKE3 + type mapping
│   ├── dag_processor.py               ← Kahn's topological sort
│   ├── registry.py                    ← DuckDB writer coordination
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── transport/
│   │   │   ├── __init__.py
│   │   │   ├── stdio.py               ← StdioTransportAdapter (MVP)
│   │   │   └── http.py                ← HttpTransportAdapter (ADR-061)
│   │   ├── workspace/
│   │   │   ├── __init__.py
│   │   │   ├── in_process.py          ← InProcessWorkspaceAdapter (MVP)
│   │   │   └── ray_actor.py           ← RayActorWorkspaceAdapter (ADR-062)
│   │   ├── bus/
│   │   │   ├── __init__.py
│   │   │   ├── in_process.py          ← InProcessBus (MVP)
│   │   │   └── ray_object_store.py    ← RayObjectStoreBus (ADR-062)
│   │   └── registry/
│   │       ├── __init__.py
│   │       ├── in_process.py          ← InProcessRegistryAdapter (MVP)
│   │       └── duckdb.py              ← DuckDbRegistryAdapter (Phase 1)
│   ├── servers/
│   │   ├── __init__.py
│   │   ├── fqsn_registry.py           ← MCP Server 1 hexagon
│   │   ├── bgd.py                     ← MCP Server 2 hexagon
│   │   └── fqdn_governance.py         ← MCP Server 3 hexagon
│   └── models/
│       ├── __init__.py
│       ├── bgd_models.py              ← GlossaryIngestionRequest, BgdManifest
│       ├── manifest_models.py         ← GroupTaskManifest, SubTaskSpec
│       └── registry_models.py         ← BgdRegistry, BgdTerm, BgdOverlap
│
├── skills/
│   ├── task.d4-database-design.fully-qualified-skill-name-registry/
│   │   ├── system.md                  ← WORM behavioral contract
│   │   ├── user.md                    ← WORM input template
│   │   └── SKILL.md                   ← Documentation + chaining
│   ├── task.d4-database-design.business-glossary-domain/
│   │   ├── system.md
│   │   ├── user.md
│   │   └── SKILL.md
│   └── task.d4-database-design.fully-qualified-domain-name-governance/
│       ├── system.md
│       ├── user.md
│       └── SKILL.md
│
├── references/
│   ├── bgd/
│   │   └── electricity/
│   │       ├── electricity-domain-kg.json     ← 847 governed domains
│   │       ├── electricity-domain-reuse.csv   ← 6.7x expansion analysis
│   │       ├── electricity-domain-taxonomy.md ← D⁴ taxonomy tree
│   │       └── UPGRADE-NOTES.md               ← SHA-256→BLAKE3, sentinel fixes
│   ├── pipelines/
│   │   ├── 01_sp_GetTableMetadataForMigration.sql
│   │   ├── 02_qry_FullColumnInventory.sql
│   │   └── 03_qry_ConstraintsAndDependencies.sql
│   ├── manifests/
│   │   └── group-task-eia-full-ingest.yaml    ← GroupTaskManifest YAML
│   └── adrs/
│       └── ADR-INDEX.md                       ← Links to obsidian-adr
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_base.py               ← ACESBaseModel trifecta serializers
│   │   ├── test_ports.py              ← Port contract validation
│   │   ├── test_adapters_transport.py ← StdioTransportAdapter
│   │   ├── test_adapters_workspace.py ← InProcessWorkspaceAdapter
│   │   ├── test_adapters_bus.py       ← InProcessBus
│   │   └── test_adapters_registry.py  ← InProcessRegistryAdapter
│   ├── integration/
│   │   ├── test_bgd_server.py         ← BGD hexagon end-to-end
│   │   ├── test_fqsn_registry.py      ← FQSN Registry hexagon
│   │   └── test_full_pipeline.py      ← Electricity BGD ingest
│   └── fixtures/
│       ├── electricity_sample.json    ← 10-term subset for fast tests
│       └── mock_fqsn_records.py       ← Governed FQSN test records
│
└── docs/
    ├── section-1-overview-architecture.md
    ├── section-2-d4-methodology.md
    ├── section-3-hexagonal-architecture.md
    ├── section-4-adf-and-ray.md
    ├── section-5-repository-structure.md
    └── section-6-governance.md
```

---

## 🔷 5.3 src/ — Implementation Layer

The `src/` directory contains only governed Python. No transport
libraries. No database drivers. No Ray imports — except in the
adapter files where they belong.

```mermaid
flowchart TD

    subgraph SRC ["🔷    src/    —    Dependency    Order"]

        subgraph L1 ["🥇    Layer    1    —    Constitutional    Base"]
            B1[base.py\nACESBaseModel\nPydantic V2 inheritance\nFour trifecta serializers\nEverything depends on this]
        end

        subgraph L2 ["🥈    Layer    2    —    Port    Contracts"]
            P1[ports.py\nMcpRequest ACESBaseModel\nMcpResponse ACESBaseModel\nACESWorkspaceContext ACESBaseModel\nTransportPort ABC\nACESWorkspacePort ABC\nMessageBusPort ABC\nRegistryPort ABC]
        end

        subgraph L3 ["🥉    Layer    3    —    Domain    Models"]
            M1[models/bgd_models.py\nGlossaryIngestionRequest\nBgdManifest\nRawGlossary]
            M2[models/manifest_models.py\nGroupTaskManifest\nSubTaskSpec\nAggregationSpec\nFailurePolicy\nNodeAffinity]
            M3[models/registry_models.py\nBgdRegistry\nBgdTerm\nBgdOverlap]
        end

        subgraph L4 ["🏅    Layer    4    —    Pipeline    Components"]
            C1[harvester.py\nfetch any URL\nPlaywright dynamic\nfile ingest\nreturns RawGlossary]
            C2[parser.py\nextract term-definition pairs\nreturns GlossaryIngestionRequest]
            C3[governer.py\nD4 taxonomy assignment\nBLAKE3 PairHash\ntype mapping\nCHECK constraint generation]
            C4[dag_processor.py\nKahn topological sort\ntable dependency ordering\nCircular dependency detection]
            C5[registry.py\nCoordinates DuckDb writes\ndelegates to RegistryPort adapter]
        end

        subgraph L5 ["🎯    Layer    5    —    Adapters    and    Servers"]
            A1[adapters/\nPort implementations\nMVP and production]
            S1[servers/\nMCP hexagons\nfour ports injected]
        end

    end

    B1 --> P1
    P1 --> M1
    P1 --> M2
    P1 --> M3
    M1 --> C1
    M1 --> C2
    M1 --> C3
    P1 --> C4
    P1 --> C5
    C1 --> A1
    C2 --> A1
    C3 --> A1
    P1 --> A1
    A1 --> S1

    style SRC fill:#e8f4fd,stroke:#1976d2,stroke-width:2px
    style L1 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style L2 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style L3 fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    style L4 fill:#f0f8f0,stroke:#388e3c,stroke-width:2px
    style L5 fill:#fff4e6,stroke:#f57c00,stroke-width:2px

    classDef l1Style fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    classDef l2Style fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef l3Style fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef l4Style fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef l5Style fill:#fff8e1,stroke:#f57c00,stroke-width:2px

    class B1 l1Style
    class P1 l2Style
    class M1,M2,M3 l3Style
    class C1,C2,C3,C4,C5 l4Style
    class A1,S1 l5Style
```

### 📐 Key Files — What Each Does

| File | SRP Responsibility | Key Classes/Functions |
|------|-------------------|----------------------|
| `base.py` | Constitutional base model | `ACESBaseModel`, four trifecta methods |
| `ports.py` | Port contracts | `TransportPort`, `ACESWorkspacePort`, `MessageBusPort`, `RegistryPort`, `McpRequest`, `McpResponse`, `ACESWorkspaceContext` |
| `harvester.py` | Source fetching | `harvest(url, format)` → `RawGlossary` |
| `parser.py` | Term extraction | `parse(raw)` → `GlossaryIngestionRequest` |
| `governer.py` | D⁴ taxonomy + BLAKE3 | `govern(request, bgd_name)` → `BgdManifest`, `get_duckdb_type_mapping()`, `compute_pair_hash()` |
| `dag_processor.py` | Dependency ordering | `get_table_dependencies(metadata_df)` → ordered list |
| `registry.py` | Registry coordination | `write(manifest)` → delegates to `RegistryPort` |

---

## 🔌 5.4 src/adapters/ — Port Implementations

Each subdirectory in `adapters/` maps to one port.
Each port has at minimum two adapters: an MVP InProcess
adapter and a production adapter. The hexagon never imports
from `adapters/` — adapters are injected at construction.

```mermaid
flowchart LR

    subgraph PORTS ["🔌    Port    ABCs    in    ports.py"]
        PT[TransportPort]
        WP[ACESWorkspacePort]
        MB[MessageBusPort]
        RP[RegistryPort]
    end

    subgraph TRANSPORT ["📡    adapters/transport/"]
        T1[stdio.py\nStdioTransportAdapter\nMVP — zero infra]
        T2[http.py\nHttpTransportAdapter\nRay Serve — ADR-061]
    end

    subgraph WORKSPACE ["🗂️    adapters/workspace/"]
        W1[in_process.py\nInProcessWorkspaceAdapter\nMVP — dict in memory]
        W2[ray_actor.py\nRayActorWorkspaceAdapter\nRay Actor — ADR-062]
    end

    subgraph BUS ["📨    adapters/bus/"]
        B1[in_process.py\nInProcessBus\nMVP — dict queue]
        B2[ray_object_store.py\nRayObjectStoreBus\nRay store — ADR-062]
    end

    subgraph REGISTRY ["🗄️    adapters/registry/"]
        R1[in_process.py\nInProcessRegistryAdapter\nMVP — dict store]
        R2[duckdb.py\nDuckDbRegistryAdapter\nDuckDB — Phase 1]
    end

    PT -.->|implemented by| T1 & T2
    WP -.->|implemented by| W1 & W2
    MB -.->|implemented by| B1 & B2
    RP -.->|implemented by| R1 & R2

    style PORTS fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style TRANSPORT fill:#e8f4fd,stroke:#1976d2,stroke-width:2px
    style WORKSPACE fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    style BUS fill:#fff4e6,stroke:#f57c00,stroke-width:2px
    style REGISTRY fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px

    classDef portStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef transportStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef workspaceStyle fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef busStyle fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef registryStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px

    class PT,WP,MB,RP portStyle
    class T1,T2 transportStyle
    class W1,W2 workspaceStyle
    class B1,B2 busStyle
    class R1,R2 registryStyle
```

---

## 🏛️ 5.5 src/servers/ — MCP Server Hexagons

Each server is a pure hexagon — business logic only.
No transport imports. No database imports. No Ray imports.
Four ports injected at construction via dependency injection.

```mermaid
flowchart TD

    subgraph SERVERS ["🏛️    src/servers/    —    Three    MCP    Hexagons"]

        subgraph FQSN ["🔑    fqsn_registry.py"]
            FS1[SRP: FQSN resolution\nregistration and validation\ndiscovery handshake gate]
            FS2[Tools:\nresolve_fqsn\nregister_fqsn\ndisable_fqsn\nlist_fqsns\nhealth]
            FS3[Port 8001\nstartup gate\nall agents depend on this]
        end

        subgraph BGD ["📚    bgd.py"]
            BS1[SRP: BGD ingestion\ncanonical term governance\nD4 taxonomy assignment]
            BS2[Tools:\ningest_glossary\nresolve_fqdn\ncalculate_reuse\nlist_bgds\nhealth]
            BS3[Port 8002\n3 replicas\nHPA max 7 for EIA ingest]
        end

        subgraph FQDN ["🗂️    fqdn_governance.py"]
            GS1[SRP: FQDN definition\nmigration and enhancement\nclient-approval cycle]
            GS2[Tools:\ndefine_fqdn\nmigrate_fqdn\nenhance_fqdn\napprove_fqdn\npropagate_fqdn\nhealth]
            GS3[Port 8003\ndepends on FQSN and BGD\nstartup last]
        end

    end

    subgraph INJECTION ["💉    Dependency    Injection    Pattern"]
        DI1[All three servers\naccept four ports\nin constructor]
        DI2[def __init__\nself\ntransport TransportPort\nworkspace ACESWorkspacePort\nmessage_bus MessageBusPort\nregistry RegistryPort]
        DI3[MVP: InProcess adapters\nProduction: Ray adapters\nZero server code changes]
    end

    FS1 --> DI1
    BS1 --> DI1
    GS1 --> DI1
    DI1 --> DI2
    DI2 --> DI3

    style SERVERS fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px
    style FQSN fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style BGD fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    style FQDN fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style INJECTION fill:#f0f8f0,stroke:#388e3c,stroke-width:2px

    classDef fqsnStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef bgdStyle fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef fqdnStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef injStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px

    class FS1,FS2,FS3 fqsnStyle
    class BS1,BS2,BS3 bgdStyle
    class GS1,GS2,GS3 fqdnStyle
    class DI1,DI2,DI3 injStyle
```

### 🔬 Server Construction Pattern

```python
# All three servers follow this identical pattern.
# The hexagon is pure business logic.
# Technology lives entirely in adapters.

from src.ports import (
    TransportPort, ACESWorkspacePort,
    MessageBusPort, RegistryPort
)


class BgdServer:
    """
    BGD MCP Server — one hexagon.
    SRP: BGD ingestion, canonical term governance, D⁴ taxonomy.
    Knows nothing about HTTP, Ray, DuckDB, or stdio.
    Imports only port contracts from src/ports.py.
    """

    def __init__(
        self,
        transport:   TransportPort,
        workspace:   ACESWorkspacePort,
        message_bus: MessageBusPort,
        registry:    RegistryPort
    ):
        self._transport   = transport
        self._workspace   = workspace
        self._message_bus = message_bus
        self._registry    = registry

    def ingest_glossary(
        self,
        request: dict,
        session_id: str
    ) -> dict:
        """Core tool — business logic only. No tech imports."""
        ctx = self._workspace.read(session_id)
        # ... governed ingest pipeline ...
        pair_hash = self._registry.write_bgd(result, role=ctx.role)
        return {"pair_hash": pair_hash, "status": "ok"}


# MVP wiring — for development and unit tests
from src.adapters.transport.stdio import StdioTransportAdapter
from src.adapters.workspace.in_process import InProcessWorkspaceAdapter
from src.adapters.bus.in_process import InProcessBus
from src.adapters.registry.in_process import InProcessRegistryAdapter

bgd_server = BgdServer(
    transport=StdioTransportAdapter(),
    workspace=InProcessWorkspaceAdapter(),
    message_bus=InProcessBus(),
    registry=InProcessRegistryAdapter()
)

# Production wiring — Ray Serve deployment
from src.adapters.transport.http import HttpTransportAdapter
from src.adapters.workspace.ray_actor import RayActorWorkspaceAdapter
from src.adapters.bus.ray_object_store import RayObjectStoreBus
from src.adapters.registry.duckdb import DuckDbRegistryAdapter

bgd_server_prod = BgdServer(
    transport=HttpTransportAdapter(),
    workspace=RayActorWorkspaceAdapter(),
    message_bus=RayObjectStoreBus(),
    registry=DuckDbRegistryAdapter()
)
# Zero server code changes between MVP and production.
```

---

## 📄 5.6 skills/ — Behavioral Contracts

Each MCP server has exactly one skill directory. Each skill
directory contains exactly three files. This is ADR-007
(Three-File Skill Standard) applied to this Task Group.

```mermaid
flowchart LR

    subgraph SKILLS ["📄    skills/    —    Three    Files    Per    Server"]

        subgraph S1 ["🔑    task.d4...fqsn-registry/"]
            F1A[system.md\nBehavioral contract\nWhat the agent must BE\nWORM — read-only ConfigMap]
            F1B[user.md\nInput template\nWhat the agent receives\nWORM — read-only ConfigMap]
            F1C[SKILL.md\nDocumentation\nChaining relationships\nDependencies: none\nDownstream: bgd fqdn-governance]
        end

        subgraph S2 ["📚    task.d4...business-glossary-domain/"]
            F2A[system.md\nBGD ingestion contract\nD4 taxonomy authority\nWORM]
            F2B[user.md\nGlossaryIngestionRequest\ninput template\nWORM]
            F2C[SKILL.md\nThree tools documented\nDependencies: fqsn-registry\nDownstream: fqdn-governance]
        end

        subgraph S3 ["🗂️    task.d4...fqdn-governance/"]
            F3A[system.md\nFQDN definition authority\nmigration contract\nWORM]
            F3B[user.md\nFQDN governance request\nclient approval template\nWORM]
            F3C[SKILL.md\nFive tools documented\nDependencies: fqsn-registry bgd\nDownstream: none — final]
        end

    end

    subgraph WORM_RULE ["🔒    WORM    Enforcement"]
        W1[Mounted read-only\nas Kubernetes ConfigMap\nagent cannot modify\nits own contract]
        W2[system.md is the constitution\nuser.md is the input template\nSKILL.md is the manual]
    end

    F1A --> W1
    F2A --> W1
    F3A --> W1

    style SKILLS fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    style S1 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style S2 fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    style S3 fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style WORM_RULE fill:#f8f0ff,stroke:#7b1fa2,stroke-width:2px

    classDef s1Style fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef s2Style fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef s3Style fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef wormStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px

    class F1A,F1B,F1C s1Style
    class F2A,F2B,F2C s2Style
    class F3A,F3B,F3C s3Style
    class W1,W2 wormStyle
```

---

## 📚 5.7 references/ — Governed Reference Material

The `references/` directory contains material that is never
generated by the build and never modified by the pipeline.
It is the governed source of truth for tests, documentation,
and planning.

| Path | Contents | Status |
|------|---------|--------|
| `references/bgd/electricity/electricity-domain-kg.json` | 847 governed domains — the reference BGD | ✅ Committed `87f7665` |
| `references/bgd/electricity/electricity-domain-reuse.csv` | Reuse analysis — 6.7x expansion ratio | ✅ Committed |
| `references/bgd/electricity/electricity-domain-taxonomy.md` | D⁴ taxonomy tree — electricity domain | ✅ Committed |
| `references/bgd/electricity/UPGRADE-NOTES.md` | SHA-256→BLAKE3 + sentinel value fixes required | ✅ Committed |
| `references/pipelines/01_sp_GetTableMetadataForMigration.sql` | Stored procedure — Contoso pipeline | ✅ Committed `87f7665` |
| `references/pipelines/02_qry_FullColumnInventory.sql` | Four inventory queries | ✅ Committed |
| `references/pipelines/03_qry_ConstraintsAndDependencies.sql` | PK/FK/DAG/circular dependency | ✅ Committed |
| `references/manifests/group-task-eia-full-ingest.yaml` | GroupTaskManifest — EIA full ingest | 🔲 Pending |
| `references/adrs/ADR-INDEX.md` | Links to obsidian-adr vault | 🔲 Pending |

> **Governance rule:** Files in `references/` are never modified
> by pipeline code. They are input artifacts — read by tests and
> documentation, not written by `governer.py` or `registry.py`.
> If a reference file needs updating, it is a Navigator decision,
> not a pipeline operation.

---

## 🧪 5.8 tests/ — Test Architecture

Tests are organized in three layers matching the implementation
dependency chain. Unit tests run without infrastructure.
Integration tests require MVP adapters. No test requires Ray,
DuckDB, or HTTP infrastructure.

```mermaid
flowchart TD

    subgraph TESTS ["🧪    tests/    —    Three    Layer    Test    Architecture"]

        subgraph UNIT ["🔬    unit/    —    No    Infrastructure    Required"]
            U1[test_base.py\nACESBaseModel trifecta\nJSON YAML MD TOON\nAll four formats validate]
            U2[test_ports.py\nPort contract validation\nMcpRequest McpResponse\nACESWorkspaceContext]
            U3[test_adapters_transport.py\nStdioTransportAdapter\nreceive and send\nValidationError on malformed]
            U4[test_adapters_workspace.py\nInProcessWorkspaceAdapter\noperator.add discipline\nWORM audit trail]
            U5[test_adapters_bus.py\nInProcessBus\npublish consume ack\ntimeout returns None]
            U6[test_adapters_registry.py\nInProcessRegistryAdapter\nthree-key architecture\ndisable not delete]
        end

        subgraph INTEGRATION ["🔗    integration/    —    MVP    Adapters    Required"]
            I1[test_bgd_server.py\nBGD hexagon end-to-end\nelectricity sample fixture\nfour ports injected]
            I2[test_fqsn_registry.py\nFQSN Registry hexagon\nresolve register disable\ngoverned gate check]
            I3[test_full_pipeline.py\nElectricity BGD ingest\nharvest to registry write\n6.7x expansion verified]
        end

        subgraph FIXTURES ["📦    fixtures/    —    Test    Data"]
            FX1[electricity_sample.json\n10-term subset\nfast unit tests\nrepresentative domains]
            FX2[mock_fqsn_records.py\nGoverned FQSN test records\nfor gate check tests]
        end

    end

    subgraph RULES ["📋    Test    Governance    Rules"]
        R1[Unit tests: no imports\nfrom adapters/transport/http.py\nno Ray no DuckDB no HTTP]
        R2[Integration tests: MVP adapters\nInProcess only\nno Ray no DuckDB]
        R3[Electricity sample is canonical\nIf test_full_pipeline passes\nthe engine is proven]
    end

    U1 --> I1
    U6 --> I1
    FX1 --> I3
    FX2 --> I2
    R1 --> U1
    R2 --> I1
    R3 --> I3

    style TESTS fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style UNIT fill:#ffebee,stroke:#c2185b,stroke-width:2px
    style INTEGRATION fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style FIXTURES fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style RULES fill:#e8f5e8,stroke:#388e3c,stroke-width:2px

    classDef unitStyle fill:#ffebee,stroke:#c2185b,stroke-width:2px
    classDef intStyle fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef fixStyle fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    classDef ruleStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px

    class U1,U2,U3,U4,U5,U6 unitStyle
    class I1,I2,I3 intStyle
    class FX1,FX2 fixStyle
    class R1,R2,R3 ruleStyle
```

---

## 📋 5.9 File Creation Sequence

The sequence is governed by the dependency chain.
No file can be created before its dependency exists.
No exceptions.

```mermaid
flowchart TD

    subgraph S1 ["🥇    Sprint    1    —    Foundation"]
        F1[src/base.py\nACESBaseModel\ntrifecta serializers\nNo dependencies]
        F2[src/ports.py\nFour port ABCs\nDepends: base.py only]
        F3[src/models/bgd_models.py\nGlossaryIngestionRequest\nBgdManifest\nDepends: base.py]
        F4[src/models/manifest_models.py\nGroupTaskManifest\nFailurePolicy\nDepends: base.py]
        F5[src/models/registry_models.py\nBgdRegistry BgdTerm BgdOverlap\nDepends: base.py]
    end

    subgraph S2 ["🥈    Sprint    2    —    MVP    Adapters"]
        A1[src/adapters/transport/stdio.py\nStdioTransportAdapter\nDepends: ports.py]
        A2[src/adapters/workspace/in_process.py\nInProcessWorkspaceAdapter\nDepends: ports.py]
        A3[src/adapters/bus/in_process.py\nInProcessBus\nDepends: ports.py]
        A4[src/adapters/registry/in_process.py\nInProcessRegistryAdapter\nDepends: ports.py]
    end

    subgraph S3 ["🥉    Sprint    3    —    Pipeline    Components"]
        P1[src/harvester.py\nDepends: bgd_models.py]
        P2[src/parser.py\nDepends: bgd_models.py]
        P3[src/governer.py\nDepends: bgd_models.py\nregistry_models.py]
        P4[src/dag_processor.py\nDepends: base.py only]
        P5[src/registry.py\nDepends: ports.py\nregistry_models.py]
    end

    subgraph S4 ["🏅    Sprint    4    —    MCP    Server    Hexagons"]
        SV1[src/servers/fqsn_registry.py\nDepends: ports.py all MVP adapters]
        SV2[src/servers/bgd.py\nDepends: ports.py all MVP adapters\nharvester parser governer]
        SV3[src/servers/fqdn_governance.py\nDepends: ports.py all MVP adapters]
    end

    subgraph S5 ["🎯    Sprint    5    —    Production    Adapters"]
        PA1[src/adapters/transport/http.py\nHttpTransportAdapter\nADR-061 prerequisite filed]
        PA2[src/adapters/workspace/ray_actor.py\nRayActorWorkspaceAdapter\nADR-062 prerequisite filed]
        PA3[src/adapters/bus/ray_object_store.py\nRayObjectStoreBus\nADR-062 prerequisite filed]
        PA4[src/adapters/registry/duckdb.py\nDuckDbRegistryAdapter\nPhase 1 — already on stack]
    end

    F1 --> F2
    F1 --> F3 & F4 & F5
    F2 --> A1 & A2 & A3 & A4
    F3 --> P1 & P2 & P3
    F2 --> P5
    A1 & A2 & A3 & A4 --> SV1 & SV2 & SV3
    P1 & P2 & P3 --> SV2
    SV1 & SV2 & SV3 --> PA1 & PA2 & PA3
    F2 --> PA4

    style S1 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style S2 fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    style S3 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style S4 fill:#fff4e6,stroke:#f57c00,stroke-width:2px
    style S5 fill:#e1f5fe,stroke:#0277bd,stroke-width:2px

    classDef s1Style fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef s2Style fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef s3Style fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef s4Style fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef s5Style fill:#e1f5fe,stroke:#0277bd,stroke-width:2px

    class F1,F2,F3,F4,F5 s1Style
    class A1,A2,A3,A4 s2Style
    class P1,P2,P3,P4,P5 s3Style
    class SV1,SV2,SV3 s4Style
    class PA1,PA2,PA3,PA4 s5Style
```

---

## 📐 5.10 Naming Conventions

All naming conventions follow ADR-029 (Acronym-First-Use Standard)
and the KISS principle — Keep It Simple and Standard.

### Python Files and Classes

| Convention | Rule | Example |
|-----------|------|---------|
| Module names | `snake_case` | `bgd_models.py`, `dag_processor.py` |
| Class names | `PascalCase` | `ACESBaseModel`, `GroupTaskManifest` |
| Method names | `snake_case` | `ingest_glossary`, `compute_pair_hash` |
| Constants | `UPPER_SNAKE` | `WAIT_RETRY`, `CPU_ANY` |
| Port ABCs | `PascalCase` + `Port` suffix | `TransportPort`, `RegistryPort` |
| Adapters | `PascalCase` + technology + `Adapter` | `StdioTransportAdapter`, `DuckDbRegistryAdapter` |
| MCP servers | `PascalCase` + `Server` suffix | `BgdServer`, `FqsnRegistryServer` |
| Ray Actors | `PascalCase` + `Actor` suffix | `FqsnRegistryActor`, `BgdRegistryActor` |

### File and Directory Names

| Convention | Rule | Example |
|-----------|------|---------|
| Python source | `snake_case.py` | `dag_processor.py` |
| SQL reference files | `NN_prefix_description.sql` | `01_sp_GetTableMetadataForMigration.sql` |
| YAML manifests | `kebab-case.yaml` | `group-task-eia-full-ingest.yaml` |
| Markdown docs | `section-N-kebab-description.md` | `section-3-hexagonal-architecture.md` |
| ADR files | `ADR-NNN-kebab-title.md` | `ADR-063-hexagonal-ports-adapters.md` |
| Skill directories | Full FQSN path as directory name | `task.d4-database-design.business-glossary-domain/` |
| BGD reference files | `{bgd-name}-domain-{type}.{ext}` | `electricity-domain-kg.json` |

### Git Commit Convention

```
type(scope): description

types: feat docs fix refactor test chore
scope: bgd fqsn fqdn ports adapters models tests docs adr

Examples:
feat(bgd): implement InProcessRegistryAdapter MVP
docs(section-5): add repository structure
fix(governer): replace SHA-256 with BLAKE3-256
refactor(servers): inject four ports into BgdServer
test(adapters): add InProcessWorkspaceAdapter operator.add test
adr: ADR-063 hexagonal ports and adapters
```

### Commit Sequence Discipline

Every session close commits to both remotes:

```bash
cd /mnt/e/WSLData/Projects/aces-d4-database-design
git add -A
git commit -m "type(scope): description"
git push origin
git push synology
```

**Dual remote is mandatory — every commit, every session.**

---

[🔝 Back to Section 5 TOC](#-section-5-table-of-contents)

[🏠 Back to Main TOC](./docs-section-1-overview-architecture.md#-table-of-contents)

---

*Section 5 of 6 — Continue, but append to a separate section from where
you left off to avoid duplication and corruption.*
