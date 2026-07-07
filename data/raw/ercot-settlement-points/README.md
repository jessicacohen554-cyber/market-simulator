# ERCOT Settlement Points List and Electrical Buses Mapping (NP4-160-SG)

Authoritative ERCOT-native crosswalk from electrical substation code to
settlement load zone (LZ_WEST / LZ_NORTH / LZ_SOUTH / LZ_HOUSTON).

- Source: ERCOT MIS public report NP4-160-SG (report type 10008),
  "Settlement Points List and Electrical Buses Mapping".
  https://www.ercot.com/mp/data-products/data-product-details?id=NP4-160-SG
- File: `SP_List_and_EB_Mapping_2026-06-18.zip` — the 2026-06-18 weekly Model DB
  Load bundle, downloaded 2026-07-07 via the public misdownload servlet
  (doclookupId 1244933617). Immutable; do not modify in place.
- Key member: `Settlement_Points_*.csv`, columns include `SUBSTATION` and
  `SETTLEMENT_LOAD_ZONE`. The `SUBSTATION` code matches the NP6-86
  (SCEDBTCNP686) `FromStation`/`ToStation` station codes exactly, covering
  93.3% of West-corridor binding-interval weight (2023-2025). LZ_WEST has
  precision 1.00 vs HIFLD-coordinate geography for the West Texas Export /
  Permian / CREZ region (validated 2026-07-07).

Purpose: geographic attribution of NP6-86 nodal binding constraints to the
West Texas Export wind corridor, for the derived VRE curtailment-share driver
(docs/handoffs/ercot-vre-curtailment-topology-scope-2026-07.md, WP-B).
This is a static reference mapping (network topology), not a time series.
