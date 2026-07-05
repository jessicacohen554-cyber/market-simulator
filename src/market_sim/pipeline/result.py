"""Return contract for the shared per-year solve core (``YearSolveResult``).

Placeholder introduced in Stage 1 so the type exists and the contract is
documented; **nothing constructs or consumes it yet**. It is populated and
returned by the shared solve core extracted in **Stages 3-4** (plan §5-§6):

- Stage 3 extracts the P0/P1 energy solve → ``pipeline.solve.run_energy_solve``,
  which returns the P1 ``result`` (clearing prices), the intermediate ``result_p1``
  bookkeeping, and the solve ``context``.
- Stage 4 extracts the P2 commitment screen → ``pipeline.commitment.run_commitment_pass``,
  which fills ``p2_state``.

Both orchestrators (``runner.py`` forecast, ``run_calibration.py`` backcast) will
consume this single return type, replacing today's ad-hoc tuples. Fields are
typed loosely here (``Any`` for the not-yet-extracted solve internals) and will
be tightened when the producing code lands in Stages 3-4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from market_sim.model.dispatch import DispatchResult


@dataclass
class YearSolveResult:
    """The shared solve core's per-year output (populated in Stages 3-4).

    Attributes:
        result: The authoritative P1 (bid-cost) dispatch/price result — the
            production clearing solve every keeper is scored on.
        result_p1: Intermediate P1 solve bookkeeping (markup/warm-start detail),
            retained for diagnostics; may coincide with ``result`` depending on
            how Stage 3 factors the P0→P1 handoff.
        context: The solve context (fleet/zone/topology bindings and any state
            the post-solve overlays and next-year evolution read).
        p2_state: Optional P2 commitment-screen state, ``None`` when the
            commitment pass did not run (the default; P2 is opt-in per CLAUDE.md).
    """

    result: "DispatchResult"
    result_p1: Any = None
    context: Any = None
    p2_state: Any = None
