"""SPP transmission-expansion spec.

Binding instrument: **SPP Board of Directors approval of an ITP portfolio** — the
Notification to Construct (NTC) issued against a Board-approved Integrated
Transmission Planning assessment is what commits a project and allocates its
cost, so NTC-issued projects of an approved portfolio are the committed set.
Source the curation reads from: the **2025 ITP Assessment Report v1.0**
(``https://www.spp.org/Documents/75483/2025%20ITP%20Report%20v1.0.pdf``, full
text at ``data/raw/spp-planning/transcriptions/2025_ITP_Report_v1.0.txt``,
landed by SPP-12) — its portfolio and staging chapters, and for the SPS /
Texas-Panhandle area specifically §4.6 (printed p. 120), §7.3.9 (p. 202) and
Table 7.1 "SPS Projects" (p. 204). FINDING-spp-12 §6 records what the report
does NOT contain: a rated North<->South transfer capability — it is a project
portfolio, not an interface-rating document — which is why
``iso_configs._spp_config``'s N<->S link is a Tier-3 placeholder and
``TRANSMISSION_BASE_STATIC_VINTAGE["SPP"]`` is 2025, the vintage of this source.

**DATA NEEDED — no rows yet**: ``data/raw/transmission-expansion/spp.csv`` does
not exist, so :func:`parse_unified_csv` returns the empty, correctly-shaped
frame and the forward TTC channel applies nothing for SPP. At this two-zone
grain most ITP projects will be ``intra_zonal`` (recorded, dispatch-inert);
only a project that raises the North<->South corridor's rated capability maps
to the ``link`` row, and it will need the rated base the placeholder lacks
before a delta can be reconciled against it (rule 14). Registered 2026-09-06 by
lane SPP-20.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="SPP",
        source_note=(
            "SPP Board-approved ITP portfolios with NTCs issued (2025 ITP "
            "Assessment Report v1.0: portfolio / staging chapters; SPS §4.6, "
            "§7.3.9, Table 7.1); no spp.csv curated yet."
        ),
    )
)
