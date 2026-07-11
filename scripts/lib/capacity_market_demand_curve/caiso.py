"""CAISO capacity-market-demand-curve spec (documented low-fidelity proxy).

CAISO has no centralized capacity auction or sloped demand curve — Resource
Adequacy (RA) is procured bilaterally between load-serving entities and
resources under CPUC oversight. Per the audit plan §3.2, CAISO keeps the
model's current fixed net-CONE proxy but re-cites it to two published
observables instead of an un-cited estimate:

- ``soft_offer_cap``: CAISO's Capacity Procurement Mechanism (CPM) soft-offer
  price cap (tariff-published backstop price ceiling).
- ``ra_report_price``: CPUC's annual Resource Adequacy Report observed
  bilateral RA contract price, where published.

Both are scalar metrics (no ``curve_point`` rows — there is no curve).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="CAISO",
        metric_aliases={},
        delivery_year_kind="calendar",
    )
)
