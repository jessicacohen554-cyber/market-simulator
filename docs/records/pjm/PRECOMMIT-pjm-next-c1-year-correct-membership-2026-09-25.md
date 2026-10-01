# PRECOMMIT — PJM-NEXT card 1: year-correct plant membership and zoning, 2019–2025 (2026-09-25)

Written and pushed **before any solve**. The seven shards pin to this commit's full SHA.

**Card.** Handoff item 1 was `mid_vintage_exit_carry` (PJM cell U). Phase 0 found that arming it alone
would break rule 14 in two places, so the card became one package of three year-correct-membership repairs.
All three are measured inputs with zero free parameters, and the arm is decided on structure (rule 1).

**Incumbent / control (rule 29(b) form 4):** keeper `2026-09-25-pjm-r-pjm-2`, bundle
`results/calibration/rpjm2_span` (2019–2025 in one bundle, all seven years solved at `651fac08`).

## 1. Phase 0 — what the zero-LP census found

Probes: `scripts/probes/_pjmnext_mvx_phase0.py` (a `fleet_only` rebuild of the keeper recipe for each year,
in three postures) and `scripts/probes/_pjmnext_bench_union_phase0.py` (the keeper's EIA-923 benchmark,
rebuilt with and without the union).

### 1a. `mid_vintage_exit_carry` — real plant-months the keeper drops

Plants that retired during their own vintage year are in neither sheet the fleet reads, so the keeper
has none of their operating months. The flag adds them back, and the rebuild shows no double carry: in
every year, 0 keeper units are removed or changed.

| year | added plants | added MW | largest |
|---|---|---|---|
| 2019 | 18 | 4,863 | Bruce Mansfield 6094 coal 2,490 (ret 2/2019 + 11/2019), **Three Mile Island 8011 nuclear 803 (ret 9/2019)**, B L England 292, Bellmeade CC 267, Bremo Bluff ST 227 |
| 2020 | 6 | 1,080 | Conesville 2840 coal 780 (6/2020), Notch Cliff / Westport CTs |
| 2021 | 4 | 462 | Birchwood 54304 coal 238 (3/2021), McKee Run ST 103 |
| 2022 | 22 | 4,145 | W H Zimmer 6019 1,305 (5/2022), Avon Lake 652, Cheswick 565, Will County 510, Chambers 244, Logan 219 |
| 2023 | 5 | 3,650 | W H Sammis 2866 1,503 (6/2023), Joliet 29 ST 1,036 (9/2023), Yorktown ST 790 (5/2023), Joliet 9 314 |
| 2024 | 9 | 1,206 | Homer City 3122 coal 626 (4/2024), Southeast Chicago CT 296 |
| 2025 | 0 | 0 | the canonical snapshot's retiree parquet already carries these plants (by design) |

### 1b. NEW DEFECT — fleet zoning. Plants eGRID 2023 lacks go to `PJM_AEP_Ohio`

The fleet zones each plant from the eGRID-2023 lookup. PJM is **not** in
`zone_assignment._EIA860_SUPPLEMENT_ISOS`, so any plant eGRID 2023 lacks falls back to `PJM_AEP_Ohio`,
wherever it really is. This hits the keeper's own fleet, not just the new rows:

| year | keeper MW in the wrong zone | + mvx rows (off → with mvx) | with `fleet_zone_vintage_coords` |
|---|---|---|---|
| 2019 | 3,824 | 8,585 | **0** |
| 2020 | 3,561 | 3,861 | **0** |
| 2021 | 2,900 | 3,363 | **0** |
| 2022 | 18 | 2,855 | **0** |
| 2023 | 0 | 0 | 0 |
| 2024 | 5 | 5 | **0** |
| 2025 | 4,529 (all retired ≤ 2022, so inert) | same | 0 |

Examples: Will County (IL) → ComEd, Cheswick → West_APS, Avon Lake → ATSI, Chambers / Logan (NJ) → EMAAC,
Bruce Mansfield → West_APS, TMI → Central_PA. The 2025 cell still carries 8,502 MW with no coordinates.
All of those 25 plants are canonical-retiree units that retired by 2022, so they carry no MW in 2025.

**Repair (this commit):** `ScenarioConfig.fleet_zone_vintage_coords`, default off. It applies only in the
fallback branch of `fleet/eia860._assign_zones`: the plant is zoned from the active EIA-860 vintage's own
plant-file coordinates, using the same `_eia860_ba_zones` rule the supplement already applies. PJM's
coords-only branch borrows the nearest eGRID PJM plant's FIPS, which agrees 98.3 % of the time in
leave-one-out. An eGRID-placed plant is never re-zoned, and membership never changes. The flag has zero
free parameters, its matrix row is added in every shard, and it is registered in the cache key with a
frozen default drop, so the default key `bd75ebb8333a8e61` is unmoved.

### 1c. The PJM benchmark omits the same plants (SPP-49's PJM finding, measured on the keeper)

The benchmark's population is `build_zone_lookup`'s keys, which for PJM means eGRID 2023 only. The
**model** fleet carries every PJM-BA plant in the vintage, so the model dispatches plants the actuals
leave out. The existing `benchmark_membership_vintage_union` (SPP-49, PJM cell O) fixes this. Here is the
EIA-923 benchmark change it makes on the keeper's own meta (TWh; additive, min Δ −0.0045 in `OTHER` from
dual-fuel re-attribution, reported):

| year | COAL_BIT | COAL_PRB | COAL_WC | nuclear | ST_GAS | biomass | solar | total off → on |
|---|---|---|---|---|---|---|---|---|
| 2019 | **+8.80** | +0.77 | +0.41 | **+5.21** | +0.57 | +0.92 | — | 803.70 → 820.81 |
| 2020 | **+8.27** | +0.30 | +0.04 | — | +0.63 | +0.49 | — | 795.85 → 805.90 |
| 2021 | **+7.84** | +0.69 | — | — | +0.06 | +0.28 | — | 818.09 → 827.09 |
| 2022 | **+4.47** | +0.30 | — | — | +0.02 | +0.10 | — | 828.26 → 833.19 |
| 2023 | — | — | — | — | — | — | — | 823.02 → 823.02 |
| 2024 | — | — | — | — | — | +0.02 | **+2.31** | 849.91 → 852.25 |
| 2025 | — | — | — | — | — | — | — | 871.63 → 871.63 |

These deltas land on the class carrying the keeper's C1 coal over-runs (COAL_BIT +11.36 / +21.45 /
+25.70 TWh in 2019 / 2020 / 2021). **Arithmetic only, with the model unchanged:** the union alone would
shrink those rows to about +2.6 / +13.2 / +17.9. It cannot be armed without mvx, though. The 2019 nuclear
(+5.21, TMI) and 2022 coal (+4.47: Zimmer, Will County, …) are generation from plants the keeper's model
**lacks**, so the union alone would open new misses of that size. **The three repairs are one package:
the model and the actual get the same plants.**

**Rebuild seam repair (this commit):** `run_calibration_full.build_benchmark_frames` recovered the union
flag only from meta's top level and from run_config's top / `calibration_flags` blocks. A
`replay_keeper --set` lands it in the override bag and in `scenario_config`, so a `--rebuild-benchmark`
registration would silently fall back to the canonical-only population. That is the bench/model split the
recovery exists to prevent. The recovery now reads all five places. This is inert for every bundle that
never set the flag, including the keeper.

## 2. Recipe

The keeper `meta.json` is replayed unchanged (`scripts/replay_keeper.py results/calibration/rpjm2_span`)
with exactly three `--set` flags:
`mid_vintage_exit_carry=true`, `fleet_zone_vintage_coords=true`, `benchmark_membership_vintage_union=true`.
**Offer curves are unchanged** (`authorized_price_tuning.used = false`), and the outage files are the
keeper's.

## 3. G-DRIFT `651fac08` → this pin (rule 29(b)) — zero LP, recorded before any solve

`git diff 651fac08 06d9a9da -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` (61 files), classified hunk by hunk:

| change set | PJM verdict |
|---|---|
| NWPP / SOCO / MISO / CAISO benchmark rows, LMP parquets, seam ladders, hydro backfill, nuclear CF, carbon rows | INERT: other ISOs' keys. `PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[2019]` is read only under `pjm_seam_neighbour_hourly_ladder`, which is false in the recipe |
| ERCOT measured bin heat rates (`73be1f68` / `e5e68768`) | INERT: `iso == "ERCOT"` branch |
| SOCO BA membership / recode / join (`9f0e8f81`), including hunks inside the `mid_vintage_exit_carry` loader and `_iso_plant_ids` | INERT: SOCO-only registries, so PJM gets the same frame back |
| NWPP pool gap guard (`9e3b40d1`) | INERT: NWPP pool path |
| 2019 RGGI rows (`72c8c7ee`) | INERT: already in the keeper's tree |
| key provenance tooling, derive / report scripts | INERT: not on the solve or scoring path |
| **COAL-SUB (`8eaf34b5` + `05437cc0`)**: `coal_subclass`, link 5 of `coal_supply_class`, the `_rows_to_generators` coal group, `_offer_curve_for_group`, `_retire_bare_coal_class`, the deleted `_PJM_OFFER_CURVE["COAL"]`, and the assembly `coal_supply` consumer | **LIVE for 2019–2022.** The keeper's formerly bare-`COAL` cohort (5.47 / 4.07 / 4.67 / 1.36 GW; 18.22 / 7.33 / 16.97 / 3.70 TWh of keeper dispatch) now resolves to COAL_BIT / PRB / WC. It prices on the subclass offer curve instead of the keeper's `COAL` curve 0.648 / 0.684 / 0.792 / 1.044, and the subclass passthrough sigmoid now applies. **INERT for 2023–2025**: the keeper has no bare-`COAL` output there, and plant 10743 (50 MW WC) is the only unresolved plant. |
| COAL-SUB scoring hunks (`_dispatch_frame` / `_model_class_for_unit`, backfill re-mapping, `benchmark_semantics.COAL_CLASSES`) | **LIVE-scoring for 2019–2022**: the bare-`COAL` model and benchmark MWh re-bucket into the subclasses, so compare per-class C1 in those years against the control, never against the committed keeper numbers |
| COAL-SUB on the arm's injected retiree coal | LIVE-for-arm: those units get a subclass too. Confirmed at HEAD by a `fleet_only` rebuild of 2019–2024 with the arm on: no `coal_subclass` raise, and the added coal lands in COAL_BIT / COAL_WC / COAL_PRB |

**Consequence (rule 29(b)).** Form 4 is valid for **2023–2025** only. For **2019–2022** a LIVE hunk earns a
**control solve**: the keeper recipe replayed at this pin with no `--set`. The arm is differenced against
that control for 2019–2022, and against the committed keeper for 2023–2025. The COAL-SUB contribution
(control minus committed keeper, 2019–2022) is reported separately as a re-pricing of the cohort. It is
not the arm's effect.

## 4. Gates and predictions (declared before any solve)

Decided on structure (rule 1). A failed gate does not kill the arm, and a passed gate does not promote it.

- **G1 liveness (shard hard stops).**
  - `run_config.json` shows the three flags true, plus the keeper's
    `eia860_vintage_tracks_solve_year`, `measured_*_heat_rates` and `pjm_rggi_allowance_pricing` true.
  - The solve log line `mid-vintage-year exit carry (PJM <y>): injecting N unit(s)` shows N =
    47 / 34 / 24 / 73 / 45 / 60 for 2019–2024. 2025 prints no such line.
  - The log line `fleet_zone_vintage_coords (PJM): K of M generators …` appears with K > 0 in 2019–2022
    and 2024.
  - The bundle's EIA-923 shared-input frame totals 820.811 / 805.898 / 827.088 / 833.192 / 823.024 /
    852.252 / 871.628 TWh for 2019…2025 (±0.001).
  - The `campd_unit_outages` sha is `312a11b8…`, as in the keeper.
- **G2 directional predictions.** For 2019–2022 these are arm vs **control** (§3). The COAL-SUB
  re-pricing of the bare-`COAL` cohort is measured separately, as control minus keeper, and not predicted
  here. The §1c "arithmetic only" row numbers are against the committed keeper and serve only to size the
  bench effect.
  - 2019: model COAL_BIT and nuclear rise (Bruce Mansfield, TMI). The COAL_BIT C1 error falls from
    +11.36 toward ~+2.6 plus whatever Mansfield dispatches, and nuclear stays within ~±1 TWh of the keeper's
    error (TMI's ~4.9 TWh of model against +5.21 of actual).
  - 2020 / 2021: the COAL_BIT error falls by ~8 TWh each (bench side), less the small added coal
    (Conesville 780 MW to 6/2020, Birchwood 238 MW to 3/2021). **2021 is expected to stay a C1 FAIL.**
    The CC −17.4 / CT −11.1 offer-ordering finding (card 4) is untouched by this card.
  - 2022: COAL_BIT rises on both sides (bench +4.47, model + Zimmer / Avon Lake / Cheswick / Will
    County's pre-retirement months). Net sign not predicted.
  - 2023: bench unchanged. Model adds Sammis coal (to 6/2023) and Joliet 29 / Yorktown ST_GAS, so
    **2023 COAL_BIT and ST_GAS rise against an unchanged actual** (the keeper's 2023 rows are the ones to
    watch). 2024: bench solar +2.31, and the model adds Homer City (to 4/2024).
  - Zoning: zonal prices can move in AEP_Ohio / ComEd / EMAAC / West_APS in 2019–2022. C3b is the
    criterion to read.
  - Determination: 2023–25 is expected to remain **NOT-YET on C1 (CC_REGULAR 2024 −14.4)**, which this
    card does not touch, and 2019–22 NOT-YET.
- **G3:** full C1–C8 rubric for every year. The reference is the control (2019–22) or the keeper (2023–25),
  re-scored on the same (union) benchmark, which separates the bench effect from the solve effect. D-1 / D-2 / D-4 run once on the composite.

## 5. DOF (rule 21)

Zero new free parameters. All three flags are measured-input switches (EIA-860 vintage retirement records,
EIA-860 plant coordinates, EIA-860 vintage BA codes). The offer-curve multiplier block is carried unchanged
from the keeper, with its existing ledger entry.

## 6. Year set (rules 34(c) / 35(b))

The PJM registered set at this pin is the keeper only, 2019–2025. **Union = 2019–2025.** All seven years
are solved.

## 7. Shards (rules 32 / 34 / 36)

There are **eleven** shards, each in its own container, pinned to this commit's full SHA: **seven arm
shards, one per year 2019…2025**, plus **four control shards for 2019–2022** (§3). Arm out-dir is
`results/calibration/pjmnext_c1_<y>`, on branch `claude/pjmnext-c1-<y>`. Control out-dir is
`results/calibration/pjmnext_ctl_<y>`, on branch `claude/pjmnext-ctl-<y>`; it runs the same command with
**no `--set`**. A control bundle is never registered and is kept out of `main` (rule 29(c)); its numbers
live in the RESULT doc. Arm command:

```
python3 scripts/replay_keeper.py results/calibration/rpjm2_span --years <y> \
  --set mid_vintage_exit_carry=true --set fleet_zone_vintage_coords=true \
  --set benchmark_membership_vintage_union=true \
  --out-dir results/calibration/pjmnext_c1_<y> --note "PJM-NEXT card 1, <y>"
```

**Retrievability (rule 34):** every shard pushes its full bundle to its own branch, including
`dispatch/<y>_P1.parquet`, using a `.gitignore` negation and a plain `git add`. The parent fetches the
bundles, composes one 2019–2025 bundle, registers it, and lands it on `main` before this lane's PR merges.
Shard SHAs are provenance only.

## 8. Promotion

Promotion is **not** decided here. The parent registers the arm, scores it against the keeper on the same
benchmark, and **asks the owner** (rule 31). If the owner rules to promote, the rule-35 order applies:
register, `audit_keepers`, `keepers/PJM.json`, `calibration-complete.json`, `build_status`, matrix
re-stamp, then prune.
