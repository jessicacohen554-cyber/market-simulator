"""NYISO confirmed-retirement spec.

Binding instrument: a **Generator Deactivation Notice** completed per the OATT
deactivation process, plus state (DEC/PSC) orders (``rto_deactivation`` /
``regulatory_order``). The Gold Book retirement table is an announced-grade
cross-check only. Public source to re-query: NYISO deactivation-notices posting.
Researched 2026-07-05: the registry CSV holds zero rows by design, not by
omission — every forward-looking completed deactivation notice found (Far
Rockaway, Gowanus/Narrows, Pinelawn) has since been reversed by a NYISO
reliability determination (returned to service or withdrawn). See
``data/raw/confirmed-retirements/nyiso.csv`` for the full research record.
"""

from __future__ import annotations

from . import IsoSpec, register

_CLASS_ALIASES = {"deactivation": "rto_deactivation", "dec": "regulatory_order"}

SPEC = register(
    IsoSpec(
        iso="NYISO",
        class_aliases=_CLASS_ALIASES,
        source_note="NYISO deactivation notices; NY DEC/PSC orders.",
    )
)
