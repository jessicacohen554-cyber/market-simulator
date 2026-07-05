"""CAISO confirmed-retirement spec.

CAISO has no RTO deactivation regime, so the binding instruments are state
orders: SWRCB once-through-cooling (OTC) compliance dates and CPUC/CEC decisions
(``statute`` / ``regulatory_order``), e.g. SB 846's Diablo Canyon schedule.
Diablo Canyon's SB 846 supersession of its earlier 2016-settlement retirement
date is the worked ``superseded`` example (a compliance date extended by a
later legislative/regulatory action). Public source to re-query: the SWRCB OTC
compliance-schedule table and CPUC/CEC dockets. Seeded 2026-07-05: AES
Alamitos 3-5, AES Huntington Beach 2, Ormond Beach 1-2 (OTC), Diablo Canyon 1-2
(SB 846) — see ``data/raw/confirmed-retirements/caiso.csv``.
"""

from __future__ import annotations

from . import IsoSpec, register

_CLASS_ALIASES = {
    "otc": "regulatory_order",
    "swrcb": "regulatory_order",
    "cpuc": "regulatory_order",
    "sb846": "statute",
}

SPEC = register(
    IsoSpec(
        iso="CAISO",
        class_aliases=_CLASS_ALIASES,
        source_note="SWRCB OTC compliance schedule; CPUC/CEC dockets; SB 846.",
    )
)
