"""PJM capacity-deliverability spec (reference ISO implementation).

PJM publishes CETO (Capacity Emergency Transfer Objective — the locational
capacity *requirement*) and CETL (Capacity Emergency Transfer Limit — the
*import transfer limit*) in MW per Locational Deliverability Area (LDA), in the
RPM Base Residual Auction "Planning Period Parameters" PDFs (and the BRA
reports / CETO-CETL DESTF deck as cross-checks). Delivery years are labelled
"2025/2026" (June 1 - May 31).

Native -> canonical metric map: ``ceto -> requirement``, ``cetl -> import_limit``
(the retrieval CSV may already use the canonical names, in which case they pass
through unchanged). Areas are LDAs (MAAC, EMAAC, SWMAAC, PSEG, PS-NORTH,
DPL-SOUTH, PEPCO, ATSI, ATSI-Cleveland, COMED, BGE, PL, DAY, DOM, DEOK, ...)
plus the RTO-level rows.

This module is the template the other ISO modules (miso/nyiso/isone/caiso)
follow: declare an :class:`IsoSpec` and register it. It uses the default
unified-CSV parser; an ISO with a native (non-CSV) source would instead pass a
custom ``parse`` hook to its spec.
"""

from __future__ import annotations

from . import IsoSpec, register

# LDAs PJM lists in the 2025/26 parameter set (later years add/drop a few).
# Documentary constant — the parser does not require areas to be in this set,
# but it records the expected vocabulary for reviewers and tests.
EXPECTED_AREAS: tuple[str, ...] = (
    "MAAC",
    "EMAAC",
    "SWMAAC",
    "PSEG",
    "PS-NORTH",
    "DPL-SOUTH",
    "PEPCO",
    "ATSI",
    "ATSI-Cleveland",
    "COMED",
    "BGE",
    "PL",
    "DAY",
    "DOM",
    "DEOK",
    "RTO",
)

# Native PJM labels -> canonical metric vocabulary.
_METRIC_ALIASES = {
    "ceto": "requirement",
    "cetl": "import_limit",
    "ceto_mw": "requirement",
    "cetl_mw": "import_limit",
}

SPEC = register(
    IsoSpec(
        iso="PJM",
        default_area_type="lda",
        metric_aliases=_METRIC_ALIASES,
        delivery_year_kind="planning",
    )
)
