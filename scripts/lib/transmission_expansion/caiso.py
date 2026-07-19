"""CAISO transmission-expansion spec.

Binding instruments: CAISO Board of Governors approval of a Transmission Plan
(TPP) portfolio (which carries TAC cost allocation) plus CPUC CPCN permits for
utility-committed work; merchant/interregional HVDC with signed interconnection
agreements. Public sources to re-query: CAISO transmission-plan pages, CPUC
dockets. Most TPP work is collector/intra-zonal at this model's grain
(``intra_zonal`` rows); WECC-side merchant lines (TransWest, SunZia) change
supply INTO the ``WECC_import`` node, not the intertie ratings, so they are
``import_tranche`` rows (recorded, dispatch-inert in V1).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="CAISO",
        source_note=(
            "CAISO board-approved TPP portfolios + CPUC CPCNs; merchant "
            "WECC HVDC with executed agreements."
        ),
    )
)
