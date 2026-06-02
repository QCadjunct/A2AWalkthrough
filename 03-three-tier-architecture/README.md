# Section 3 — Three Tier Architecture

> **Status: PARKED.**
> This section will be migrated to be Technical Committee 56 (TC56)- and
> Agent-to-Agent (A2A)-compliant **once the Marimo Transformation (Section 2) is
> complete.** No implementation lives here yet — by design.

## The parking decision

A distributed, three-tier deployment is a sound long-term direction:

1. **Tier 1 — stateless ingress.** A thin gateway that accepts requests and
   routes them; holds no state.
2. **Tier 2 — distributed compute mesh.** A pool of workers executing bounded,
   governed agent chains concurrently.
3. **Tier 3 — shared state and upstream providers.** Shared coordination state
   plus the upstream model/Application Programming Interface (API) providers.

It is **not** being built now, and that is a deliberate, recorded decision —
treated as Write Once Reuse Many: it does not reverse on its own.

## Why parked, and why this order

The tiers **consume** the conformance surface that Section 2 establishes — the
governed Agent Card, the Fully Qualified Skill Name (FQSN) registry, the WORM
Enum-keyed cascade, the `WorkspaceState`/`WorkspaceResponseObject` envelope, and
the model registry. Building the cluster before that surface is finished would
mean building on a contract that is still changing, then tearing out scaffolding
when it settles.

So the order is: **finish the contract, then build the cluster** — and the
cluster must inherit the contract's compliance, not invent its own.

## The migration constraint (what "compliant" means here)

When this section is un-parked, it will be migrated such that:

- **A2A-compliant.** Every tier speaks the same A2A surface the foundation
  defines. Inter-tier traffic rides A2A Message / Task / Artifact; the
  governed Agent Card and FQSN registry remain the single source of agent
  identity and capability. No tier introduces an out-of-band protocol.
- **TC56-compliant.** The deployment conforms to the relevant Ecma
  International TC56 / Natural Language Interaction Protocol (NLIP) suite
  expectations, with the `WorkspaceState` envelope riding inside the standard
  message content as the foundation already establishes.

Distributed-execution specifics (the compute-mesh technology, the shared-state
layer, the deployment substrate) are each their own future Architectural
Decision Record (ADR) and Joint Application Design (JAD) session. They are not
pre-decided here; this README records only the parking and the compliance
constraint the eventual implementation must satisfy.

## Un-park conditions (all must hold)

1. Section 2 (Marimo Transformation) is complete and validated — foundation
   stable, all eight labs runnable against live agents, A2A compliance notes
   finalized.
2. An explicit decision to un-park is taken (in a JAD session), not inferred
   from this directory's existence.
3. The migration plan demonstrates A2A and TC56 compliance for every tier
   before any tier is implemented.

## Contents

- `docs/` — design notes and diagrams capturing the thinking (no code).
- `slides/` — any teaching material for the eventual architecture.

Until the conditions above are met, this section is documentation only.
