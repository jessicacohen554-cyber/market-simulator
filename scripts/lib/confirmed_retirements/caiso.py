"""CAISO confirmed-retirement spec.

CAISO has no RTO deactivation regime, so the binding instruments are state
orders: SWRCB once-through-cooling (OTC) compliance dates and CPUC/CEC decisions
(``statute`` / ``regulatory_order``), e.g. SB 846's Diablo Canyon schedule. The
OTC amendment history is the worked ``superseded`` example (a compliance date
extended by a later board action). Public source to re-query: the SWRCB OTC
compliance-schedule table and CPUC/CEC dockets. The registry CSV lands as DATA
NEEDED until the OTC/Diablo rows are itemized and verified against current dates.
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
