"""NYISO confirmed-retirement spec.

Binding instrument: a **Generator Deactivation Notice** completed per the OATT
deactivation process, plus state (DEC/PSC) orders (``rto_deactivation`` /
``regulatory_order``). The Gold Book retirement table is an announced-grade
cross-check only. Public source to re-query: NYISO deactivation-notices posting.
The registry CSV lands as DATA NEEDED until the forward list is itemized.
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
