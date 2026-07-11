"""MISO capacity-market-demand-curve spec.

MISO's Planning Resource Auction (PRA) priced against a flat VOLL-based
demand curve through Planning Year 2024-25; from PY2025-26 it uses a seasonal,
reliability-based demand curve with a distinct Cost of New Entry (CONE) and
curve shape per season (summer/fall/winter/spring) — the only ISO in this
registry whose ``season`` column is populated for demand-curve rows (see the
schema header). ``area`` carries the Local Resource Zone (LRZ 1-10) when MISO
publishes zonal curves, else null for a MISO-wide row.

Native -> canonical metric map: ``cone`` -> ``net_cone``, ``rbdc_point`` ->
``curve_point`` (Reliability-Based Demand Curve).
"""

from __future__ import annotations

from . import IsoSpec, register

_METRIC_ALIASES = {
    "cone": "net_cone",
    "rbdc_point": "curve_point",
}

SPEC = register(
    IsoSpec(
        iso="MISO",
        metric_aliases=_METRIC_ALIASES,
        delivery_year_kind="planning",
    )
)
