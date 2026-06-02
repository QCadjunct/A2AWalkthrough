"""Two execution strategies, told as a database-locking analogy.

When a chain calls several agents, there are two ways to handle the risk that a
prerequisite agent is down — and they map exactly onto the two classic database
concurrency-control strategies.

PESSIMISTIC LOCKING  (run_chain)
    Acquire/verify everything up front. The @requires decorator probes every
    prerequisite Agent Card BEFORE the body runs; if any is down, abort
    immediately. Like ``SELECT ... FOR UPDATE``: you lock the resources before
    touching them, so you never start work you cannot finish. Cost: a down
    agent blocks the whole chain even if this particular request never needed
    it.

OPTIMISTIC LOCKING  (run_serially_reentrant)
    Assume success, proceed, and handle a conflict only if it actually occurs —
    then safely retry. Like a version-checked ``UPDATE ... WHERE version = n``:
    you do the work and reconcile on conflict. Each step is idempotent and the
    method is *serially reentrant* — re-invoking it resumes from where it left
    off, skipping already-completed steps, because progress is recorded in the
    WORM WorkspaceResponseObject chain (matched by correlation_id). Cost: more
    bookkeeping; benefit: a transient outage on an unused agent never blocks
    the request, and a half-finished chain can be safely resumed.

Acronyms: A2A - Agent-to-Agent; WORM - Write Once Reuse Many; URL - Uniform
Resource Locator.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx

from a2a_labs.decorators import requires
from a2a_labs.workspace import (
    ResponseStatus,
    WorkspaceResponseObject,
    WorkspaceState,
)


def _card_reachable(url: str) -> bool:
    card = url.rstrip("/") + "/.well-known/agent-card.json"
    try:
        return httpx.get(card, timeout=2.0).status_code == 200
    except Exception:  # noqa: BLE001
        return False


# ===========================================================================
# PESSIMISTIC — lock first, then run (the existing model)
# ===========================================================================
def make_pessimistic_chain(
    step_urls: list[str],
    step_fn: Callable[[WorkspaceState], WorkspaceResponseObject],
) -> Callable[[WorkspaceState], WorkspaceResponseObject]:
    """Build a chain runner guarded by @requires — pessimistic locking.

    Every prerequisite is verified before any step runs. If one is down, the
    whole chain aborts up front with a named error. Equivalent to taking all the
    locks before doing any work.
    """

    @requires(*step_urls)
    def run_chain(request: WorkspaceState) -> WorkspaceResponseObject:
        # All prerequisites confirmed up front by @requires.
        return step_fn(request)

    return run_chain


# ===========================================================================
# OPTIMISTIC — run, reconcile on conflict, resume on re-entry
# ===========================================================================
@dataclass
class ReentrantChainState:
    """Records progress so the chain can be safely re-entered.

    Maps each step's prerequisite URL to the WorkspaceResponseObject it
    produced. On re-entry, completed steps (those with a terminal response whose
    correlation_id matches) are skipped — this is what makes the method serially
    reentrant rather than restart-from-scratch.
    """

    completed: dict[str, WorkspaceResponseObject] = field(default_factory=dict)

    def is_done(self, url: str, request: WorkspaceState) -> bool:
        resp = self.completed.get(url)
        return bool(
            resp
            and resp.is_terminal
            and resp.correlation_id == request.blake3_pair_hash
        )


def run_serially_reentrant(
    request: WorkspaceState,
    steps: list[tuple[str, Callable[[WorkspaceState], WorkspaceResponseObject]]],
    state: ReentrantChainState | None = None,
    max_passes: int = 3,
) -> tuple[WorkspaceResponseObject | None, ReentrantChainState]:
    """Optimistic, serially reentrant chain execution.

    Proceeds without an up-front lock. For each (prerequisite_url, step):
      * if already completed for this request (state says so) -> skip;
      * else attempt the step; if its prerequisite is unreachable, record a
        non-terminal NEED_INPUT marker and move on instead of aborting.
    Re-invoking with the same ``state`` resumes: completed steps are skipped and
    only the still-pending ones are retried — up to ``max_passes``.

    Returns the last terminal response and the (possibly partial) state, so the
    caller can re-enter later to finish a chain that was blocked transiently.
    """
    state = state or ReentrantChainState()
    last_terminal: WorkspaceResponseObject | None = None

    for _ in range(max_passes):
        pending = False
        for url, step in steps:
            if state.is_done(url, request):
                continue  # serial re-entry: skip completed work
            if not _card_reachable(url):
                # Optimistic: do not abort the whole chain. Mark and continue;
                # a later re-entry can complete it once the agent is back.
                state.completed[url] = request.respond(
                    result=f"prerequisite {url} unavailable; will retry",
                    status=ResponseStatus.NEED_INPUT,
                )
                pending = True
                continue
            resp = step(request)
            state.completed[url] = resp
            if resp.is_terminal:
                last_terminal = resp
        if not pending:
            break  # everything completed; no need for another pass

    return last_terminal, state
