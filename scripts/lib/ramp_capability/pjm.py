"""PJM ramp-capability spec (reference ISO implementation).

Scoping only — the derivation is the generic path in the package
``__init__`` (EIA-860 fast-start + CAMPD CEMS 1-hour envelope). PJM's fleet
plants are the EIA-860 balancing-authority code ``PJM``; the CAMPD extracts
scanned are the full PJM physical footprint, the same state list
``market_sim.data.campd.ISO_STATES["PJM"]`` the outage derivation uses (a
state whose extract is absent is skipped, so coverage widens as extracts
land).

Consumed by the PJM per-generator reserve co-optimization
(``pjm_reserve_pergen``): the measured fast-start / envelope quantities bound
FleetArrays.ramp10, the 10-minute reserve-deliverability cap
(docs/multi-iso/pjm-reserve-ordc.md Phase 2).
"""

from __future__ import annotations

from . import IsoSpec, register

# Same footprint as market_sim.data.campd.ISO_STATES["PJM"] (kept literal so
# scripts/lib stays importable without the model package on path).
_PJM_STATES: tuple[str, ...] = (
    "PA",
    "NJ",
    "MD",
    "DE",
    "IL",
    "OH",
    "IN",
    "KY",
    "WV",
    "VA",
    "NC",
    "TN",
    "MI",
    "DC",
)

SPEC = register(IsoSpec(iso="PJM", ba_code="PJM", campd_states=_PJM_STATES))
