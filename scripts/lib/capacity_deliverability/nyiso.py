"""NYISO capacity-deliverability spec.

NYISO publishes locational capacity requirements (LCR) for its In-City (NYC),
Long Island, and G-J locality zones as both an ICAP MW requirement and an LCR%
(``value_mw`` and ``value_pu`` on the same row), in the annual "Locational
Minimum Installed Capacity Requirements" report. The companion "Locality Bulk
Power Transmission Capability Report" publishes each locality's deliverable
import limit (``import_limit``, MW only). NYCA is the statewide Installed
Reserve Margin (IRM): an ``rto``-area-type row carrying ``value_pu`` only
(``system_requirement``, e.g. 20.0% -> 0.200). Delivery years are labelled
"2025/2026" (May 1 - April 30).

``data/raw/capacity-deliverability/nyiso/nyiso.csv`` is retrieved already in
canonical unified form (metric/area_type columns use the canonical
vocabulary), so no native-label alias map is needed and this module relies
entirely on the shared :func:`~scripts.lib.capacity_deliverability.parse_unified_csv`
reader.
"""

from __future__ import annotations

from . import IsoSpec, register

# Localities NYISO lists in its LCR reports, plus the statewide NYCA row.
# Documentary constant — the parser does not require areas to be in this set,
# but it records the expected vocabulary for reviewers and tests.
EXPECTED_AREAS: tuple[str, ...] = ("NYC", "Long Island", "G-J", "NYCA")

# The raw CSV already uses canonical metric/area_type labels; no mapping needed.
_METRIC_ALIASES: dict[str, str] = {}

SPEC = register(
    IsoSpec(
        iso="NYISO",
        default_area_type="locality",
        metric_aliases=_METRIC_ALIASES,
        delivery_year_kind="planning",
    )
)
