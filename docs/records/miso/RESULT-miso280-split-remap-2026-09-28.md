# RESULT — miso-280: West Riverside CAMPD identity remap. Zero status flips; 2019 unchanged as predicted; PROMOTED.

```
LANE     : miso-280 (owner ruling 2026-09-28, lever card "C: Build it (Recommended)")
PREREG   : docs/PRECOMMIT-miso280-split-remap-2026-09-28.md (pin 8f765fef)
PHASE 0  : docs/FINDING-miso280-phase0-riverside-vlr-southgas-2026-09-28.md
OUTGOING : 2026-09-27-miso-279-stcov (miso279_span) — pruned (rule 35)
KEEPER   : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025)
DELTA    : campd_split_remap_companions = true (seven '-splitremap-' companions). DOF +0
CONTROL  : keeper bundle (G-DRIFT 47d3f872..8f765fef: all non-delta hunks INERT; rule 29(b) form 4)
VERDICT  : full span NOT-YET (fuelmix, price_mean, price_shape — the keeper's same three); train 2023-2025 CALIBRATED
```

## 1. Legs

Seven single-year shards pinned to `8f765fef`. Every leg passed `_miso280_shard_check.py` in the parent (recipe = keeper
+ exactly the new field; all seven `-splitremap-` companions read at their pinned shas; inputs, vintage, hydro
classifier, log). 18 files each incl. `dispatch/<Y>_P1.parquet`. All 7 shard sessions archived.

| year | leg commit (provenance) | LW internal price keeper → arm $/MWh |
|---|---|---|
| 2019 | `a28eb2c7` | 27.914 → 27.913 |
| 2020 | `de4568ee` | 24.562 → 24.511 |
| 2021 | `7920e673` | 37.080 → 37.031 |
| 2022 | `c0403949` | 58.440 → 58.638 |
| 2023 | `5f2a8568` | 32.698 → 32.737 |
| 2024 | `3fbac325` | 30.757 → 30.781 |
| 2025 | `6f39b705` | 41.630 → 41.665 |

## 2. Gates (live scorer) — zero criterion-year status flips

| criterion-year | keeper miso-279 | miso-280 |
|---|---|---|
| C1 ST_GAS 2019 (band ±8.00) | −8.003 TWh FAIL | −8.003 TWh FAIL |
| C1 CC_REGULAR 2020 / 2021 / 2022 / 2023 / 2024 | −2.95 / −5.99 / −3.52 / +0.65 / +2.08 | −2.39 / −6.01 / −4.09 / +0.21 / +1.82 (all PASS) |
| C3a 2022 | −15.8 % FAIL | −15.5 % FAIL |
| C3b 2021 | 0.254 FAIL | 0.252 FAIL |
| legitimacy D-1/D-2/D-4 FAIL rows | 11 | 11 (same set) |
| determination | NOT-YET (3) | NOT-YET (3) |

Predictions (PRECOMMIT §5) held: 2019 unchanged (no 64020, no CT-03/04 rows); CC_REGULAR moves ≤ 0.6 TWh; no status
flip; prices move by cents (2022 +$0.20).

## 3. Reading

A rule-14 identity repair: CAMPD's CT-03/CT-04 history now sits on West Riverside (64020), so its outage windows,
measured CC heat rate (6.915) and tranche row are its own, and Riverside 55641 loses its sibling's outages, its refused
heat-rate row and its 150 % CF tranche. It targets no failing criterion and moves none. Stated limitation: a
2020-01-01 → 04-09 outage window at 64020 CT-03 precedes COD (`unit_outage_precod_clip` off in the keeper).

## 4. Where the bytes are

The composite `miso280_span` (slim bundle incl. `hourly/`, attestation with a `miso280` block, regenerated diagnostics,
stamped partition passing `--check`), its registry sidecar and payload are on `main` with this lane's PR. Per-year leg
dirs are parent-local and gitignored; the SHAs above are provenance only (rule 33(d)). A re-solve of any leg costs
~20–35 min (2022 ~75 min).

## 5. Promotion and next

Promoted on the owner's ruling ("Promote (Recommended)"). Year set (rule 35(b)): outgoing {2019–2025}, incoming
{2019–2025}, covered. `audit_keepers --iso MISO` passes after the prune.

Owner rulings this lane: C3b 2021 → "Leave as routed miss"; VLR data → none public, routed. Next lane (owner pick
"Probe 2019 South steam"): zero-LP phase 0 on why floored MISO-South ST_GAS plants dispatch below actual in 2019.
