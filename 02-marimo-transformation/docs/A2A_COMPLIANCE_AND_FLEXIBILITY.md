# A2A Compliance & The Flexibility Argument

How three objects — the **common message base**, the **WorkspaceResponseObject**,
and the **governed Agent Card** — take the original Agent-to-Agent (A2A)
protocol exactly as Labs 1-8 use it, and make it dramatically more flexible
without breaking conformance.

Every acronym spelled out on first use. Key: A2A - Agent-to-Agent; FQSN - Fully
Qualified Skill Name; BGD - Business Glossary Definition; FQDN - Fully Qualified
Domain Name; WORM - Write Once Reuse Many; NLIP - Natural Language Interaction
Protocol; ADK - Agent Development Kit.

## The governing principle

The A2A protocol defines three things the labs use: an **Agent Card** (identity
+ skills + URL, fetched for discovery), a **Message** (what a client sends), and
a **Task/Artifact** (what an agent returns). Our objects do not replace any of
them. They ride **inside** the parts the protocol treats as opaque — the message
content and the artifact payload — and they make the card a governed object
instead of a hand-typed literal. Conformance is untouched; flexibility is added
above the normative surface.

---

## Layer 1 — The Agent Card

### What the original A2A gives you

```python
# Hand-written, once per agent, per lab:
skill = AgentSkill(id="insurance_coverage", name="Insurance coverage",
                   description="...", tags=["insurance"], examples=[...])
agent_card = AgentCard(name="InsurancePolicyCoverageAgent",
                       url=f"http://{HOST}:{PORT}/", version="1.0.0",
                       capabilities=AgentCapabilities(streaming=False),
                       skills=[skill])
```

Functional. But the id, name, tags, URL, and port are free-form strings repeated
in every lab. Nothing connects the skill a card advertises to the skill a
request asks for or the skill the orchestrator routes to — they are three
separate strings that happen to match.

### How ours becomes infinitely more flexible

```python
from a2a_labs.a2a_bridge import build_agent_card
from a2a_labs import AgentRole, get_settings

card = build_agent_card(AgentRole.POLICY, get_settings())  # that's it
```

The card is built from a **Fully Qualified Skill Name (FQSN) registry** and the
typed `AgentRole`. One builder serves Lab 2 (hand-built server), Lab 4 (ADK),
Lab 6 (LangGraph), and Lab 8 (orchestrator). The flexibility this unlocks:

| Need | Original | Governed card |
|------|----------|---------------|
| Add a skill to an agent | edit that lab's card code | add one `SkillSpec` to the registry |
| Re-point a port/URL | edit every hardcoded literal | change `AgentPort` Enum once |
| Route by skill (Lab 8) | match free strings by hand | look up the FQSN in the registry |
| Audit every skill in the system | grep 8 files | enumerate one registry |
| A new agent reuses a skill | copy-paste the AgentSkill | reference the same FQSN |

The FQSN (`policy.insurance_coverage`) is the single identity a card advertises,
a request targets (`WorkspaceState.skill_id`), and the orchestrator routes to —
**one string, three uses, defined once.**

---

## Layer 2 — The common message object (WorkspaceEnvelope)

### What the original A2A gives you

A `Message` carries a text part. A `Task` carries `Artifact`s. The protocol does
not give you any notion of *identity continuity* between a request and its
response — if you send three messages and get three answers back, matching them
is your problem, usually solved by hoping the order is preserved.

### How ours becomes infinitely more flexible

`WorkspaceEnvelope` is the **common base** both the request and the response
inherit. It carries the BLAKE3 identity chain — BGD surrogate, FQDN, PAIR_HASH —
plus `chain_depth` and `correlation_id`. Because both sides share it:

* A response **inherits** its request's identity (`req.respond(...)` copies the
  BGD/FQDN, increments `chain_depth`, sets `correlation_id` to the request's
  PAIR_HASH).
* Matching a reply to its request is **structural, not positional**:
  `verify_correlation(request, response)` compares hashes. Parallel handoffs in
  Lab 8 can return out of order and still be attributed correctly.
* Provenance is **WORM** (`frozen=True`): you never mutate an envelope, you
  build the next one — so the identity chain is tamper-evident by construction.

This is the object the Model Context Protocol (MCP) client/server boundary and
the A2A agent/agent boundary both share — the single "common message object" you
asked for.

---

## Layer 3 — WorkspaceResponseObject

### What the original A2A gives you

The response side of the labs is a bare string (`new_agent_text_message(text)`)
or an `Artifact` whose text you parse yourself. There is no typed notion of
*status* (did the agent answer, partially answer, need input, fail, or hit the
"I don't know" path?), and no record of *which agent* produced *which part* of a
multi-agent answer.

### How ours becomes infinitely more flexible

`WorkspaceResponseObject` is the structural mirror of `WorkspaceState`:

```python
resp = request.respond(
    result="In-network: $25 copay per session.",
    status=ResponseStatus.OK,          # typed: OK / PARTIAL / NEED_INPUT / ERROR / UNKNOWN
    source_agent="InsurancePolicyCoverageAgent",
)
resp.is_terminal        # True -> no further hop needed
resp.correlation_id     # == request.blake3_pair_hash
resp.answered_skill_id  # which FQSN was actually exercised
```

What this unlocks across the labs:

* **Lab 3 (client):** can tell an answer from an "I don't know"
  (`ResponseStatus.UNKNOWN`) without string-sniffing — the policy agent's
  guardrail becomes a typed outcome.
* **Lab 5 (sequential chain):** `chain_depth` and `is_terminal` let the chain
  decide whether another hop is needed instead of always running every step.
* **Lab 8 (orchestrator):** `source_agent` makes the "say which agent gave you
  the information" instruction structural — attribution is a field, not a
  prompt request that the model might forget.

---

## Incremental adoption — the flexibility that matters most

`response_from_text()` returns `None` when it receives a plain-string answer
from an agent that does not yet emit workspace objects. So a **governed client
talks to both governed and ungoverned agents**. You can adopt these objects one
agent at a time across Labs 1-8 — there is no flag day. That is what "infinitely
more flexible" means in practice: the new structure is strictly additive, rides
inside the protocol's opaque fields, and degrades gracefully to the original
behavior.

---

## The one-sentence version

> The original A2A defines the envelope; our three objects define the *contents
> and the catalog* — a governed Agent Card built from one FQSN registry, a
> common WORM identity base shared by every message, and a typed response mirror
> — so the same conformant protocol now supports skill-routing, out-of-order
> correlation, typed outcomes, and per-agent attribution across all eight labs,
> while still talking to agents that have none of it.

---

## Parked as future enhancements (explicitly NOT in this build)

The following are documented as a roadmap and intentionally **deferred** so this
layer stays focused and A2A-conformant:

* **Ray.io distributed execution** — placement groups tying compute-heavy
  agents to dedicated Graphics Processing Unit (GPU) nodes; object-spill
  policies. (See the Ray Core / Bridged Hybrid analysis.)
* **Kubernetes plane architecture** — control/data plane split for the agent
  mesh.
* **ACES Agent Definition Framework (ADF), TaskGroup, and Task** — the richer
  execution-graph objects above WorkspaceState/Response.

These sit on top of the message + card layer built here; none of them change the
A2A conformance surface, which is why they can wait.
