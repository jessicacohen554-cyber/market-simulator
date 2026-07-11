"""PJM capacity-market-elcc spec (reference ISO implementation).

PJM publishes annual "ELCC Class Ratings" (wind, solar, storage-by-duration,
hybrid) used to convert nameplate MW to UCAP for capacity accreditation. These
are typically a single current-fleet class-average rating per delivery year,
not a penetration-indexed curve — ``penetration_pct``/``penetration_unit`` are
left null unless a specific study publishes the marginal curve (see the raw
README for what landed).
"""

from __future__ import annotations

from . import IsoSpec, register

_RESOURCE_CLASS_ALIASES = {
    "battery_4hr": "storage_4hr",
    "battery_2hr": "storage_2hr",
    "onshore wind": "wind",
    "offshore wind": "wind_offshore",
    "fixed-tilt solar": "solar",
    "tracking solar": "solar",
    "solar fixed panel": "solar",
    "solar tracking panel": "solar",
    "4-hr storage": "storage_4hr",
    "6-hr storage": "storage_6hr",
    "8-hr storage": "storage_8hr",
    "10-hr storage": "storage_10hr",
    "landfill intermittent": "other",
    "landfill gas intermittent": "other",
    "hydro intermittent": "other",
    "hydro with non-pumped storage": "other",
    "demand resource": "other",
    "solar hybrid open loop - storage component": "hybrid_solar_storage",
    "solar hybrid closed loop - storage component": "hybrid_solar_storage",
}

SPEC = register(
    IsoSpec(
        iso="PJM",
        resource_class_aliases=_RESOURCE_CLASS_ALIASES,
    )
)
