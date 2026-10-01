# PRECOMMIT — miso-280: West Riverside CAMPD identity remap (55641 CT-03/CT-04 → EIA 64020)

```
LANE    : miso-280 (handoff candidate C; owner ruling 2026-09-28 "Build it (Recommended)"; rule 28(a) on-queue:
          CHARTER-miso-stgas-unit-fuel-attribution scope item 2, held out by miso-278/279)
KEEPER  : 2026-09-27-miso-279-stcov (results/calibration/miso279_span, 2019-2025), legs solved at 47d3f872
ARM     : keeper recipe + campd_split_remap_companions = true (new field, default False)
CONTROL : none solved. G-DRIFT 47d3f872..<pin> (§3); the keeper bundle IS the control (rule 29(b) form 4)
SHARDS  : 7 legs, one year each 2019-2025 (rules 34(c), 36), pinned to this document's commit SHA
DATA    : DATA PROFILE: miso — no intake; seven derived '-splitremap-' companions committed before this document
DOF     : +0 (CAMPD unit identity + EIA-860 generator ids + the frozen derive estimators; no parameter)
```

## 1. The object (rule 14; rule 23 trigger = identity data change, never a residual)

CAMPD files West Riverside Energy Center's 2020 CTs (EIA plant 64020, CTG3/CTG4) under legacy Riverside 55641 as
units `CT-03`/`CT-04`. CAMPD CT-03+04 gross tracks EIA-923 64020 net within 2 % every year 2020–2025. Every
CAMPD-derived artifact the keeper reads books those units on 55641: 55641 carries its sibling's outage windows (64020
none of its own), 55641's CC heat-rate row is refused `boundary_above_band` (64020 on a fallback rate), and 55641's
tranche row reads a 150 % median CF. Phase 0: `docs/records/miso/FINDING-miso280-phase0-riverside-vlr-southgas-2026-09-28.md` §1, §5.

**This lever targets no failing criterion** (C1 CC_REGULAR passes every year). It is taken on structure (owner ruling).

## 2. The delta

- `campd.CAMPD_UNIT_PLANT_REMAP` += `(55641,"CT-03")→64020`, `(55641,"CT-04")→64020` (unconditional; no live solve
  path reads raw CAMPD — post-solve benchmark per-plant rows re-route; ISO class totals byte-identical).
- Gate `campd_split_remap_companions` (default False, `_CACHE_KEY_OPTIONAL_FIELDS`, drop value `"False"`): selects the
  `-splitremap-` companion of seven artifacts at once; an absent companion RAISES. Off ⇒ every keeper path and sha
  unchanged (tests `tests/unit/data/test_campd_split_remap_companions.py`, 17 pass).
- Companions = keeper file with only the 55641/64020 lines swapped for the re-derived ones (derive scripts drifted
  since the keeper files were cut, so a full re-derive would move unrelated rows; splicing the no-remap re-derive back
  reproduces each keeper file byte-for-byte — control measured):

  | companion | sha256 | rows changed |
  |---|---|---|
  | `campd-unit-outages-unitroute-splitremap-MISO.csv` | `76c0ebb09fdef8de08639f8c5f7712c9a035eddc107834ea0af8bfaa61a9a834` | 88 (55641 96→31, 64020 0→65) |
  | `campd-unit-outages-shortgas-splitremap-MISO.csv` | `147b9b197e310d9586c3025b151fae4741c584564be98822b7dfcb5d5e83afca` | 36 |
  | `campd-unit-outages-maxgen-unitroute-splitremap-MISO.csv` | `67886b6572c4b7d34a89e524c94d1c470df47a55348bb7d7d48b48b714e1bb1f` | 10 |
  | `campd_cc_heat_rates-splitremap-MISO.csv` | `0c140f0487054fa2d5310ea82dd7bcdbf3b19703277de026bb99a7f3566b1799` | 64020 new 6.9149; 55641 6.8982 refused → 6.8831 ok |
  | `thermal_tranches-fuelsplit-stcov-splitremap-MISO.csv` | `d6a3c9e497f42a8d637d75df5c25dc00bbbc715a6bd455fcd972f2921d3d9f54` | 55641 CF 150→95.2; 64020 new |
  | `thermal_tranches_online_frac_by_year-…-splitremap-MISO.csv` | `88b00ce785166c71aed9a970716df850876ac8d47240bf30f26bc82371ce6298` | |
  | `thermal_tranches_p25_level_mw-…-splitremap-MISO.csv` | `a7393d7a6f373f7a9b077ec9b97d7907aa59ed8356986f5347c847b8015cb1b4` | |
  | `thermal_tranches_oom_level_mw-…-splitremap-MISO.csv` | `c61daea77720eb8bf7a1b68e25a05ac9b2c43d3c1ef7072973731594f346a0fb` | |

- Out of scope: `plant_emission_rates_v2` (shared all-ISO; no carbon/NOx/SO2 price in the MISO backcast → not in
  dispatch; C5a co2 is reported-only).

## 3. G-DRIFT — `47d3f872..<pin>`

Measured over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`, `data/raw/_validation-source`,
`data/raw/reference` at `6ca311d4` (96 commits, 26 files): **all INERT for MISO** — SPP West/East variant (gated
`iso=="SPP"` + `spp_west_east_active()`), CAISO intertie/import-cap/ST_GAS HR (CAISO-keyed), NYISO import ladders,
PJM mid-curve (off), `coal_econ_marginal_hr_two_sided` (off, no MISO artifact), `retiree_cems_cap` removal (keeper has
it `false` every year), ERCOT W A Parish bin rows and ERCOT LMP benchmark. MISO solve-surface fingerprint unchanged
(216 rows, `2d9f493abe84`). Plus this lane's own hunks: **the delta** (LIVE only under the gate) and the `runner.py` /
`assembly.py` selector plumbing (returns the plain bool when unarmed — INERT). Form 4 holds.

## 4. Zero-LP footprint (fleet_only, keeper vs arm; `results/phase0/miso/_miso280_splitremap_footprint.json`)

| yr | CC_REGULAR availability TWh | Δ |
|---|---|---:|
| 2019 | 138.343 → 138.343 | 0 |
| 2020 | 140.589 → 141.253 | +0.66 |
| 2021 | 146.720 → 146.005 | −0.71 |
| 2022 | 171.703 → 170.530 | −1.17 |
| 2023 | 181.456 → 181.071 | −0.38 |
| 2024 | 181.135 → 180.927 | −0.21 |
| 2025 | 170.726 → 170.568 | −0.16 |

No other class, no unit outside 55641/64020 moves; floors 0 at both. 55641 committed HR 2020 11.35 → 6.92, 2021 11.15 →
6.90; 64020 ~6.6–6.8 → 6.85–6.98.

**Stated limitation.** In the std companion 64020 CT-03 carries a 2020-01-01 → 2020-04-09 window before West
Riverside's COD; with `unit_outage_precod_clip` off (keeper) it may overlap the COD ramp in 2020. Reported, not fixed
here (that flag would be a second delta).

## 5. Predictions (directions and bounds only)

1. 2019 byte-identical to the keeper (no 64020, no CT-03/04 rows) up to solver noise.
2. CC_REGULAR energy moves by ≤ ~1 TWh in any year (2020–21 up at 55641 on the corrected heat rate; 2022–25 small).
3. C1 statuses unchanged; prices move by cents. C1 ST_GAS 2019 is not a criterion here (rule 1).
4. Per-plant bench rows at 55641/64020 re-route (legitimacy D-rows may change at those two plants only).

## 6. Decision rule (fixed now)

S-1 recipe = keeper + exactly `campd_split_remap_companions` (shard check HARD 1); S-2 the leg read all seven pinned
`-splitremap-` companions (HARD 1b); S-3 inputs/vintage/classifier/log as miso-279. C1–C8 reported per year at full
magnitude vs the keeper. Promotion is the owner's (rule 31); no criterion selects it (rule 1). The structural case is
rule 14: each CEMS unit's history on the EIA plant it belongs to.

## 7. Arm command (per year Y, one shard each)

```
python scripts/replay_keeper.py results/calibration/miso279_span --years <Y> \
  --set campd_split_remap_companions=true \
  --out-dir results/calibration/miso280_arm_<Y> \
  --note "miso-280 arm <Y>: West Riverside CAMPD identity remap companions"
```

Shard check: `scripts/probes/_miso280_shard_check.py --leg results/calibration/miso280_arm_<Y> --year <Y> --log <log>`.
Compose: `scripts/probes/_miso280_compose_span.py`.

## 8. Launch record

Launched 2026-09-28 02:29–02:31 UTC, all pinned to `8f765fef0ed79c89687b6bf686cb65f611a9fea4`, tagged `miso-280` /
`shard`, auto-PR off. Each pushes `claude/miso280-arm-<Y>` from out-dir `miso280_arm_<Y>` (full bundle incl.
`dispatch/<Y>_P1.parquet`, gitignore negation + plain `git add`, rule 34(a)).

| year | session |
|---|---|
| 2022 (first, slow leg) | `session_01PjwJzuftGNxzfT3k9MMR6C` |
| 2019 | `session_0155sG1WB9jZeb8GZZKJLFG5` |
| 2020 | `session_01JdKTZNn71oRmvy9YJuRx2L` |
| 2021 | `session_013emPaksn5vRQ4LtZx1grgm` |
| 2023 | `session_016oRN9g34eQ5P6ZEVzGzK37` |
| 2024 | `session_01KKs13dxQH8PB6tGtVGJjd9` |
| 2025 | `session_019svWRjQjanTwWYVhGck9Qd` |
