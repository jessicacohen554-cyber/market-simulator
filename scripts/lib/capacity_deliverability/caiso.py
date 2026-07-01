"""CAISO capacity-deliverability spec.

CAISO publishes two locational resource-adequacy families: Local Capacity
Requirements (LCR, from the annual Local Capacity Technical Report) per Local
Capacity Area, and Maximum Import Capability (MIC, from the annual RA Import
Capability filing) per import branch group, plus a system-wide Planning
Reserve Margin (PRM) requirement row. Delivery years are calendar years
(e.g. ``"2023"``).

Unlike PJM, ``area_type`` varies *within* the CAISO CSV rather than defaulting
uniformly: LCR rows carry ``local_area``, MIC rows carry ``branch_group``, and
the system-wide PRM row carries ``rto`` — the retrieval CSV stamps
``area_type`` explicitly per row, so :func:`~scripts.lib.capacity_deliverability.parse_unified_csv`
only falls back to ``default_area_type`` if a row ever left it blank.

The CSV already uses canonical metric names (``requirement`` /
``import_limit`` / ``system_requirement``), so no metric-alias map is needed.
"""

from __future__ import annotations

from . import IsoSpec, register

# Local Capacity Areas CAISO lists in the Local Capacity Technical Report.
# Documentary constant — the parser does not require areas to be in this set,
# but it records the expected vocabulary for reviewers and tests.
LOCAL_AREAS: tuple[str, ...] = (
    "Humboldt",
    "North Coast/North Bay",
    "Sierra",
    "Stockton",
    "Greater Bay",
    "Greater Fresno",
    "Kern",
    "Big Creek/Ventura",
    "LA Basin",
    "San Diego/Imperial Valley",
)

# The CSV already carries canonical metric labels; no native -> canonical
# remapping is required.
_METRIC_ALIASES: dict[str, str] = {}

SPEC = register(
    IsoSpec(
        iso="CAISO",
        default_area_type="local_area",
        metric_aliases=_METRIC_ALIASES,
        delivery_year_kind="calendar",
    )
)
