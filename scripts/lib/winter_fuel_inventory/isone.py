"""ISO-NE winter-fuel-inventory spec (New England oil-security fleet).

ISO New England's footprint is exactly the six New England states, so the
per-plant EIA-860 oil-limb / firing-rate derivation filters on
``{ME, NH, VT, MA, RI, CT}`` (no partial-state ambiguity — unlike PJM/MISO,
which would need a plant-level membership resolver). The fleet/system/program
figures — start-of-winter oil inventory, re-supply delivery-rate caps, tank
capacities, and winter-reliability / retention program unit lists — are
hand-curated into ``data/raw/winter-fuel-inventory/isone/isone.csv`` from the
public ISO-NE studies (Operational Fuel-Security Analysis 2018; 21st-Century
Energy Security / Energy Security Improvements filings) and program filings
(Mystic cost-of-service agreement; ISO-NE Winter Reliability Program), each row
carrying its exact citation.

The default parser (:func:`scripts.lib.winter_fuel_inventory.parse_default`)
unions the EIA-860 derivation with that CSV, so ISO-NE needs no custom hook.

EIA-860 vintage: the committed top-level snapshot under ``data/raw/eia-860``
(data year 2024; proposed units extend to 2025).
"""

from __future__ import annotations

from . import IsoSpec, register

# ISO-NE footprint = the six New England states (exact, no partial states).
NEW_ENGLAND_STATES: tuple[str, ...] = ("ME", "NH", "VT", "MA", "RI", "CT")

# Label for the committed EIA-860 snapshot used by the per-plant derivation.
EIA_VINTAGE: str = "2024"

SPEC = register(
    IsoSpec(
        iso="ISONE",
        eia_states=NEW_ENGLAND_STATES,
        eia_vintage=EIA_VINTAGE,
    )
)
