"""MISO ramp-capability spec.

Scoping only — the derivation is the generic path in the package
``__init__``. MISO's fleet plants are the EIA-860 balancing-authority code
``MISO``; the CAMPD extracts scanned are the MISO physical footprint, the
same state list ``market_sim.data.campd.ISO_STATES["MISO"]`` the outage
derivation uses (states overlap PJM/ERCOT — the BA-code fleet scoping keeps
each ISO's rows to its own plants).

Consumed by the MISO per-asset reserve co-optimization
(``miso_reserve_pergen``) as the measured upgrade path for its
class-fraction ramp caps (docs/multi-iso/miso-reserve-coopt.md).
"""

from __future__ import annotations

from . import IsoSpec, register

# Same footprint as market_sim.data.campd.ISO_STATES["MISO"] (kept literal so
# scripts/lib stays importable without the model package on path).
_MISO_STATES: tuple[str, ...] = (
    "AR",
    "IA",
    "IL",
    "IN",
    "KY",
    "LA",
    "MI",
    "MN",
    "MO",
    "MS",
    "ND",
    "SD",
    "TX",
    "WI",
)

SPEC = register(IsoSpec(iso="MISO", ba_code="MISO", campd_states=_MISO_STATES))
