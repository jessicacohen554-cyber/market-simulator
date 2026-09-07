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
portfolio, not an interface-rating document — which is why the base N<->South
limit had to come from somewhere else. It now does: ``_spp_config``'s link
carries **3,400 MW**, the rule-14 reconciled limit-at-bind figure lane SPP-53
built from SPP's own 2026 RTBM binding-constraint archive (owner ruling P13;
``PRECOMMIT-spp-53-2026-09-07.md`` fixed the construction before any limit was
read, ``FINDING-spp-53-2026-09-07.md`` carries every number), replacing
SPP-20's 48,700 MW Tier-3 placeholder. SPP's entry in
``TRANSMISSION_BASE_STATIC_VINTAGE`` is **2026** accordingly — it follows the
limit vintage, not this module's source; the 2025 ITP report is the
committed-*project* pipeline, and a forward row read from it is reconciled
against that 3,400 MW base.

**DATA NEEDED — no rows yet**: ``data/raw/transmission-expansion/spp.csv`` does
not exist, so :func:`parse_unified_csv` returns the empty, correctly-shaped
frame and the forward TTC channel applies nothing for SPP. At this two-zone
grain most ITP projects will be ``intra_zonal`` (recorded, dispatch-inert);
only a project that raises the North<->South corridor's rated capability maps
to the ``link`` row — and since SPP-53 that row has a real base to be
reconciled against (rule 14), which the 48,700 MW placeholder never gave it.
Registered 2026-09-06 by lane SPP-20; the base-limit paragraph above brought
to the SPP-53 position by lane SPP-35 (2026-09-07, FINDING-spp-53 §6 O-4).
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
