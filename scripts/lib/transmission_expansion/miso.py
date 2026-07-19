"""MISO transmission-expansion spec.

Binding instruments: MISO Board of Directors approval of an MTEP/LRTP tranche
(Tranche 1 approved 2022-07-25; Tranche 2.1 approved 2024-12-12) — approval
carries cost allocation, so tranche membership is the committed set. Public
sources to re-query: MISO MTEP reports and LRTP dashboard. Most LRTP segments
are intra-zonal at this model's six-zone (LRZ-union) grain or shift the
LOLE-published CIL/CEL rather than a bilateral link limit, so rows here are
mostly ``intra_zonal``/``interface`` with reconciled deltas only where MISO
publishes an inter-zone transfer-capability increase.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="MISO",
        source_note=(
            "MISO board-approved LRTP tranches (MTEP appendices) + JOA RDT "
            "amendments; LRTP project dashboard."
        ),
    )
)
