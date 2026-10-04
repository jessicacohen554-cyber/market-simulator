"""MISO uc-params spec: the CAMPD state footprint the derive scans.

Scoping only — the derivation is the generic plant-basis path in the package
__init__ (CAMPD unit-level gross load / heat input, pooled 2023-2025).
The footprint is :data:`market_sim.data.campd.ISO_STATES["MISO"]`, the same
list the outage derivation uses; a state whose extract is absent is skipped,
so coverage widens as extracts land. Consumed by
market_sim.model.uc.params when unit_commitment_milp is armed.
"""

from __future__ import annotations

from market_sim.data.campd import ISO_STATES

from . import IsoSpec, register

SPEC = register(IsoSpec(iso="MISO", campd_states=tuple(ISO_STATES["MISO"])))
