# A2AWalkthrough

A teaching-oriented evolution of the Agent-to-Agent (A2A) Walkthrough, structured
in three sections that trace a deliberate path: take a working demo, transform it
into a governed standards-layer foundation, and (later) extend it to a distributed
deployment that stays Technical Committee 56 (TC56)- and A2A-compliant.

Maintained by Peter Heller, Mind Over Metadata LLC, for CSCI 381 — Artificial
Intelligence (AI) Tools for the Practitioner, City University of New York (CUNY)
Queens College.

## The three sections

### 1. A2A Original (`01-a2a-original/`)
The upstream fork: eight Jupyter labs, agent server files, and helpers exactly as
they teach the DeepLearning.AI A2A course. This is the untouched baseline — the
demo that earns the idea. Nothing here is modified; it is the "before" against
which the transformation is measured.

### 2. Marimo Transformation (`02-marimo-transformation/`)
The active work: a shared standards-layer foundation package (`a2a_labs`) plus
Marimo notebooks that replace the Jupyter labs, and the teaching decks that
explain the evolution. This is where the demo becomes a governed system —
Enumerations (Enums) replacing free-form strings, a Pydantic Version 2 (V2)
settings boundary, the Write Once Reuse Many (WORM) Enum-keyed cascade, and a
model registry derived from real `fabric -L` output. See its README for detail.

### 3. Three Tier Architecture (`03-three-tier-architecture/`) — PARKED
A distributed deployment (stateless ingress, distributed compute mesh, shared
state plus upstream providers). **This section is parked.** It will be migrated
to be TC56- and A2A-compliant **once the Marimo Transformation is complete** —
not before. The tiers consume the conformance surface that Section 2 builds, so
that surface must be finished and validated first. See its README for the parking
decision, rationale, and the conditions under which it un-parks.

## Why this order

The demo proves one path works. The Marimo Transformation makes N paths safe —
every constraint defined once and inherited, so the marginal cost of the next
agent is flat. Only once that governed foundation is complete does a distributed
tier earn its place, and even then it must inherit the same A2A and TC56
compliance the foundation establishes. Build the contract before the cluster.

## Layout

```
A2AWalkthrough/
├── README.md                      (this file)
├── 01-a2a-original/               upstream labs, agents, helpers (baseline)
├── 02-marimo-transformation/
│   ├── README.md
│   ├── src/a2a_labs/              the standards-layer foundation package
│   ├── marimo/                    Marimo notebooks (replace the Jupyter labs)
│   ├── docs/                      architecture, standards, compliance notes
│   └── slides/                    teaching decks
└── 03-three-tier-architecture/    PARKED
    ├── README.md                  parking decision + migration conditions
    ├── docs/                      design notes (no implementation yet)
    └── slides/
```

## Governance

WSL is the authoritative git interface. Every commit is pushed to both remotes
(GitHub `QCadjunct/A2AWalkthrough` and the Synology mirror) in the same session.
Architectural decisions, once made, are treated as Write Once Reuse Many: they
do not silently reverse. The parking of Section 3 is one such decision.
