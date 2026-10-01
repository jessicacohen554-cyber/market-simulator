# PRECOMMIT — soco-96: arm `dual_fuel_measured_oil_burn` on the SOCO keeper

Lane soco-96, 2026-09-30. Written **before any solve**.

- **Owner ruling:** soco-96 build card → **"Oil price at measured burn"**.
- **What the ruling was given:** the card stated the phase-0 finding that no candidate admissibly closes a ledgered row. It named this arm's reach, C3a 2022 +0.07–0.14 $/MWh, and said its admissibility is contested under rule 13.
- **Purpose:** the arm is built because the owner ruled it, not because it moves a residual (rules 1/13/14).
- **Keeper:** `2026-09-30-soco93-pondage-bound`, bundle `results/calibration/soco93_span`, solved at `68f900961b1858466abede9756cff22b19807ba5`.

## 1. The object

- **Field:** `ScenarioConfig.dual_fuel_measured_oil_burn`.
  - New in commit `cdaed8c2`. Default False.
  - Registered in `_CACHE_KEY_OPTIONAL_FIELDS` at its declared False, so no committed key moves.
  - Listed in `_BACKCAST_ONLY_OVERLAY_FIELDS`.
  - The matrix row was added in the same commit: SOCO cell `O`, every other ISO `U`.
- **What it does:** each gas generator at a plant with a measured row is priced, on each covered day, at `f·oil + (1−f)·gas`.
  - `oil` is the dual-fuel switch's EIA-923 monthly delivered petroleum series.
  - `gas` is the cell's final delivered gas price, after the F923/hub/zonal overlays.
- **How f is measured:** f is the plant-day oil share of heat input. The CO2/heat-input mixing identity runs at plant-day grain over gas-primary units.
  - Units are excluded when coal-capable: a coal code in EIA-860 Energy Source 1–6, via the CAMD-EIA crosswalk, at the solve-year vintage.
  - The factors are those of 40 CFR Part 75 App. G Eq. G-4, the basis CAMPD books `co2Mass` on. The rule-14 reconciliation against the Part 98 factors is in `constants.py`.
- **The artifact:** `data/raw/_processed-legacy/campd_measured_oil_burn_days_SOCO.csv`, produced by `scripts/data/derive_measured_oil_burn_days.py`.

| year | plant-days f>0 | plants | mean f | days f≥0.01 |
|---|---|---|---|---|
| 2019 | 5,546 | 45 | 0.0088 | 158 |
| 2020 | 5,397 | 44 | 0.0105 | 161 |
| 2021 | 5,371 | 45 | 0.0177 | 241 |
| 2022 | 5,743 | 46 | 0.0203 | 266 |
| 2023 | 4,992 | 41 | 0.0165 | 209 |
| 2024 | 5,087 | 41 | 0.0153 | 227 |
| 2025 | 5,179 | 42 | 0.0213 | 213 |

- **Rule 19:** the written mask is the switch's `skip_cells`, so on covered cells the measured mix REPLACES `min(gas, oil)`. `dual_fuel_switching` is not armed for SOCO, so this is inert here either way.
- **Rule 13, stated rather than hidden:** the trigger is the unit's measured fuel conduct in that year.
  - It is admitted by owner ruling as a backcast-only measured physical input, analogous to CAMPD outage windows.
  - Its forward substitute is `dual_fuel_switching`'s price-parity switch.
  - The phase-0 lane judged the trigger inadmissible. Whether an arm built on it can be a keeper is the owner's call under rule 13, and §7 says so.
- **DOF: zero.** No threshold and no scaling. Both factors are published regulatory constants.
- **Rule 25:** SOCO's own CEMS, EIA-860 and EIA-923. Nothing is transferred.
- **Zero-LP footprint** (fleet_only rebuild of the soco93 recipe, on vs off):

| year | generator-hours changed | gas generators changed | capacity-weighted mean Δ, all gas ($/MMBtu) |
|---|---|---|---|
| 2019 | 511,224 | 170 | +0.035 |
| 2020 | 505,536 | 166 | +0.026 |
| 2021 | 524,928 | 182 | +0.062 (min −10.77 in Uri) |
| 2022 | 573,840 | 179 | +0.153 |
| 2023 | 486,648 | 164 | +0.114 |
| 2024 | 494,400 | 164 | +0.099 |
| 2025 | 503,688 | 168 | +0.113 |

- **Elliott window, 2022-12-23..26:** +$1.69/MMBtu across all gas, +$2.04 on the 147 affected generators (about 21.3 GW).
- **Phase-0 reach** (`scratchpad/phase0/PHASE0-soco96.md`): C3a 2022 +0.07–0.14 at measured burn. C3b 2022 ≤ −0.005 (stays FAIL). C1: 0 in all years.

## 2. Phase 0 (done, zero LP)

`PHASE0-soco96.md` measured four candidates. Elliott 2022 is a quantity gap of about 8 GW, not a fuel-price gap: λ exceeds the whole cost stack in 24 % of its hours. 2019, 2020, 2021 and 2023 carry no cold window.

## 3. G-DRIFT (rule 29(b)) — keeper solve SHA `68f90096` → this PRECOMMIT's base

**Verdict: ALL INERT, measured.**

The instrument is `scripts/probes/_soco92_gdrift_identity.py --keeper-sha 68f900961b1858466abede9756cff22b19807ba5`, run against HEAD `cdaed8c2`. It rebuilt the keeper's LP inputs at both SHAs from one data tree. Result: **ALL LP INPUTS BIT-IDENTICAL, 7/7 years**. The record is `results/calibration/_soco96/gdrift_input_identity.json`, not committed.

What the instrument reported as changed or added, and why none of it reaches SOCO:
- **5 "changed" defaults:** all worktree absolute paths.
- **13 added fields:** all default-off, and none is in SOCO's recipe. They include this lane's own `dual_fuel_measured_oil_burn`, the declared delta.
- **Two "changed" constants:** `CAMPD_BINNING_ISOS` and `RGGI_MEMBER_STATES_BY_YEAR`. These are the known set-ordering artifacts (soco-93 §3).
- **Added constants:** unreferenced unless their gates are armed.

The reading half covers what sits after the `fleet_only` exit: `model/lp/rows.py`, `model/interchange/*`, `runner.py`, `pipeline/*` and `data/eia930/*`. Every hunk from `68f90096` to `cdaed8c2` there is NYISO-gated (`nyiso_import_landing_band`, `nyiso_fg_split`) or CAISO-gated (clock repair, unprinted-year gas). SOCO never enters those branches.

**Form 4 holds: the committed `soco93_span` bundle is the control. No control solve.**

## 4. Years (rules 34(c), 35(c), 36)

SOCO's registered set is the keeper, **2019–2025**. All seven years are solved, one year-isolated shard per year. The
parent composes them at zero LP.

## 5. Recipe and hard stops

Each shard runs ONE year `<Y>` ∈ {2019, …, 2025} at the pinned SHA `<SHA>` (the commit carrying this document):

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
uv sync
uv run python scripts/hydrate_data.py --profile soco
PYTHONPATH=. uv run python scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. uv run python scripts/data/curate_demand_profile.py
PYTHONPATH=. uv run python scripts/run_calibration_full.py --restore-shared-inputs results/calibration/soco93_span
uv run python scripts/replay_keeper.py results/calibration/soco93_span --years <Y> \
  --out-dir results/calibration/soco96_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --set egrid_identity_heat_rates=true --set coal_econ_marginal_hr_two_sided=true \
  --set st_gas_mustrun_per_plant=true --set st_gas_mustrun_p25_level=true \
  --set st_gas_mustrun_oom_level=true --set gas_daily_shape=true \
  --set gas_hh_monthly_shape=true --set hydro_min_flow_floor=true \
  --set hydro_pondage_bound=true --set dual_fuel_measured_oil_burn=true \
  --note "soco-96 <Y>: soco-93 keeper recipe + dual_fuel_measured_oil_burn (CAMPD plant-day oil share)"
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
| `data/raw/_processed-legacy/campd_measured_oil_burn_days_SOCO.csv` | `7ea8096be5257e817d669245ee5c84fca10bd97cc54c5fd0f9490f8328409edf` |

- **The solve log carries:**
  - `measured oil burn (SOCO <Y>): N gas tranches`, where N matches the §1 census: 170 / 166 / 182 / 179 / 164 / 164 / 168 for 2019–2025.
  - Everything soco-93's legs showed: `st_gas_mustrun_oom_level ARMED (SOCO): 3`, the RoR split, `min-flow floor reconciled with the RoR split`, and `hydro pondage bound —` with 15/16 plants.
  - `container preflight:` and `memory peak:`.
- **`scenario_config`** (bundle `run_config.json`) shows all eighteen `--set` fields true.
- **Offer tuning:** every `offer_curve_by_group` band is 1.0.
- **`gas_prices[<Y>]`** equals the keeper's: 2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52.
- **Bundle:** `dispatch/<Y>_P1.parquet` is present.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1 (liveness).** Each leg's log shows the §5 tranche count, and the solve's fuel-price array differs from the keeper's only on covered gas cells.
- **E2 (price).** C3a moves by ≤ +0.3 pp in every year except 2021 and 2022, and by ≤ +1.0 pp in 2022. There are no C3a status flips. The determination stays NOT-YET on the caveat budget.
- **E3.** C3b 2022 stays FAIL / ledgered (phase-0 bound ≤ −0.005 NRMSE).
- **E4.** Class energy moves < 0.5 TWh per class-year, and no C1 row flips. Oil-burning gas units lose energy to gas-only units in covered days.
- **E5.** Unserved energy is 0 in every year. C6 and C8 PASS.

## 7. Promotion recommendation rule (fixed now)

The parent RECOMMENDS this run as the SOCO keeper **iff all five hold**:

1. **Legs clean:** all seven legs solve cleanly, with the §5 hard stops met.
2. **The measured mix is the only moved input:** G-DRIFT inert (§3), and every leg's tranche count matches §5.
3. **No unserved-energy increase** in any year.
4. **C6 PASS and C8 PASS**, and no new D-4 FAIL.
5. **No C1, C2 or C4 row flips PASS → FAIL** anywhere in 2019–2025.

Price is not in the rule.

**Even when §7 holds, the recommendation carries the rule-13 flag.** The trigger is measured conduct. Rule 13 says a measured input that fails its forward test "must never be enabled in a keeper". The owner admitted it as a backcast-only physical input, so promotion needs an explicit owner ruling (rule 31) that says so.

On a yes (rule 35):
1. Enumerate the SOCO year union (2019–2025).
2. Register the run.
3. Run `audit_keepers` E1.
4. Run `prune_iso_runs --iso SOCO --force-uncite`, which removes `2026-09-30-soco93-pondage-bound`.

If §7 fails, the run is registered as a probe (rule 15) and the owner rules.

## 8. Retrievability (rule 34)

Each shard pushes its FULL bundle, including `dispatch/<Y>_P1.parquet`, to its own branch `claude/soco96-<Y>`:

```
printf '\n!results/calibration/soco96_<Y>/**\n!results/calibration/soco96_<Y>/dispatch/\n' >> .gitignore
git add .gitignore results/calibration/soco96_<Y>
```

The parent then:
1. Fetches and verifies each leg: `git ls-tree` returns more than 0 files, and the hard stops hold.
2. Composes `results/calibration/soco96_span`.
3. Lands the composed span on `main` before this lane's PR merges.
