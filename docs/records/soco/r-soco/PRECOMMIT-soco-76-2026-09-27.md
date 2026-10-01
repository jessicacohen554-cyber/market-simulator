# PRECOMMIT — soco-76: two SOCO CT plants priced at a class default because EPA files them under another plant ID

Lane soco-76, 2026-09-27. Written and pushed **before any shard was launched**. The parent solves nothing
(rule 32(a)). Each year is solved in its own shard (rule 36) and each shard pushes its full bundle (rule 34).

Control: the keeper `2026-09-26-soco72-gas-basis-window` (bundle `results/calibration/soco72_span`, legs solved at
`19159a0cdc961f62454b66c3b8a73b436418826f`). Its committed numbers are the control (rule 29(b) form 4). No control
solve is spent.

**Read this first: the lever does not close either failing row.** The greedy (§4) leaves 2019 COAL_BIT failing
(−4.24 → −4.15 pp) and 2020 C4 coal at 0.302. It is taken because it replaces a class-default heat rate with the
plants' own measured rate (rules 1 / 14), not because it helps a gate.

Task framing: the soco-76 handoff (TASK 1, zero LP): the gas side of the 2019 merit order. No owner ruling exists on
soco-75's two-sided coal incremental-HR mode (`docs/calibration-log/soco.md`, checked 2026-09-27), so that mode is
NOT built here.

## 0. G-DRIFT (rule 29(b)), keeper sha `19159a0c` → HEAD

- `19159a0c` → `bd2839ae`: audited by soco-73 (`FINDING-soco-73-2026-09-27.md` §1), instrument 3, **all LP inputs
  bit-identical**, every hunk INERT for SOCO.
- `bd2839ae` → `fcd46045` (read by hand): `src/market_sim/data/fuel/basis/miso.py` (MISO winter hub map — MISO
  branch only); `data/raw/_validation-source/pjm_offer_midcurve_*` (PJM); a new reference file
  `data/raw/reference/camd-eia-crosswalk/` (intake only — no backcast-path code reads it). **All INERT for SOCO.**
- This lane's own diff: one `ISO_SCOPE` row in `scripts/data/derive_egrid_identity_heat_rates.py` and the new
  artifact `egrid_identity_heat_rates_SOCO.csv`. The consumer reads it only when `egrid_identity_heat_rates` is on,
  and the keeper recipe has it `false`, so with the flag off every input is unchanged.

**Form 4 is valid. The keeper is the control.**

## 1. The census (zero LP, soco72-2019 leg): who clears in coal's CEMS-synced, model-off hours

`scripts/probes/_soco76_gas_census.py all`, record `docs/records/soco/r-soco/soco76_gas_census.json`.

- **Coal plants synced in CEMS but off in the model (2019):** Barry 8,053 h, Crist 6,302, Wansley 3,532, Daniel 193,
  Gaston 151, Bowen 48.
- **What runs instead.** In those hours the CC fleet clears at $20–22/MWh, $16–17 below the coal offer. That is the
  correct merit order at 2019 gas: the CC inputs check out against their own data (below).
- **The simple-cycle over-run.** 2019 CT_PEAKER is 12.53 TWh model vs 4.48 EIA-923 at the plant boundary. The top
  over-runners, each undercutting coal by $6–8/MWh at $30–32:

  | plant | model TWh | EIA-923 TWh | offer $/MWh | undercut $/MWh (median) |
  |---|---|---|---|---|
  | Tenaska Georgia 55061 | 2.71 | 0.13 | 30.98 | 7.42 |
  | **Dahlberg 7709** | **1.72** | **0.49** (no bench plant row) | 31.83 | 6.77 |
  | Calhoun 55409 | 1.55 | 0.34 | 31.48 | 6.98 |
  | Walton County 55128 | 1.37 | 0.46 | 30.84 | 7.60 |
  | Addison 55267 | 1.12 | 0.37 | 32.13 | 6.47 |

## 2. Testing the gas inputs against the plants' own data

For the 15 largest undercutting gas plants (undercut-TWh-weighted):

- **Heat rate vs same-year CEMS:** −0.25 MMBtu/MWh. Every artifact-covered CC and CT is within ±0.3 of its own
  CEMS. Two apparent gaps are explained: Wansley 7946 is a `steam_not_metered` plant the CC boundary guard already
  refuses; Central Alabama 55440's all-hours rate carries part-load hours (its loaded rate matches).
- **Delivered gas vs own EIA-923 receipts:** −$0.11/MMBtu. soco-72 already measured the basis.
- **Availability vs CEMS output:** no plant's model capacity sits below its measured output in a way that forces
  dispatch. The CT over-runners are available, and cheap, not mis-sized.

**Two defects found, both at plants whose measured data never reaches the model:**

### 2a. Dahlberg and Hartwell: an EPA / EIA plant-ID split (THE LEVER)

- EPA files **Dahlberg** (EIA 7709, ten 91.9 MW GTs) under CAMD/eGRID ORIS **7765**, and **Hartwell** (EIA 54538)
  under **70454**. EPA's own CAMD–EIA crosswalk (`data/raw/reference/camd-eia-crosswalk/`) flags exactly these two
  SOCO plants with `PLANT_ID_CHANGE_FLAG = 1`.
- Neither has a CAMPD record under its EIA id, so neither reaches `campd_ct_heat_rates_SOCO.csv`, and neither has an
  eGRID `PLHTRT` under its EIA id. Both price at the `HEAT_RATE_BINS` vintage class default: **10.5** (Dahlberg) and
  **11.5** (Hartwell).
- Their measured rates: eGRID `PLHTIAN/PLNGENAN` **12.62** (Dahlberg) and **12.56** (Hartwell). For Dahlberg,
  CAMPD under 7765 gives a loaded net rate of 12.26–12.62 in every year 2019–2025, and EIA-923 gives 12.21 (2019).
- **The registered carrier is `egrid_identity_heat_rates`** (nyiso-151, default off, SOCO cell `U`), built for
  exactly this two-registry split. Its frozen, threshold-free discovery rule, run over SOCO's whole CAMPD-less fossil
  population (AL/FL/GA/MS), finds **exactly these two plants, 7/7 eGRID vintages each** (exact
  `PLNGENAN == EIA-923 netgen` to <0.5 MWh):

  | plant | eGRID ORIS | pooled rate | LOYO range | model now |
  |---|---|---|---|---|
  | Dahlberg 7709 | 7765 | 12.6212 | 12.6104–12.6353 | 10.5 |
  | Hartwell 54538 | 70454 | 12.5649 | 12.2603–12.6478 | 11.5 |

- **Code:** one `ISO_SCOPE` row (rule 25: SOCO's own artifact). Estimator unchanged (rule 23: the derive's
  source is unchanged; SOCO was never in scope). Artifact
  `data/raw/_processed-legacy/egrid_identity_heat_rates_SOCO.csv`, sha256
  `32c46c93a1552a4a48e077dffac75dd817530fb50872eac31887d34c8390985f`. NYISO's artifact is untouched.
- **Zero free parameters** (rule 21): arithmetic on eGRID's published fields. **Rule 13:** regenerates from any new
  eGRID / EIA-923 vintage for a forward year. **Rule 19:** no other mechanism prices these plants — the class
  default is simply replaced.

### 2b. McDonough 710 CTs: plant-blend heat rate (RECORDED, NOT BUILT)

- The four 1971 CTs at Jack McDonough carry the plant's CC-dominated eGRID blend **6.83**, so they offer $21.92 and run
  0.48 TWh in 2019 against ~0 actual (CEMS 645 MWh gross).
- `egrid_family_heat_rates` (armed) refuses the GT family as `out_of_window`: its own rate is 35–46 MMBtu/MWh on
  ~150–230 MWh/yr (start-dominated). The CT artifact needs ≥ 50 loaded hours; these units have ~22.
- **No measured, zero-parameter rate exists** for these units. Falling back to the class default instead of the plant
  blend would be a design change to the family mechanism (rule 19). It is the named next object, not built here.

## 3. Census (zero LP): the lever in the fleet

`_soco76_gas_census.py fleet`, record `docs/records/soco/r-soco/soco76_identity_fleet_census.json`. A `fleet_only`
rebuild on the keeper recipe, flag off vs on, all seven years:

- **Exactly six units move in every year** (Dahlberg and Hartwell `_econlo` / `_econhi` / `_peak`); neither plant has
  a `_committed` tranche. Heat rate 10.5 → 12.6212 and 11.5 → 12.5649.
- `pmax`, `min_gen` and `availability` are byte-identical for every unit. No other unit's `mc` moves.
- Median `mc` (keeper → arm), Dahlberg / Hartwell:

  | year | Dahlberg | Hartwell |
  |---|---|---|
  | 2019 | 31.829 → 37.552 | 34.527 → 37.400 |
  | 2020 | 26.941 → 31.677 | 29.174 → 31.551 |
  | 2021 | 43.600 → 51.700 | 47.419 → 51.485 |
  | 2022 | 79.809 → 95.225 | 87.076 → 94.815 |
  | 2023 | 33.724 → 39.830 | 36.603 → 39.668 |
  | 2024 | 31.729 → 37.432 | 34.418 → 37.281 |
  | 2025 | 45.096 → 53.499 | 49.057 → 53.276 |

## 4. Greedy estimate, baseline-differenced

`_soco76_gas_census.py greedy`, record `docs/records/soco/r-soco/soco76_identity_greedy.json`.

- **Construction.** The six tranches are re-dispatched as price-takers against the leg's zone price at the keeper
  offer (baseline) and at the arm offer. The hourly arm − baseline delta is refilled from the cheapest idle headroom
  across the REFILL classes (the soco-69 rule). C1 is `calibration_verdict.score_fuelmix` on the keeper's payload;
  C4 is the scorer's construction.
- **Stated limit.** Prices are held fixed. soco-72 measured the LP moving about 3× its greedy.

| year | COAL_BIT pp | CT_PEAKER pp | ST_GAS pp | COAL_PRB pp | C4 coal NRMSE |
|---|---|---|---|---|---|
| 2019 | **−4.24 → −4.15 FAIL** | +2.71 → +2.27 | −2.06 → −1.85 | +0.71 → +0.85 | 0.263 → 0.250 |
| 2020 | −2.36 → −2.32 | +2.22 → +2.04 | −2.14 → −2.00 | = | **0.3045 → 0.3019 FAIL** |
| 2021 | +0.37 = | −0.52 → −0.53 | −2.73 → −2.71 | = | 0.208 = |
| 2022 | +1.16 = | −0.91 → −0.98 | −2.28 → −2.22 | +2.69 = | 0.240 = |
| 2023 | −1.86 = | +2.40 → +2.20 | −2.16 → −1.96 | = | 0.268 = |
| 2024 | −1.35 → −1.33 | +1.58 → +1.48 | −1.90 → −1.83 | = | 0.257 → 0.254 |
| 2025 | (skipped, preliminary) | +0.21 → +0.08 | −2.15 → −2.03 | = | 0.184 = |

2019 class deltas (TWh): CT_PEAKER −1.09, ST_GAS +0.51, COAL_PRB +0.35, COAL_BIT +0.23.

## 5. Recipe and hard stops

Each shard runs one year `<Y>` ∈ {2019, …, 2025}, pinned to the SHA that carries this document:

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install --no-deps -e .
.venv/bin/python scripts/hydrate_data.py --profile soco
PYTHONPATH=. .venv/bin/python scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. .venv/bin/python scripts/data/curate_demand_profile.py
.venv/bin/python scripts/replay_keeper.py results/calibration/soco72_span --years <Y> \
  --out-dir results/calibration/soco76_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --set egrid_identity_heat_rates=true \
  --note "soco-76 <Y>: soco-72 keeper recipe + egrid_identity_heat_rates (SOCO artifact: Dahlberg 7709<->7765, Hartwell 54538<->70454)"
```

**Hard stops.** A shard that sees otherwise stops and does not push.

- `git rev-parse HEAD` equals the pinned SHA.
- `run_config.json` `environment.packages` equals {highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3,
  pyarrow 24.0.0, pydantic 2.13.4}.
- `sha256sum data/raw/_processed-legacy/egrid_identity_heat_rates_SOCO.csv` equals `32c46c93…985f`.
- The solve log carries the line `SOCO: eGRID identity-reconciled heat rates applied to 12 generator(s) across 2
  plant(s)` (measured on the 2019 `fleet_only` build: 10 Dahlberg + 2 Hartwell EIA-860 generators).
- `scenario_config` shows all nine `--set` fields true, plus `gas_basis_differential_measured_by_year` true.
- Every band is 1.0.
- `dispatch/<Y>_P1.parquet` is present.
- `gas_prices[<Y>]` equals the keeper's value (2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52).
- The solve log carries `container preflight:` and `memory peak:`.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1 (the six tranches).** In every leg, the six Dahlberg/Hartwell tranches' median `mc` equals §3's arm column to
  ±$0.01, and every unit's hourly `cap_mw` is byte-identical to the soco72 leg.
- **E2 (direction).** Dahlberg and Hartwell energy falls in every year; CT_PEAKER falls; ST_GAS rises; COAL_BIT and
  COAL_PRB rise weakly. Nuclear, hydro, solar |Δ| ≤ 0.1 TWh.
- **E3 (the failing rows).** 2019 COAL_BIT ≈ −4.1 to −3.9 pp (at ~1–3× the greedy): **still FAIL**. 2020 C4 coal
  ≈ 0.297–0.302: at the ceiling either way; a pass is possible, not expected.
- **E4 (side effects).** 2019 and 2023 CT_PEAKER move in by ≈ 0.2–0.6 pp; 2019/2020/2023 ST_GAS move in. The thinnest
  row, 2022 COAL_PRB +2.69, is not reached by the lever (Dahlberg barely runs at 2022 gas).
- **E5.** Unserved 0 MWh every year. **E6.** C6, C8 PASS; D-2 and D-4 unchanged in kind (no floor is added).
- **Expected determination: NOT-YET** (2019 COAL_BIT, likely 2020 C4).

## 7. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff** all four hold:

1. All seven legs solve cleanly with the §5 hard stops met.
2. **The mechanism fires exactly as censused:** E1 holds in every leg.
3. No year's unserved energy increases.
4. C6 and C8 PASS, and `legitimacy_diagnostics` records no new D-4 FAIL.

**This holds whatever C1 and C4 do.** A class-default heat rate standing in for a plant's own measured rate is an
input error (rule 14); if the fix moves a row the wrong way, that is reported at full magnitude as the next
root-cause lead, never as a reason to keep the default.

The owner's standing ruling covers promotion ("If structural integrity improves but gates regress that may still be a
keeper"). If it lands: rule 35 enumerates the SOCO year union from every sidecar, runs `audit_keepers` E1, then
`prune_iso_runs --iso SOCO --force-uncite` removes `2026-09-26-soco72-gas-basis-window`.

## 8. Retrievability (rule 34(e))

- Each shard pushes its full bundle, `dispatch/<Y>_P1.parquet` included, to `claude/soco76-<Y>` through a
  `.gitignore` negation and a plain `git add`.
- The parent fetches each leg, verifies it, and composes `soco76_span`. The composite (slim set + `hourly/`), sidecar
  and payload land on `main` with this lane's PR.
- A leg not landed on `main` is costed as a re-solve, ~2 min of LP per year.
