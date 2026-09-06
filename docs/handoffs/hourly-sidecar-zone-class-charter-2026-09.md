# Per-zone / per-class / per-storage-unit hourly sidecars — CHARTER (owner-funded 2026-09-06, session caiso-261)

**Owner decision (card, 2026-09-06): "Charter the sidecar" — "An Opus/Fable
core-infra session adds per-zone, per-class and per-storage-unit hourly
sidecars to every solve so the LP identity can be closed from committed
files without a replay. Every keeper regenerates its hourly/ on its next
promotion."** All-ISO core infrastructure (`scripts/run_calibration_full.py`,
rule 27 `[R-PUSH]`: Opus/Fable only). **No code in this session.**

## §1 — The defect the ask closes

The committed `hourly/` sidecars (`class_hourly_<year>.parquet` — ISO-total
MW by klass; `system_<year>.parquet` — per-zone price/slack/dump/demand;
`storage_<year>.parquet` — per-tech charge/discharge; `class_band_hourly`;
`reserve_family`) do not close the LP's energy balance: Σ klass + Σ
(discharge − charge) + slack − dump − Σ demand reads **+66 / +250 / +261 MW
mean, max 233 / 487 / 507 MW** on the CAISO keeper (caiso-258 §2.1,
re-measured unchanged at caiso-261) — not exports (the sinks never
dispatch), not slack/dump, not the WECC nodes, not a loss term. Because the
class sidecar is ISO-total and the storage sidecar is per-tech, the
residual cannot be attributed from committed files; a replay of the full
(gitignored) dispatch frames is the only route, which is exactly what rule
15's "read the keeper's hourlies instead of replaying" was meant to avoid.
The same gap blocks every per-zone question the CAISO lane has carried
since caiso-249 (the DOM_GAS/STORAGE boundary, the Pacific 07–08 slab, the
hod 22–23 closure by zone).

## §2 — What the funded session adds (seam: `_write_class_hourly_sidecar` and siblings, `scripts/run_calibration_full.py` ~L542)

1. `hourly/zone_class_hourly_<year>.parquet` — `(year, pass, zone, klass,
   hour, mw)` for every load zone AND every import/export node, signed MW
   unclipped, from the same P1 dispatch frame the ISO-total sidecar is
   summed from (so the ISO-total remains its exact marginal).
2. `hourly/storage_unit_hourly_<year>.parquet` — `(year, pass, zone, unit,
   tech, hour, charge, discharge, soc)`.
3. `hourly/flow_hourly_<year>.parquet` — `(year, pass, link, hour, mw)` for
   every transmission link, so inter-zone flow is on the record.
4. `hourly/identity_<year>.json` — the per-zone hourly closure computed at
   write time (Σ gen + Σ storage net + Σ inflow − Σ outflow + slack − dump −
   demand), max |residual| and the hours it exceeds 1 MW: **a solve whose
   own sidecars do not close to ≤ 1 MW per zone-hour fails its write**, and
   the number is in the bundle forever.
5. Size budget: per-zone × class ≈ 8 zones × 14 klasses × 8760 → ~1M rows
   per year, sub-MB in parquet with dictionary encoding; the storage-unit
   table is the largest (ERCOT/CAISO hundreds of units) — cap by writing
   per-unit rows only for units ≥ 10 MW and rolling the rest into a
   `_small` unit per zone/tech, and state the rule in the file's metadata.

## §3 — Rules that bind it

* Rule 15: the new sidecars are part of every KEEPER bundle's committed
  set from the promotion that first carries them; existing keepers are NOT
  re-solved for it — each ISO's keeper regenerates its `hourly/` on its
  **next** promotion (the replay path `scripts/replay_keeper.py` gains the
  same writers so a keeper can be re-sidecarred from a byte-identical
  replay when a lane needs it before then, and that replay is justified by
  this charter, rule 15's "unit-level questions" clause).
* Rule 28: no solve-affecting change — the writers read the dispatch
  frame after the solve; `cache_key()` / the solve surface are untouched
  and every registered run re-scores byte-identically
  (`check_registry_payload_parity.py`, `tests/scoring/` goldens).
* Rule 27: edited locally, pushed as on-disk bytes, blob-verified.
* The identity check (§2.4) is a test in `tests/` on the two golden
  systems (1 gen / 1 zone / 24 h first), then on a full bundle.

## §4 — First consumer

The CAISO hod 22–23 closure (caiso-258 / caiso-261) re-run per zone from
the new sidecars, attributing the +261 MW 2025 residual — the acceptance
demonstration for the lane.
