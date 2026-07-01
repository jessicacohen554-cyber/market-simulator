"""MISO capacity-deliverability spec (LRR / LCR / CIL / CEL / ZIA / PRMR by LRZ).

MISO publishes, per Local Resource Zone (LRZ 1-10) and **season** (unlike the
other ISOs, MISO has been seasonal since Planning Year 2023-24: summer / fall /
winter / spring each get their own values), the Local Reliability Requirement
(LRR, an MW quantity that also carries a per-unit-of-peak ratio), Local
Clearing Requirement (LCR), Capacity Import Limit (CIL), Capacity Export Limit
(CEL), and Zonal Import Ability (ZIA). System/subregional rows (RTO, North,
South) carry the Planning Reserve Margin Requirement (PRMR) instead of a
zonal LRR. Sources: the annual LOLE Study Report (CIL/CEL/ZIA/LRR) and the
Planning Resource Auction (PRA) Results posting (as-cleared LCR/CIL/ZIA/CEL/
PRMR), both per delivery year.

Native -> canonical metric map:
    lrr  -> requirement                  (carries value_mw + value_pu)
    lcr  -> local_clearing_requirement
    cil  -> import_limit
    cel  -> export_limit
    zia  -> import_ability
    prmr -> system_requirement

Delivery years are Planning Years labelled "2023/2024" (June 1 - May 31).
LRZ area rows use area_type "lrz"; RTO/North/South system rows use "rto".
"""

from __future__ import annotations

from . import IsoSpec, register

# LRZ 1-10 plus the system/subregional rows (RTO, North, South) MISO reports
# PRMR against. Documentary constant, mirrors pjm.EXPECTED_AREAS.
EXPECTED_AREAS: tuple[str, ...] = (
    "LRZ 1",
    "LRZ 2",
    "LRZ 3",
    "LRZ 4",
    "LRZ 5",
    "LRZ 6",
    "LRZ 7",
    "LRZ 8",
    "LRZ 9",
    "LRZ 10",
    "RTO",
    "North",
    "South",
)

# Native MISO labels -> canonical metric vocabulary.
_METRIC_ALIASES = {
    "lrr": "requirement",
    "local_reliability_requirement": "requirement",
    "lcr": "local_clearing_requirement",
    "local_clearing_requirement": "local_clearing_requirement",
    "cil": "import_limit",
    "import_limit": "import_limit",
    "cel": "export_limit",
    "export_limit": "export_limit",
    "zia": "import_ability",
    "zonal_import_ability": "import_ability",
    "import_ability": "import_ability",
    "prmr": "system_requirement",
    "system_requirement": "system_requirement",
}

SPEC = register(
    IsoSpec(
        iso="MISO",
        default_area_type="lrz",
        metric_aliases=_METRIC_ALIASES,
        delivery_year_kind="planning",
    )
)
