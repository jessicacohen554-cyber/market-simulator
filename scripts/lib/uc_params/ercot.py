"""ERCOT uc-params spec: the CAMPD state footprint the derive scans.

Scoping only — the derivation is the generic plant-basis path in the package
__init__ (CAMPD unit-level gross load / heat input, pooled 2023-2025).
The footprint is :data:`market_sim.data.campd.ISO_STATES["ERCOT"]`
plus :data:`EXTRA_FACILITIES`, the same
list the outage derivation uses; a state whose extract is absent is skipped,
so coverage widens as extracts land. Consumed by
market_sim.model.uc.params when unit_commitment_milp is armed.
"""

from __future__ import annotations

from market_sim.data.campd import ISO_STATES

from . import IsoSpec, register

#: ERCOT-fleet facilities whose CEMS files under a state outside the TX
#: footprint, read from that state's extract alone (the rest of the state
#: stays out, so the class-fallback rows pool ERCOT plants only). Kiamichi
#: Energy Facility (EIA/CAMD 55501, 183.9 MW CC) sits in Oklahoma with
#: balancing authority ERCO (EIA-860M August 2026 operating file).
EXTRA_FACILITIES: tuple[tuple[str, int], ...] = (("OK", 55501),)

SPEC = register(
    IsoSpec(
        iso="ERCOT",
        campd_states=tuple(ISO_STATES["ERCOT"]),
        extra_facilities=EXTRA_FACILITIES,
    )
)
