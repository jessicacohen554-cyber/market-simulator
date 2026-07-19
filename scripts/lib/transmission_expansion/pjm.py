"""PJM transmission-expansion spec.

Binding instruments: PJM Board approval of RTEP baseline/window projects with
executed Designated Entity Agreements (e.g. the 2022 RTEP Window 3 portfolio
approved 2023-12; the 2024 window selections approved 2025-02). Public sources
to re-query: PJM RTEP updates and Transmission Construction status pages. Base
statics are the 2024 transfer-limit postings, so only post-2024 in-service work
is additive; most RTEP work lacks a published interface-TTC uplift and lands as
``reconciled``/``ambiguous`` or ``intra_zonal`` rows.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="PJM",
        source_note=(
            "PJM board-approved RTEP baseline/window portfolios with executed "
            "Designated Entity Agreements."
        ),
    )
)
