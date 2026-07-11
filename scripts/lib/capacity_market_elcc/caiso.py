"""CAISO capacity-market-elcc spec.

CAISO/CPUC's Net Qualifying Capacity (NQC) methodology, refined via CPUC
Resource Adequacy proceedings and E3-authored ELCC studies, for wind/solar/
storage accreditation.
"""

from __future__ import annotations

from . import IsoSpec, register

_RESOURCE_CLASS_ALIASES = {
    "battery_4hr": "storage_4hr",
}

SPEC = register(
    IsoSpec(
        iso="CAISO",
        resource_class_aliases=_RESOURCE_CLASS_ALIASES,
    )
)
