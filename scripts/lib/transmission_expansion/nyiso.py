"""NYISO transmission-expansion spec.

Binding instruments: NYPSC orders / Tier 4 contracts (CHPE) and NYISO
public-policy-transmission selections with executed development agreements
(Propel NY). Public sources to re-query: NYISO planning (PPTN) pages, DPS
dockets. The Central-East static (2,850 MW) is already the post-AC-Transmission
(Segment A/B, in service Dec 2023) measured 2024-25 mean, so the AC
Transmission project must NOT appear as a delta; CHPE is an HQ→NYC HVDC supply
line — the model has no NYISO import node, so it is an ``import_tranche`` row
(recorded, dispatch-inert in V1).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="NYISO",
        source_note=(
            "NYPSC Tier 4 contracts (CHPE) + NYISO public-policy selections "
            "with executed development agreements (Propel NY)."
        ),
    )
)
