"""CAISO ramp-capability spec.

Scoping only — the derivation is the generic path in the package
``__init__`` (EIA-860 fast-start + CAMPD CEMS 1-hour envelope). CAISO's fleet
plants are the EIA-860 balancing-authority code ``CISO``; the CAMPD extracts
scanned are the CAISO physical footprint, the same state list
``market_sim.data.campd.ISO_STATES["CAISO"]`` the outage derivation uses
(California only — a state whose extract is absent is skipped, so coverage
widens as extracts land).

Consumed by the CAISO per-generator reserve co-optimization
(``config.reserve_config._caiso_design``, L-10): the measured fast-start /
envelope quantities bound ``FleetArrays.ramp10``, the 10-minute
reserve-deliverability cap that makes the published §27.1.2.3.5 scarcity
demand curve bite (without it the zone-aggregate requirement clears from idle
CC headroom at zero opportunity cost — the MISO lesson, issue #1492).
"""

from __future__ import annotations

from . import IsoSpec, register

# Same footprint as market_sim.data.campd.ISO_STATES["CAISO"] (kept literal so
# scripts/lib stays importable without the model package on path). CAISO's
# metered footprint is California; out-of-state imports (WECC) carry no CEMS
# rows and are represented by the model's WECC_import node, not a fleet plant.
_CAISO_STATES: tuple[str, ...] = ("CA",)

SPEC = register(IsoSpec(iso="CAISO", ba_code="CISO", campd_states=_CAISO_STATES))
