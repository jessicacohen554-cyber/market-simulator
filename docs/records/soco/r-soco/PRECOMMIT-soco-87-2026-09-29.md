# PRECOMMIT — soco-87: arm `gas_hh_monthly_shape` (measured Henry Hub MONTHLY gas shape) on the SOCO keeper

Lane soco-87, 2026-09-29. Written **before any solve**. Owner ruling 2026-09-29 (soco-87 card, after
FINDING-soco-87 §5): **"Arm + solve 7 shards (Recommended)"**.

## 1. The object

- **Mechanism:** `gas_hh_monthly_shape` (existing `ScenarioConfig` field, default off; armed on the ERCOT keeper; off
  on the SOCO keeper). In `fuel.gas_seasonal_shape` it **replaces** the generic climatological
  `GAS_MONTHLY_SEASONALITY` (identical in every year) with the measured Henry Hub monthly shape for the solve year,
  `HH_m / hour-weighted mean(HH_year)`. The annual level (keeper `gas_prices` + soco-72 measured basis) is unchanged,
  and `gas_daily_shape` still normalizes within each month on top.
- **Why it is real structure (rule 1).** The keeper's gas price runs the wrong way through 2021 and 2022: the generic
  shape makes January the dearest month while Henry Hub rose through the year. That is a known-wrong input, and this
  replaces it with the measured one.
- **Rule 13.** A measured commodity price. For a forecast year with no HH rows the code falls back to the generic shape
  (the futures-strip analogue). It is not an overlay and not an outcome.
- **Rule 19.** It replaces the generic shape and stacks on nothing.
- **DOF: zero.** No new field, no fitted value. `henry_hub_monthly.csv` is already committed and already read by the
  ERCOT keeper.
- **Rule 25.** Nothing is transferred: the input is a national measured series, not ERCOT's verdict. This is SOCO's own test.
- **What it cannot do** (stated before the solve): the 2022 December Elliott week, and the 2024/2025 January cold
  snaps. Those are daily SE-basis spikes (owner: "Stay free-data only"). Nor can it fix the 2019/2020 C3a level
  offset, because the shape is mean-preserving.

## 2. Zero-LP census (phase 0, done)

`fleet_only` rebuild on the soco85 keeper recipe, flag off vs on, **every year**
(`scripts/probes/_soco87_c3b_monthly.py --census`):

| year | units moved | fuel types moved | max \|annual mean ratio − 1\| | monthly fuel ratio |
|---|---:|---|---:|---|
| 2019 | 225 / 339 | gas only | 2.7e-4 | 0.733–1.143 |
| 2020 | 225 / 340 | gas only | 2.7e-4 | 0.855–1.236 |
| 2021 | 236 / 347 | gas only | 2.7e-4 | 0.605–1.490 |
| 2022 | 232 / 348 | gas only | 2.7e-4 | 0.593–1.442 |
| 2023 | 220 / 328 | gas only | 2.7e-4 | 0.842–1.236 |
| 2024 | 220 / 329 | gas only | 2.7e-4 | 0.666–1.257 |
| 2025 | 223 / 353 | gas only | 2.7e-4 | 0.870–1.146 |

In every year: unit ids, `pmax`, `availability`, `heat_rate`, `min_gen` and every non-gas fuel price are identical.
The 2.7e-4 residual is the generic shape's own hour-weighting: its mean over 8,760 h is not exactly 1. Every year
carries the same value, so it is a property of the shape being replaced, not of the arm.

Greedy reach (FINDING-soco-87 §4, same marginal unit, no reshuffle): C3b 2020 0.222→0.191, 2021 0.260→0.149, 2022
0.389→0.284, 2024 0.277→0.192; passing years stay passing (2025 0.174→0.184). C3a moves ≤ 3.2 pp, with no flips.

## 3. G-DRIFT (rule 29(b)) — keeper solve SHA `599df6a0` → `29ec2b9c` (this PRECOMMIT's base)

`git diff 599df6a0 29ec2b9c -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference` covers 24 files and 12 commits: SPP-100, NWPP-NEXT-8, SPP-99, R-CAISO-13,
NYISO-NEXT-11, PJM-NEXT-8 and merges. None is a SOCO lane. **Verdict: ALL INERT**, recorded before any shard is launched.
(This PRECOMMIT's commit adds only docs and a probe on top of `29ec2b9c`.)

| reason class | files / hunks |
|---|---|
| default-off flag absent from / false in the recipe | new fields `nyiso_ne_ac_node`, `coal_fuel_inventory_monthly_pile`, `unit_outage_exit_cohort_repair`, `chp_steam_floor_conduct_scope`, `caiso_eia930_clock_repair` (all default False, no default flips, no new `__post_init__` coercion, dropped from the key at default); `outages.py` / `fleet/arrays.py` dated-exit shares (`_dated_shares is None`); `fleet/assembly.py` CHP conduct scope (needs `chp_steam_floor_p25`, False); `campd_bins.py` selector (`campd_split_remap_companions` False); `run_calibration.py::resolve_coal_monthly_pile`; `lp/rows.py` coal-yard block (not built for SOCO) and `coal_fuel_inventory.py` |
| another ISO's branch | NYISO NE AC node (`interchange/spec.py`, `nyiso.py`, `registry.py`, `nyiso_par_attribution.py`, `pipeline/commitment.py` NYISO bridge, run_calibration hub/TTC hunks, all gated `iso == "NYISO"`); CAISO EIA-930 clock repair (`eia930/frames.py` gated `ba_code == "CISO"`, `eia930/demand.py` CAISO loaders, run_calibration `iso == "CAISO"`); `nyiso_firm_imports` retired (False everywhere) |
| provenance / governance | `resolved_inputs.py`; `forecast_parity_registry.py`; `solve_surface_declared.py` (two new constants at their declared hash: the SOCO provenance fingerprint moves `a66095bf…` → `a8190617…` over 192 → 194 rows, and `moved_rows('SOCO')` is identical, so the cache key is unmoved); docstring-only edits in `caiso.py` / `miso.py` / `import_nodes.py` |

`data/raw/reference`, `data/raw/_validation-source`: unchanged. **Form 4 holds: the committed `soco85_span` bundle is the
control; no control solve.**

## 4. Years (rule 34(c), rule 35(c))

SOCO's only registered run is the keeper, years **2019–2025**. All seven are solved. Rule 36: **one year-isolated
shard per year**, composed by the parent at zero LP.

## 5. Recipe and hard stops

Each shard runs ONE year `<Y>` ∈ {2019, …, 2025} at the pinned SHA `<SHA>`, the commit carrying this document:

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
uv venv .venv && uv pip install -r requirements.txt && uv pip install --no-deps -e .
.venv/bin/python scripts/hydrate_data.py --profile soco
PYTHONPATH=. .venv/bin/python scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. .venv/bin/python scripts/data/curate_demand_profile.py
PYTHONPATH=. .venv/bin/python scripts/run_calibration_full.py --restore-shared-inputs results/calibration/soco85_span
.venv/bin/python scripts/replay_keeper.py results/calibration/soco85_span --years <Y> \
  --out-dir results/calibration/soco87_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --set egrid_identity_heat_rates=true --set coal_econ_marginal_hr_two_sided=true \
  --set st_gas_mustrun_per_plant=true --set st_gas_mustrun_p25_level=true \
  --set st_gas_mustrun_oom_level=true --set gas_daily_shape=true \
  --set gas_hh_monthly_shape=true \
  --note "soco-87 <Y>: soco-85 keeper recipe + gas_hh_monthly_shape (measured Henry Hub monthly shape)"
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

- **Solve log** carries `st_gas_mustrun_oom_level ARMED (SOCO): 3`, `container preflight:` and `memory peak:`.
- **`scenario_config`** (bundle `run_config.json`) shows all fifteen `--set` fields true (`gas_daily_shape` and
  `gas_hh_monthly_shape` among them) plus `soco_gas_st_campaign_commitment` true.
- **Offer tuning:** every `offer_curve_by_group` band is 1.0.
- **`gas_prices[<Y>]`** equals the keeper's: 2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52 (the annual reference is
  unchanged; only the monthly shape moves).
- **Bundle:** `dispatch/<Y>_P1.parquet` is present.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1.** C3b falls in 2020, 2021, 2022 and 2024. 2022 stays FAIL. 2020 and 2024 sit near the 0.20 line, so either
  side is possible (greedy 0.191 / 0.192).
- **E2.** No C3a status flips. 2019, 2020 and 2022 stay FAIL. **Determination stays NOT-YET.**
- **E3.** Class energy moves by < 1.5 TWh per class-year. A monthly gas shape shifts coal/gas switching between
  months, so this is looser than soco-85's 0.8. No C1 row flips.
- **E4.** Unserved energy is 0 in every year; C6 and C8 PASS.

## 7. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff all five hold**:

1. **Legs clean:** all seven legs solve cleanly, with the §5 hard stops met.
2. **Fuel is the only moved input:** the §2 census holds at the pinned SHA.
3. **No unserved-energy increase** in any year.
4. **C6 PASS and C8 PASS**, and `legitimacy_diagnostics` records no new D-4 FAIL.
5. **No C1, C2 or C4 row flips PASS → FAIL** anywhere in 2019–2025.

Price (C3a/C3b) is deliberately **not** in the rule: the mechanism is kept or dropped on structure (rule 1), and its
price effect is reported at full magnitude either way.

**If it lands (rule 35):** enumerate the SOCO year union (2019–2025), run `audit_keepers` E1, then
`prune_iso_runs --iso SOCO --force-uncite`, which removes `2026-09-28-soco85-gas-daily-shape`.

**If it does not land:** nothing is committed beyond the records; the result is written up and the owner rules.

## 8. Retrievability (rule 34)

Each shard pushes its FULL bundle (including `dispatch/<Y>_P1.parquet`) to its own branch `claude/soco87-<Y>` via a
`.gitignore` negation and a plain `git add`. The parent fetches, verifies (`git ls-tree` > 0 files, hard stops),
composes `results/calibration/soco87_span` and, only if promoted, lands it on `main` before this lane's PR merges.
