# PRECOMMIT — soco-93: arm `hydro_pondage_bound` on the SOCO keeper

Lane soco-93, 2026-09-30. Written **before any solve**. Owner rulings: soco-92 card "Next lane" → **"Pondage bound
phase 0 (Recommended)"**, then soco-93 card "Pondage" → **"Build/solve (Recommended)"**. The purpose is STRUCTURE
(rule 1), not C3a.

Base: `origin/main` `241ab838` plus soco-92's five commits (PR #6896 still open at branch time; soco-92 head
`1a48c069e37483ef1aebebf53ccb3bd2b128232c`), plus soco-93 phase 0. Keeper: `2026-09-30-soco92-hydro-min-flow`
(`results/calibration/soco92_span`, solved at `a3d9249960b523008ffa11cf35d99d3f49782e9d`).

## 1. The object

- **Mechanism:** the existing `ScenarioConfig.hydro_pondage_bound` (default off; SOCO cell `U`). One link-free
  water-balance row per bounded plant-hour, `P + Spill + V(t) − V(t−1) = I(t)` with `0 ≤ V ≤ B`, cyclic. `I` is the
  plant's own monthly budget over the month's hours, and `B` is `data/raw/soco-hydro/soco_hydro_pondage.csv`. The row
  is built by `data.hydro.load_hydro_pondage` and assembled by the existing `model/lp/hydro_cascade.py` builder.
- **No new `ScenarioConfig` field and no new constant.** The new input is SOCO's own NID-derived artifact (phase 0).
  Rule 28(c) is not triggered.
- **Rule 17.** (a) Driver: each plant's measured forebay volume × head (NID). (b) Window: every hour. This is a
  RESTRICTION, not a floor: spill is unbounded, so it forces no MWh and moves no monthly total. (c) Forward story: NID is
  static (re-derived on a new vintage), and inflow is the forecast year's monthly budget, the array the LP already
  carries.
- **Rule 13.** A physical, static structure attribute. `hydro_pondage_bound` is deliberately not in the per-year
  measured-overlay registry (`scenarios.py` hydro-1 note).
- **Rule 19.** Complementary to `hydro_ror_split` (RoR-flat rows carry no pondage row) and to `hydro_min_flow_floor`
  (the floor bounds the trough, the row bounds concentration). Phase 0 measured the two as compatible: in every year and
  every bounded unit the floor is ≤ the unit's own inflow (worst case equal, a flat month), so the floor needs zero
  forebay. Mutually exclusive with `hydro_cascade_coupling`, which is not armed.
- **DOF: zero.** η = 1.0 and `Max Storage` are the builder's frozen upper-bound conventions (rule 21).
- **Rule 25.** SOCO's own dams (HILARRI v4 → NID), SOCO's own budgets. Nothing transferred.

## 2. Zero-LP phase 0 (done) — `FINDING-soco-93-pondage-phase0-2026-09-30.md`

- **Coverage:** 100 % of hydro MW linked. Rows bind for 15–16 reservoir units (829–957 MW). 12–13 large reservoirs
  (1,422–1,550 MW) hold more than a month, so their rows are redundant and not built. 14–15 units are RoR-flat.
- **Census on the keeper:** its dispatch violates the forebay in 99–120 of 179–192 bounded plant-months (52–67 %).
  0.18–0.27 TWh/yr of its hydro timing is infeasible.
- **Clip upper bound:** the cut in top-20 % λ hours is 59–77 MW against a 650–1,208 MW hydro+PS excess.

## 3. G-DRIFT (rule 29(b)) — keeper solve SHA `a3d92499` → this PRECOMMIT's base

`git diff a3d92499 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference`: 4 files, one commit (`2386952f` R-ERCOT-17). **Verdict: ALL INERT.**

- `config/scenarios.py`: adds `ercot_south_texas_pooled_basis` (default False, dropped from the cache key, ERCOT-gated,
  absent from SOCO's recipe).
- `data/fuel/basis/ercot.py` and the two `__init__` re-exports: the new `pool_ercot_south_texas_basis` function, reached
  only through that flag.
- The rest of this lane's diff is outside the solve path (`scripts/probes`, `scripts/gen_soco60b_attestation.py`, docs,
  matrix) or is a new data file read only when `hydro_pondage_bound` is armed (`data/raw/soco-hydro/`).
- **Measured (§3a):** `_soco92_gdrift_identity.py --keeper-sha a3d9249960b523008ffa11cf35d99d3f49782e9d` against
  HEAD `610f2424`. It rebuilt the keeper's LP inputs at both SHAs from one data tree. **ALL LP INPUTS BIT-IDENTICAL,
  7/7 years.**
  - The five "changed" defaults are worktree absolute paths. The one added field is `ercot_south_texas_pooled_basis`.
  - The three "changed" constants (`CAMPD_BINNING_ISOS`, `EIA930_PS_FOLDED_INTO_WAT`, `RGGI_MEMBER_STATES_BY_YEAR`)
    are set-ordering artifacts: `git diff a3d92499 HEAD -- src/market_sim/config/constants.py` is empty.
  - The pondage row is built after the `fleet_only` exit, so the instrument cannot see it by construction. It is the
    declared delta, not drift.

**Form 4 holds: the committed `soco92_span` bundle is the control. No control solve.**

## 4. Years (rules 34(c), 35(c), 36)

SOCO's registered set is the keeper, **2019–2025**. All seven are solved, one year-isolated shard per year, and the
parent composes them at zero LP.

## 5. Recipe and hard stops

Each shard runs ONE year `<Y>` ∈ {2019, …, 2025} at the pinned SHA `<SHA>` (the commit carrying this document):

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
uv sync
uv run python scripts/hydrate_data.py --profile soco
PYTHONPATH=. uv run python scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. uv run python scripts/data/curate_demand_profile.py
PYTHONPATH=. uv run python scripts/run_calibration_full.py --restore-shared-inputs results/calibration/soco92_span
uv run python scripts/replay_keeper.py results/calibration/soco92_span --years <Y> \
  --out-dir results/calibration/soco93_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --set egrid_identity_heat_rates=true --set coal_econ_marginal_hr_two_sided=true \
  --set st_gas_mustrun_per_plant=true --set st_gas_mustrun_p25_level=true \
  --set st_gas_mustrun_oom_level=true --set gas_daily_shape=true \
  --set gas_hh_monthly_shape=true --set hydro_min_flow_floor=true \
  --set hydro_pondage_bound=true \
  --note "soco-93 <Y>: soco-92 keeper recipe + hydro_pondage_bound (SOCO NID forebay)"
```

**Hard stops.** A shard that sees otherwise stops and does not push.

- **Pinned SHA:** `git rev-parse HEAD` equals `<SHA>`.
- **Artifact hashes (`sha256sum`):**

| file | sha256 |
|---|---|
| `data/raw/gas-prices/henry_hub_monthly.csv` | `88e0b68814e4a857e1079d826998c0086e2bd31735e2d8ef1a4855da1faa5926` |
| `data/raw/gas-prices/henry_hub_daily.csv` | `7c2787a4001e0a6c2d7f468a77e4c2faadeb1df5d9214d9da990bfab162a4ad3` |
| `data/raw/_processed-legacy/thermal_tranches_oom_level_mw_SOCO.csv` | `722e65b582a8699df8ee947270e6ea9f3c56eac227204d474bcbf152d9d7f2ba` |
| `data/raw/campd-unit-outages-perunitdark-SOCO.csv` | `03ce606cfe118ef28e560739d12a005b2240aa112609e119c51a9f86ea2fd37c` |
| `data/raw/_processed-legacy/campd_gas_st_campaign_params_SOCO.csv` | `cc1be8f33fa267b23a0fdd13520a904a1c35522143e2210f54a2a9586d0e2dc1` |
| `data/raw/_processed-legacy/thermal_tranches_SOCO.csv` | `ab5ec265d192379551c14facc6f65d8d972f117a565bae36b0179bbf96122ad7` |
| `data/raw/soco-hydro/soco_hydro_pondage.csv` | `abb10f83ef770fd4f36424f1db4a31d30d12a9915d2fbc9a41e45baf371b93fa` |

- **Solve log** carries:
  - `st_gas_mustrun_oom_level ARMED (SOCO): 3`;
  - `RoR split —` with 14 or 15 RoR plants (**not** "no hydro-plant-modes classifier partition");
  - `min-flow floor reconciled with the RoR split`;
  - `hydro pondage bound —` with **15 or 16** plants carrying a storage row (phase-0 census: 15 in 2019, 2021, 2022,
    2024, 2025; 16 in 2020, 2023). **Not** "INERT" and **not** "no hydro pondage artifact";
  - `container preflight:` and `memory peak:`.
- **`scenario_config`** (bundle `run_config.json`) shows all seventeen `--set` fields true, plus `hydro_ror_split` true
  and `soco_gas_st_campaign_commitment` true.
- **Offer tuning:** every `offer_curve_by_group` band is 1.0.
- **`gas_prices[<Y>]`** equals the keeper's: 2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52.
- **Bundle:** `dispatch/<Y>_P1.parquet` is present.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1 (liveness).** The arm's per-unit hydro violates the forebay in **0** bounded plant-months (census instrument,
  `_soco93_pondage_census.py --dispatch-dir <arm>`), against 99–120 for the keeper.
- **E2 (direction).** Model hydro + PS in top-20 % λ hours **falls** by no more than the clip bound (≤ 59–77 MW); low-40 %
  hours rise or hold.
- **E3 (price).** C3a moves by ≤ 0.5 pp in every year with **no status flips**. The determination stays NOT-YET.
- **E4.** Class energy moves < 0.5 TWh per class-year; hydro energy within 0.01 TWh of the keeper (spill should not be
  chosen); no C1 row flips.
- **E5.** Unserved energy is 0 in every year; C6 and C8 PASS.

## 7. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff all six hold**:

1. **Legs clean:** all seven legs solve cleanly, with the §5 hard stops met.
2. **The pondage row is the only moved input:** G-DRIFT inert (§3), and each leg's log shows the §5 pondage row count.
3. **Liveness:** E1 — zero violated bounded plant-months in the arm, in every year.
4. **No unserved-energy increase** in any year.
5. **C6 PASS and C8 PASS**, and `legitimacy_diagnostics` records no new D-4 FAIL.
6. **No C1, C2 or C4 row flips PASS → FAIL** anywhere in 2019–2025.

Price (C3a/C3b) is deliberately **not** in the rule. The mechanism is kept or dropped on structure, and its price effect
is reported at full magnitude either way.

**Promotion itself needs an owner ruling (rule 31).** If §7 holds, the parent surfaces the promotion question. On a yes
(rule 35): enumerate the SOCO year union (2019–2025), register, run `audit_keepers` E1, then
`prune_iso_runs --iso SOCO --force-uncite`, which removes `2026-09-30-soco92-hydro-min-flow`. If §7 fails, the run is
registered as a probe (rule 15) and the owner rules.

## 8. Retrievability (rule 34)

Each shard pushes its FULL bundle (including `dispatch/<Y>_P1.parquet`) to its own branch `claude/soco93-<Y>`, using
`printf '\n!results/calibration/soco93_<Y>/**\n!results/calibration/soco93_<Y>/dispatch/\n' >> .gitignore` and then a
plain `git add .gitignore results/calibration/soco93_<Y>`. The parent fetches and verifies each leg
(`git ls-tree` > 0 files, the hard stops), composes `results/calibration/soco93_span`, and lands it on `main` before
this lane's PR merges.
