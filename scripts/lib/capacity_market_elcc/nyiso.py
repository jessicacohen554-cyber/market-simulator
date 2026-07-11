"""NYISO capacity-market-elcc spec.

NYISO's ICAP/UCAP conversion factors for intermittent and limited-duration
resources, from the Capacity Accreditation Task Force (CATF) and related
filings.
"""

from __future__ import annotations

from . import IsoSpec, register

_RESOURCE_CLASS_ALIASES = {
    "battery_4hr": "storage_4hr",
    "land_based_wind": "wind",
    "offshore_wind": "wind_offshore",
}

SPEC = register(
    IsoSpec(
        iso="NYISO",
        resource_class_aliases=_RESOURCE_CLASS_ALIASES,
    )
)
