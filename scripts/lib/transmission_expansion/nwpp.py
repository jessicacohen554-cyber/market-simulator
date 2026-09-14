"""NWPP transmission-expansion spec.

Binding instrument: there is no pool-wide transmission planning authority, so
the committed set is each participant's **Board- or Commission-approved
project with a WECC path rating or an executed construction commitment** —
Boardman-to-Hemingway (B2H, Idaho Power / PacifiCorp / BPA, 2028 in Idaho
Power's 2025 IRP preferred portfolio, printed p. 5), SWIP-North (2029, same
table), and PacifiCorp's Gateway segments (the 2024 catalogue already carries
Path 85 Aeolus West "Post Gateway" at 2,670 / 1,816 MW, README §1.2). Source
the curation reads from: the **WECC 2024 Path Rating Catalog — Public Version**
(``data/raw/nwpp-planning/transcriptions/2024_Path_Rating_Catalog_Public_v2.txt``,
landed by NWPP-12), whose "Accepted" / "Planned" categories and revision dates
are the rating-side instrument, plus the participant IRPs in the same corpus for
the in-service dates. ``TRANSMISSION_BASE_STATIC_VINTAGE["NWPP"]`` is **2024**
accordingly — the catalogue vintage every base link in ``_nwpp_config`` is
transcribed from.

**DATA NEEDED — no rows yet**: ``data/raw/transmission-expansion/nwpp.csv`` does
not exist, so :func:`parse_unified_csv` returns the empty, correctly-shaped
frame and the forward TTC channel applies nothing for NWPP. At this five-zone
whole-BA grain most projects are ``intra_zonal`` (recorded, dispatch-inert);
B2H raises the NW↔INLAND corridor (it terminates at Hemingway, IPCO, and
Boardman, BPAT) and maps to that ``link`` row; the NW↔OR boundary has no rated
path and will not acquire one (README §1.4), so no row can ever target it.
NorthWestern's caveat rides with every rating: "ATC is much less than TTC"
(2026 MT IRP printed p. 122). Registered 2026-09-14 by lane NWPP-20.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="NWPP",
        source_note=(
            "WECC 2024 Path Rating Catalog (Accepted/Planned paths, revision "
            "dates) + participant IRP in-service dates (B2H 2028, SWIP-N 2029); "
            "no nwpp.csv curated yet."
        ),
    )
)
