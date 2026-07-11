# MISO capacity-market-auction-price (PRA clearing prices)

Drop the retrieved unified CSV here as **`miso.csv`**. `area` = LRZ 1-10
(`area_type=lrz`); a MISO-wide average row (if published) uses
`area=MISO`/`area_type=rto`. `season=annual` through PY2024-25,
summer/fall/winter/spring from PY2025-26. `auction_round=planning_resource_auction`.

## Authoritative sources

- MISO Planning Resource Auction Results: https://www.misoenergy.org/planning/resource-adequacy/
  (search "MISO PRA results [planning year]")

Delivery years <= 2026/2027 only.

**STATUS:** `miso.csv` committed — full seasonal per-LRZ clearing prices for
PY2025-26 and PY2024-25 (all 10 LRZs × 4 seasons, from the PRA Results
Postings), full PY2023-24 (transitional season structure, from the 2023 PRA
Results), plus a sparser historical series PY2015-16 through PY2022-23
transcribed from the multi-year comparison table (single-zone-width and
whole-row merged cells only — ambiguous multi-zone-but-not-all-zone spans in
the source's flattened table image were omitted rather than guessed). PY2026-
27 results exist at MISO but the primary PDF returned HTTP 403 on repeated
fetch attempts; a secondary-source (Modo Energy) summary was found but
excluded from this file (primary-source-only policy) — logged in
`docs/handoffs/capacity-market-intake-2026-07.md`.
