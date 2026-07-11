"""MISO capacity-market-elcc spec.

MISO has published the most detailed public wind/solar marginal-ELCC-vs-
penetration studies of any ISO in this registry (Accreditation Reform /
wind & solar capacity-credit reports) — the strongest candidate for a genuine
multi-point penetration curve; see the raw README for per-zone coverage.
"""

from __future__ import annotations

from . import IsoSpec, register

_RESOURCE_CLASS_ALIASES = {
    "battery_4hr": "storage_4hr",
}

SPEC = register(
    IsoSpec(
        iso="MISO",
        resource_class_aliases=_RESOURCE_CLASS_ALIASES,
    )
)
