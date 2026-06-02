# Parked Enhancements — Deferred by Design

These capabilities were explicitly deferred during the A2A-compliance build so
the message + Agent Card layer stays focused and conformant. Each sits *above*
the workspace objects and does not alter the Agent-to-Agent (A2A) conformance
surface — which is precisely why it can wait.

Status: **PARKED** (designed-for, not built). Promote to an Architectural
Decision Record (ADR) when work begins.

## 1. Ray.io distributed execution

- **What:** distribute agent and tool execution across the home compute cluster
  (FreedomTower, TheBeast, MiniBeast, S3Bucket) using Ray Core.
- **Why parked:** the A2A message layer must be stable first; Ray is an
  execution substrate beneath it, not a protocol concern.
- **Entry points when resumed:** Ray Placement Groups to pin Graphics Processing
  Unit (GPU)-heavy agents (e.g. the Research agent) to specific nodes; object
  spill policies for high-volume worker data. The `@ray.remote` decorator maps
  to the Bridged Hybrid Python Architecture (Python = orchestration/spec, Ray
  C++ runtime = execution).
- **Known trap:** prior sketches contained a *fabricated* Ray `await` function —
  verify against current Ray Core API before coding.

## 2. Kubernetes plane architecture

- **What:** a control-plane / data-plane split for the agent mesh, moving the
  four agent servers (ports 9999/9998/9997/9996) from bare uvicorn processes to
  managed workloads.
- **Why parked:** the launcher's three tiers (terminal / subprocess / asyncio
  supervisor) cover current needs; Kubernetes is the scale-out story, not the
  lab story.
- **Entry points when resumed:** map each `AgentRole` to a Deployment; the
  `AgentPort` Enum becomes Service definitions; `@requires(...)` health checks
  become readiness probes.

## 3. ACES Agent Definition Framework (ADF), TaskGroup, and Task

- **What:** the richer execution-graph objects that sit *above*
  `WorkspaceState` / `WorkspaceResponseObject` — a Directed Cyclic Graph (DCG)
  of Tasks grouped into TaskGroups, defined by the ADF.
- **Why parked:** the common message base must be proven first; TaskGroup/Task
  compose workspace messages, so they depend on this build, not the reverse.
- **Entry points when resumed:** a `Task` wraps a `WorkspaceState` request plus
  its expected `WorkspaceResponseObject`; a `TaskGroup` is a `chain_depth`-aware
  collection; the ADF is the normative abstract layer they fulfill.

---

## Why the ordering is correct

The message + card layer is the **conformance surface**: it is what touches the
A2A protocol. Ray, Kubernetes, and ADF/TaskGroup/Task are all *consumers* of
that surface — they schedule, host, or compose the messages, but none of them
changes what goes on the wire. Building the conformant core first means the
parked items can be added later without revisiting A2A compliance.
