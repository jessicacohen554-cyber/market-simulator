"""ISO-NE capacity-deliverability spec (LSR / MCL / interface limits by zone).

ISO-NE publishes the Local Sourcing Requirement (LSR, import zones) and Maximum
Capacity Limit (MCL, export zones) in the FCA Informational Filing (Section
IV.A.3), filed ~November each year, roughly three years ahead of the Capacity
Commitment Period.  Transmission interface import limits used to derive the
LSR/MCL appear in Section IV.A.1.  The system Installed Capacity Requirement
(ICR) and net-ICR (after HQICCs) are in the same filing's transmittal letter.

Native -> canonical metric map:
    lsr  -> requirement        (import-constrained: SENE)
    mcl  -> export_limit       (export-constrained: NNE, Maine)
    icr  -> system_requirement (net-ICR, area = RestOfSystem)

Delivery years are Capacity Commitment Periods labelled "2024/2025"
(June 1 - May 31).  FCA N → CCP (N+9)/(N+10), e.g. FCA 14 → 2023/2024.

Capacity Zones (FCA 14-16, four-zone structure):
    SENE        Southeast New England (SEMASS+RI+NEMA/Boston), import-constrained
    NNE         Northern New England (NH+VT+ME), export-constrained
    Maine       nested within NNE, export-constrained
    RestOfPool  CT + Western/Central MA, unconstrained (no LSR/MCL)
"""

from __future__ import annotations

from . import IsoSpec, register

EXPECTED_AREAS: tuple[str, ...] = (
    "SENE",
    "NNE",
    "Maine",
    "RestOfPool",
    "RestOfSystem",
)

_METRIC_ALIASES = {
    "lsr": "requirement",
    "mcl": "export_limit",
    "icr": "system_requirement",
    "net_icr": "system_requirement",
    "net-icr": "system_requirement",
}

SPEC = register(
    IsoSpec(
        iso="ISONE",
        default_area_type="capacity_zone",
        metric_aliases=_METRIC_ALIASES,
        delivery_year_kind="planning",
    )
)
