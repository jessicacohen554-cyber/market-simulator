"""NYISO capacity-market-demand-curve spec.

NYISO's Installed Capacity (ICAP) market prices against sloped Demand Curves,
reset triennially (the "Demand Curve Reset" / DCR study), published separately
for the system (NYCA) and each locality — NYC (Zone J), Long Island (Zone K),
and the G-J Locality (Lower Hudson Valley). ``area`` therefore carries a value
(NYCA/NYC/LI/G-J) unlike PJM's single RTO-wide curve.

Native -> canonical metric map: ``icap_demand_curve_point`` -> ``curve_point``,
``reference_point_price`` -> ``net_cone`` (NYISO's demand-curve reference
point is its Net-CONE analog).
"""

from __future__ import annotations

from . import IsoSpec, register

_METRIC_ALIASES = {
    "icap_demand_curve_point": "curve_point",
    "reference_point_price": "net_cone",
}

SPEC = register(
    IsoSpec(
        iso="NYISO",
        metric_aliases=_METRIC_ALIASES,
        delivery_year_kind="planning",
    )
)
