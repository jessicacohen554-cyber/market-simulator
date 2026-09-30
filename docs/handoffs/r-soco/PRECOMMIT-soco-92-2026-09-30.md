# PRECOMMIT — soco-92 Track A: arm the RECONCILED reservoir min-flow floor (`hydro_min_flow_floor` under `hydro_ror_split`) on the SOCO keeper

Lane soco-92, 2026-09-30. Written **before any solve**. Owner ruling 2026-09-29 (soco-91 card, hydro shape):
**"Queue as next SOCO lane (Recommended)"** — build the rule-19 reconciled reservoir floor for **structure (rule 1),
not for C3a**, plus PS cycling depth only if a measured, year-regenerable driver exists.

Base: `origin/main` `ac7d36d6` plus soco-91's two commits (PR #6889 still open at branch time; soco-91 head
`d5c9482705ef1149c523320b849803cb687a58a6`). Keeper: `2026-09-29-soco87-gas-hh-monthly` (`results/calibration/soco87_span`).

## 1. The object

- **Mechanism:** the existing `ScenarioConfig.hydro_min_flow_floor` (default off; SOCO cell `O`), armed **with** the
  keeper's `hydro_ror_split` (K). With both on, `data.hydro.build_hydro_fleet` reduces the fleet's measured monthly Q95
  low-flow level (EIA-930 `NG: WAT`, `measured_hydro_min_flow_level`) by the RoR class's stamped flat base and
  allocates the remainder over the **reservoir class only**, pro rata by each plant's own monthly budget. Total forced
  sustained base = the Q95 level exactly. This is the re-open path soco-hydro-4 §2 named ("a reconciled ARM 1 + 2 arm
  is a real follow-up") and the matrix cell records.
- **No new `ScenarioConfig` field, no new constant, no new artifact.** The reconciliation is already in code
  (`hydro.py` "min-flow floor reconciled with the RoR split"). Rule 28(c) is not triggered.
- **Rule 17.** (a) Driver: FERC-licence minimum releases and inflow a reservoir cannot hold back. (b) Window: all 24 h,
  month-constant, so no diurnal shape is pinned; it binds where the LP would push the reservoir class below the
  sustained level (measured: nights, wet season). (c) Forward story: the solve year's own EIA-930 series in a backcast,
  the pooled `HYDRO_CLIMATOLOGY_YEARS` per-month percentile for a forecast year (existing code path).
- **Rule 13.** A measured physical availability input (a low-flow index), month-constant, not an outcome.
- **Rule 14 misalignment, bounded.** SOCO's pre-2024-07-15 `NG: WAT` folds pumped-storage *discharge*. On 2025 (the
  one clean year) folding PS discharge back in moves the monthly Q05 by **0 to +12 MW** (≤ 2.4 %), because PS
  discharges at peak, not in low-flow hours. December 2024 has a 1,343 h EIA-930 gap, so that month's level is 0 and it
  carries no floor (soco-hydro-4 ‡). Both are recorded and not repaired.
- **Rule 19.** One family with `hydro_ror_split`, reconciled by construction and never stacked. No other mechanism
  floors SOCO conventional hydro.
- **DOF: zero.** The percentile is the ceiling's mirror (`HYDRO_MIN_FLOW_PERCENTILE`), and the allocation is by measured
  budget.
- **Rule 25.** SOCO's own EIA-930 series and its own ORNL EHA partition. Nothing transferred.

## 2. Zero-LP phase 0 (done) — `scripts/probes/_soco92_hydro_phase0.py`

A `fleet_only` rebuild of the keeper recipe, floor off vs on, every year. **The only moved array is `min_gen` on
reservoir-class hydro units** (27–28 units per year). `pmax`, `availability` and `mc_base` are identical for every
unit. RoR plants: 15/43 (2019–2021), 14/42 (2022–2023, 2025), 14/42 (2024).

Reconciled reservoir floor (MW, by month) and a **lower bound** on keeper binding (fleet reservoir dispatch below the
fleet floor; the floor is per plant, so real binding is higher):

| year | Q95 level Jan–Dec (MW) | reservoir floor > 0 in | floor avg MW | keeper hours below | lift GWh |
|---|---|---|---:|---:|---:|
| 2019 | 1716 912 1064 598 247 163 76 54 46 44 195 338 | Jan–Apr, Dec | 189 | 1,917 | 774 |
| 2020 | 1179 909 1525 647 281 134 73 92 118 270 304 528 | Jan–Apr, Dec | 218 | 2,025 | 840 |
| 2021 | 328 639 394 516 245 287 386 128 386 278 226 330 | Feb–Apr, Jul, Sep | 43 | 1,759 | 176 |
| 2022 | 537 671 1260 574 162 89 84 75 54 49 91 369 | Jan–Apr, Dec | 124 | 2,181 | 601 |
| 2023 | 622 895 600 381 260 108 78 61 60 48 47 74 | Jan–Mar | 42 | 760 | 102 |
| 2024 | 232 548 704 294 229 61 55 51 63 66 85 0 | Feb–Apr | 27 | 697 | 80 |
| 2025 | 269 298 452 307 582 252 70 101 49 48 77 59 | Jan, Mar, May | 23 | 1,246 | 89 |

The keeper's reservoir class reaches **0 MW** in every year (`hydro_ror_split` keeps only the RoR base on). The floor
moves reservoir energy from the price peaks into the wet-season nights and shoulders. That is the direction soco-91 §4
measured (model hydro + PS 140–570 MW short at night, 650–1,200 MW long at peak).

**PS cycling depth — NOT BUILT (no measured driver).** On 2025, the one year with a clean `NG: PS` column:

| | discharge TWh | charge TWh | RTE |
|---|---:|---:|---:|
| keeper | 2.457 | 3.056 | 0.804 |
| EIA-930 | 1.956 | 2.412 | 0.811 |

The model's round-trip efficiency already matches the measured one. It cycles **~26 % more energy on both sides**,
which is a price-amplitude outcome (the NEISO/PJM `G` reasoning), not a physical parameter. One clean year cannot
identify a year-regenerable driver. Pinning the volume would pin an outcome (rule 13). `pumped_storage_cycling_depth`
stays `U`, with this note.

## 3. G-DRIFT (rule 29(b)) — keeper solve SHA `e44cf620` → this PRECOMMIT's base

`git diff e44cf620 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference`: 33 files, 23 commits (SPP-102, miso-286, R-CAISO-15, R-ERCOT-14/15,
NYISO-NEXT-12/13, NWPP-NEXT-9/10, soco-88). **Verdict: ALL INERT.**

- **Measured, not argued:** `scripts/probes/_soco92_gdrift_identity.py` (the soco-73 instrument) rebuilt the keeper's
  LP inputs at both SHAs from one data tree. **ALL LP INPUTS BIT-IDENTICAL, 7/7 years.** The five "changed" defaults
  are worktree absolute paths (`campd_bins_path`, `control_retrofit_path`, `plant_emission_rates{,_v2}_path`,
  `plant_registry_path`). The six added fields are default-off and absent from the recipe: `coal_monthly_pile_measured_receipts`,
  `ercot_swcap_vintage`, `miso_gas_ecomin_online_floor`, `nyiso_ne_ac_recon_detach`, `spp_commitment_posture`,
  `unit_outage_exit_ym_from_eia860`.
- **LP construction (read):**
  - `lp/rows.py`, `lp/model.py`, `reserves/spec.py`, `pipeline/{solve,kwargs,year}.py`: SPP-102 posture rows and the
    `zero_posture_markup`, both gated on `spp_commitment_posture`.
  - `pipeline/commitment.py`, `runner.py`, `run_calibration_full.py`: miso-286 EcoMin floor (default off,
    MISO-gated), NYISO-NEXT-12 topology thread (`iso == "NYISO"`).
  - `model/storage.py`: R-CAISO-15 battery envelope, gated `caiso_eia930_clock_repair` / CAISO.
  - `pipeline/spec.py`: R-ERCOT-14 `ercot_swcap_vintage` (default off).
  - `data/raw/reference`: Oklaunion ERCOT rows, NWPP plant-basis, and soco-88's SOCO rows in
    `iso-gas-capacity-state-weights.csv`. The last is read only by `gas_electric_power_monthly_level` (R, off).

**Form 4 holds: the committed `soco87_span` bundle is the control. No control solve.**

## 4. Years (rules 34(c), 35(c), 36)

SOCO's registered set is the keeper, **2019–2025**. All seven are solved, one year-isolated shard per year, composed
by the parent at zero LP.

## 5. Recipe and hard stops

Each shard runs ONE year `<Y>` ∈ {2019, …, 2025} at the pinned SHA `<SHA>` (the commit carrying this document):

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
uv sync
uv run python scripts/hydrate_data.py --profile soco
PYTHONPATH=. uv run python scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. uv run python scripts/data/curate_demand_profile.py
PYTHONPATH=. uv run python scripts/run_calibration_full.py --restore-shared-inputs results/calibration/soco87_span
uv run python scripts/replay_keeper.py results/calibration/soco87_span --years <Y> \
  --out-dir results/calibration/soco92_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --set egrid_identity_heat_rates=true --set coal_econ_marginal_hr_two_sided=true \
  --set st_gas_mustrun_per_plant=true --set st_gas_mustrun_p25_level=true \
  --set st_gas_mustrun_oom_level=true --set gas_daily_shape=true \
  --set gas_hh_monthly_shape=true --set hydro_min_flow_floor=true \
  --note "soco-92 <Y>: soco-87 keeper recipe + hydro_min_flow_floor (reconciled under hydro_ror_split)"
```

**Hard stops.** A shard that sees otherwise stops and does not push.

- **Pinned SHA:** `git rev-parse HEAD` equals `<SHA>`.
- **Artifact hashes (`sha256sum`)**, unchanged from PRECOMMIT-soco-87 §5:

| file | sha256 |
|---|---|
| `data/raw/gas-prices/henry_hub_monthly.csv` | `88e0b68814e4a857e1079d826998c0086e2bd31735e2d8ef1a4855da1faa5926` |
| `data/raw/gas-prices/henry_hub_daily.csv` | `7c2787a4001e0a6c2d7f468a77e4c2faadeb1df5d9214d9da990bfab162a4ad3` |
| `data/raw/_processed-legacy/thermal_tranches_oom_level_mw_SOCO.csv` | `722e65b582a8699df8ee947270e6ea9f3c56eac227204d474bcbf152d9d7f2ba` |
| `data/raw/campd-unit-outages-perunitdark-SOCO.csv` | `03ce606cfe118ef28e560739d12a005b2240aa112609e119c51a9f86ea2fd37c` |
| `data/raw/_processed-legacy/campd_gas_st_campaign_params_SOCO.csv` | `cc1be8f33fa267b23a0fdd13520a904a1c35522143e2210f54a2a9586d0e2dc1` |
| `data/raw/_processed-legacy/thermal_tranches_SOCO.csv` | `ab5ec265d192379551c14facc6f65d8d972f117a565bae36b0179bbf96122ad7` |

- **Solve log** carries:
  - `st_gas_mustrun_oom_level ARMED (SOCO): 3`;
  - `RoR split —` with 14 or 15 RoR plants (**not** "no hydro-plant-modes classifier partition");
  - `min-flow floor reconciled with the RoR split`;
  - `container preflight:` and `memory peak:`.
- **`scenario_config`** (bundle `run_config.json`) shows all sixteen `--set` fields true, plus `hydro_ror_split` true
  and `soco_gas_st_campaign_commitment` true.
- **Offer tuning:** every `offer_curve_by_group` band is 1.0.
- **`gas_prices[<Y>]`** equals the keeper's: 2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52.
- **Bundle:** `dispatch/<Y>_P1.parquet` is present.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1 (liveness).** In every year the reservoir floor binds in at least the §2 lower-bound hours. The reservoir class
  has no 0 MW hour in a month whose floor is > 0.
- **E2 (direction).** Model hydro + PS discharge in soco-91's low-40 % λ hours **rises** toward EIA-930, and in the
  top-20 % hours **falls**, in every year with a floor > 0. The largest moves are in 2019, 2020 and 2022.
- **E3 (price).** C3a moves by ≤ 1.5 pp in every year, with **no status flips** (soco-91 §4 perfect-hindsight bound:
  ≤ 1.1 pp). **Determination stays NOT-YET.**
- **E4.** Class energy moves < 1.0 TWh per class-year; hydro energy is unchanged (the budget is unchanged); no C1 row
  flips.
- **E5.** Unserved energy is 0 in every year; C6 and C8 PASS.

## 7. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff all six hold**:

1. **Legs clean:** all seven legs solve cleanly, with the §5 hard stops met.
2. **Hydro floor is the only moved input:** the §2 census holds at the pinned SHA (only reservoir-hydro `min_gen`
   moves).
3. **Liveness:** the reservoir floor binds (E1) in every year where it is > 0.
4. **No unserved-energy increase** in any year.
5. **C6 PASS and C8 PASS**, and `legitimacy_diagnostics` records no new D-4 FAIL.
6. **No C1, C2 or C4 row flips PASS → FAIL** anywhere in 2019–2025.

Price (C3a/C3b) is deliberately **not** in the rule. Per the owner's ruling, the mechanism is kept or dropped on
structure, and its price effect is reported at full magnitude either way.

**Promotion itself needs an owner ruling (rule 31).** If §7 holds, the parent surfaces the promotion question. On a yes
(rule 35): enumerate the SOCO year union (2019–2025), register, run `audit_keepers` E1, then
`prune_iso_runs --iso SOCO --force-uncite`, which removes `2026-09-29-soco87-gas-hh-monthly`. If §7 fails, the run is
registered as a probe (rule 15) and the owner rules.

## 8. Retrievability (rule 34)

Each shard pushes its FULL bundle (including `dispatch/<Y>_P1.parquet`) to its own branch `claude/soco92-<Y>`, using
`printf '\n!results/calibration/soco92_<Y>/**\n!results/calibration/soco92_<Y>/dispatch/\n' >> .gitignore` and then a
plain `git add .gitignore results/calibration/soco92_<Y>`. The parent fetches and verifies each leg
(`git ls-tree` > 0 files, the hard stops), composes `results/calibration/soco92_span`, and lands it on `main` before
this lane's PR merges.
