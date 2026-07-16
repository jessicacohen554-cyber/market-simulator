"""MISO declared capacity-emergency events spec (pre-2026 Max Gen ladder).

MISO's capacity ladder over the registry window 2023-2025 is Capacity
Advisory -> Maximum Generation Alert -> Maximum Generation Warning -> Maximum
Generation Event Steps 1-5 (each level's pricing/capacity effects are
enumerated in the 2023 MISO SOM p.10: Alert = 4-hour online resources may set
price in ELMP; Warning = Tier 1 emergency pricing + non-firm export
curtailment + external capacity-resource calls; Step 1 = emergency-only unit
commitment + emergency output ranges; Step 2 = Tier 2 pricing + LMRs +
emergency DR/purchases; Steps 3-5 = curtailment priority / reserve-sharing /
firm load shed). MISO's 3-step simplification takes effect 2026-06-01
(KA-01551), outside this window.

Declared scopes MISO documents use: the full footprint, or the Midwest /
South subregions. MISO market operations run on EST (UTC-5) year-round
(Tariff Module A convention; the IMM Summer-2025 quarterly states its event
hours in EST), so ``utc_offset_hours=5``.

Primary sources per row are the Potomac Economics (IMM) SOM/quarterly
reports — see ``data/raw/maxgen-events/README.md`` for the full source ladder
(OASIS remains the upgrade path for endpoint precision when reachable) and the
adjudicated absences (Jan-2024 Heather: no declaration above Conservative
Operations; Jan-2025 Enzo: raised STR requirements, no declaration).
"""

from __future__ import annotations

from . import IsoSpec, register

# Declared-scope vocabulary observed in the 2023-2025 primary documents.
REGIONS: frozenset[str] = frozenset({"footprint", "midwest", "south"})

register(
    IsoSpec(
        iso="MISO",
        regions=REGIONS,
        utc_offset_hours=5,  # EST year-round (Tariff Module A)
    )
)
