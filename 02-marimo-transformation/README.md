# Section 2 — Marimo Transformation

The standards-layer foundation that turns the A2A demo into a governed system,
plus the Marimo notebooks and teaching decks that present it.

## What this section is

The upstream labs work, but they hardcode model strings, read configuration ad
hoc, and express agent relationships by convention. This section replaces that
with one shared package, `a2a_labs`, that every lab imports — so a constraint is
defined once and inherited everywhere. A typo fails at import, not at runtime; a
provider swap is one environment variable; a wrong vendor/model pair cannot be
constructed.

## The foundation package: `src/a2a_labs/`

| Module | Responsibility |
|---|---|
| `enums.py` | Closed sets: `AgentRole`, `AgentPort`, `Provider`, `TransportMode`. Standard-library `StrEnum`/`IntEnum` with `@unique`/`@verify`. Each Enum owns its derived facts (e.g. `AgentRole.port`, `AgentRole.default_url()`); one `DEFAULT_HOST` constant. |
| `vendors.py` | The original `VendorModel` Enum + `VendorModelSelection` cascade — kept as the "before" of the registry refactor. |
| `registry.py` | `MODEL_REGISTRY` parsed directly from `fabric -L` (Vendor → models). Regenerate by re-pasting a fresh dump. Exposes the ready-built `MODELS` cascade. |
| `cascade.py` | The WORM, Enum-keyed `Cascade` governance registry and `CascadeKey`. Validates parent→child pairs; built once at import, immutable, reused across labs. Not limited to (vendor, model). |
| `messages.py` | `ModelMessage` — the frozen Pydantic wire object for a selected (vendor, model) pair; composed `fabric_id`/`litellm`, `to_wire`/`from_wire`. |
| `config.py` | Pydantic V2 `Settings`: holds configuration and validates credentials; delegates composition to the Enums (`litellm_model`, `url_for`, `port_for`). |
| `workspace.py` | `WorkspaceState` / `WorkspaceResponseObject` — the WORM request/response envelope with BLAKE3 correlation. |
| `a2a_bridge.py` | Governed A2A Agent Card builder and the Fully Qualified Skill Name (FQSN) registry; state↔message↔artifact adapters. |
| `locking.py` | Pessimistic (`@requires`) vs optimistic, serially-reentrant chain execution. |
| `orchestrator.py` | Three agent-launch tiers: manual commands, subprocess manager, async supervisor. |
| `decorators.py` | `@lab_step`, `@async_lab_step`, `@requires`. |

### Design principles (enforced, not aspirational)
- **No hardcoding where an Enum or constant exists.** A value that is already an
  Enum member is referenced, never re-typed.
- **One source of truth, navigated — never copied.** Derived facts are computed
  from the one structure, not duplicated.
- **Pydantic only at the boundary.** Static catalogs are plain data; Pydantic
  validates where input actually enters.
- **WORM governance.** Registries are write-once, immutable, reused many times.
- **KISS = Keep It Simple and Standard.** Standard-library mechanisms over
  hand-rolled equivalents.

## `marimo/`
One notebook per lab (`lab0_launcher` … `lab8_beeai_requirement`), replacing the
Jupyter originals. The ASGI agent servers run as separate uvicorn processes; the
notebooks are clients, not hosts.

## `docs/`
Architecture overview, standards-and-Marimo notes, and the A2A compliance /
flexibility analysis.

## `slides/`
Teaching decks. `Lab1_Darwinian_Reorder.pptx` is the canonical Lab 1 deck — it
presents each foundation object as an adaptation selected by a real failure
pressure, with the code/blackbox block reordered to follow the "why we forked"
segue and wired with internal navigation links.

## Completion gate
Section 3 (Three Tier Architecture) stays parked until this section is complete
and validated. "Complete" means: the foundation package stable, all eight Marimo
labs runnable against live agents, and the A2A compliance notes finalized.
