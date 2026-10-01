# PRECOMMIT — soco-85: arm `gas_daily_shape` (Henry Hub within-month gas shape) on the SOCO keeper

Lane soco-85, 2026-09-28. Written **before any solve**. Owner ruling 2026-09-28 (soco-85 card, after
FINDING-soco-85 §4): **"Arm + solve 7 shards"**.

## 1. The object

- **Mechanism:** `gas_daily_shape` (existing `ScenarioConfig` field, default off; SOCO matrix cell U). It multiplies
  every gas plant-month's measured F923 delivered level by the measured Henry Hub daily staircase ÷ that month's own
  calendar-day mean (`fuel.hubs.gas_daily_shape_factors`). It is re-carried on the plant-monthly overwrite
  (`plant_prices.py`).
- **Why it is real structure (rule 1).** Southern dispatches against the day's gas, not the month's. The shape is
  mean-preserving per month, so it adds only the within-month commodity swing.
- **Rule 13.** A measured input that regenerates for a forecast year (a forward monthly level × a representative
  daily shape — the function's own docstring). It is not an overlay and not an outcome.
- **DOF: zero.** No new field, no new artifact, no fitted value. `henry_hub_daily.csv` is already committed and
  already consumed by CAISO / NYISO / NEISO / MISO backcasts (`backcast_config.py` default list).
- **Rule 25.** Nothing is transferred: the input is a national measured series, not another ISO's fitted number.
- **What it cannot do** (stated before the solve): carry the Southeast basis blowout. Elliott λ averages
  $407/MWh against a Henry Hub factor of 1.27 (FINDING-soco-85 §4). No free SE daily hub exists (owner ruling
  2026-09-28: "Stay free-data only").

## 2. Zero-LP census (phase 0, done)

`fleet_only` rebuild on the soco83 recipe, flag off vs on, **every year** (`_soco85_cc_incremental.fleet`):

| year | gas units | fuel ratio range | max \|month mean − 1\| |
|---|---:|---|---:|
| 2019 | 225 | 0.792–1.448 | 9e-15 |
| 2020 | 225 | 0.598–1.333 | 1e-14 |
| 2021 | 236 | 0.523–4.695 (Uri) | 1e-14 |
| 2022 | 232 | 0.627–1.432 | 1e-14 |
| 2023 | 220 | 0.735–1.276 | 1e-14 |
| 2024 | 220 | 0.535–3.287 | 1e-14 |
| 2025 | 223 | 0.637–2.143 | 1e-14 |

In every year: unit ids, `pmax`, `availability`, `heat_rate` and every non-gas fuel price are identical. §7(2) is
therefore already established at zero LP on this recipe; the shards re-check it only through the hard stops.

Greedy reach (FINDING-soco-85 §4): C3a 2021 −6.1 → −4.8 %, 2022 −16.1 → −15.7 %, 2024 −4.4 → −4.9 %, others within
0.2 pp; no status flips.

## 3. G-DRIFT (rule 29(b)) — keeper solve SHA `19d60fd6` → this PRECOMMIT's SHA

`git diff 19d60fd6 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference`: 28 files, 18 commits. **Verdict: ALL INERT** — recorded before any
shard is launched.

| reason class | files / hunks |
|---|---|
| another ISO's branch or artifact | `ISO_PLANT_ENTRIES` (ERCOT only; `plant_entry_first_inside_row("SOCO", y)` is `{}`, so `ba_membership.py` / `fleet/arrays.py` entry masks skip); `CAMPD_UNIT_PLANT_REMAP` +12 rows (LA/OK/WI facilities; SOCO reads AL/GA/MS/FL only); `eia930/demand.py` + `zonal_shares.py` (CAISO only); `solve_surface_declared.py` (ERCOT fingerprint); MISO / PJM companion artifacts |
| default-off flag absent from the recipe | `campd_split_remap_companions`, `unit_outage_rederive_peaker_windows` (also needs `unit_outage_full_rederive`, False), `caiso_tac_shares_standard_time`, `pjm_da_virtual_settle_financial` (with `pjm_da_virtual_bids`, False): `outages.py`, `campd.py`, `campd_bins.py` selectors (return plain `True` unarmed), `pipeline/solve.py`, `virtual_bids.py`, `scenarios.py`, CLI plumbing |
| scoring / reported-only / diagnostics | `actual_lmp.json` + `actual_lmp_hourly_SOCO.parquet` (soco-84 benchmark), `soco_energy_auction.py` + `paths.py` (reported-only), `resolved_inputs.py` provenance, `_benchmark_eia923_frame`, `scripts/lib/seam_neighbour_price/*` (not imported by the solve path) |

`data/raw/reference`: unchanged. **Form 4 holds: the committed `soco83_span` bundle is the control; no control solve.**

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
PYTHONPATH=. .venv/bin/python scripts/run_calibration_full.py --restore-shared-inputs results/calibration/soco83_span
.venv/bin/python scripts/replay_keeper.py results/calibration/soco83_span --years <Y> \
  --out-dir results/calibration/soco85_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --set egrid_identity_heat_rates=true --set coal_econ_marginal_hr_two_sided=true \
  --set st_gas_mustrun_per_plant=true --set st_gas_mustrun_p25_level=true \
  --set st_gas_mustrun_oom_level=true --set gas_daily_shape=true \
  --note "soco-85 <Y>: soco-83 keeper recipe + gas_daily_shape (Henry Hub within-month gas shape)"
```

**Hard stops.** A shard that sees otherwise stops and does not push.

- **Pinned SHA:** `git rev-parse HEAD` equals `<SHA>`.
- **Artifact hashes (`sha256sum`):**

| file | sha256 |
|---|---|
| `data/raw/gas-prices/henry_hub_daily.csv` | `7c2787a4001e0a6c2d7f468a77e4c2faadeb1df5d9214d9da990bfab162a4ad3` |
| `data/raw/_processed-legacy/thermal_tranches_oom_level_mw_SOCO.csv` | `722e65b582a8699df8ee947270e6ea9f3c56eac227204d474bcbf152d9d7f2ba` |
| `data/raw/campd-unit-outages-perunitdark-SOCO.csv` | `03ce606cfe118ef28e560739d12a005b2240aa112609e119c51a9f86ea2fd37c` |
| `data/raw/_processed-legacy/campd_gas_st_campaign_params_SOCO.csv` | `cc1be8f33fa267b23a0fdd13520a904a1c35522143e2210f54a2a9586d0e2dc1` |
| `data/raw/_processed-legacy/thermal_tranches_SOCO.csv` | `ab5ec265d192379551c14facc6f65d8d972f117a565bae36b0179bbf96122ad7` |

- **Solve log** carries `st_gas_mustrun_oom_level ARMED (SOCO): 3`, `container preflight:` and `memory peak:`.
- **`scenario_config`** (bundle `run_config.json`) shows all fourteen `--set` fields true — `gas_daily_shape` among
  them — plus `soco_gas_st_campaign_commitment` true.
- **Offer tuning:** every `offer_curve_by_group` band is 1.0.
- **`gas_prices[<Y>]`** equals the keeper's: 2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52 (the annual reference is
  unchanged; only the within-month shape moves).
- **Bundle:** `dispatch/<Y>_P1.parquet` is present.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1.** C3a moves by ≤ 2 pp in every year. Direction: toward λ in 2021 and 2022. No C3a status flips; 2019, 2020
  and 2022 stay FAIL. **Determination stays NOT-YET.**
- **E2.** Class energy moves by < 0.8 TWh per class-year. No C1 row flips.
- **E3.** Unserved energy is 0 in every year; C6 and C8 PASS.
- **E4.** The LP's price response in cold snaps exceeds the greedy's (the greedy is copper-plate and holds floors).

## 7. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff all five hold**:

1. **Legs clean:** all seven legs solve cleanly, with the §5 hard stops met.
2. **Fuel is the only moved input:** a `fleet_only` rebuild at the pinned SHA shows, per year, the §2 census —
   identical `pmax` / `availability` / `heat_rate` / non-gas fuel, gas monthly means preserved.
3. **No unserved-energy increase** in any year.
4. **C6 PASS and C8 PASS**, and `legitimacy_diagnostics` records no new D-4 FAIL.
5. **No C1, C2 or C4 row flips PASS → FAIL** anywhere in 2019–2025.

Price (C3a/C3b) is deliberately **not** in the rule: the mechanism is kept or dropped on structure (rule 1), and its
price effect is reported at full magnitude either way.

**If it lands (rule 35):** enumerate the SOCO year union (2019–2025), run `audit_keepers` E1, then
`prune_iso_runs --iso SOCO --force-uncite`, which removes `2026-09-28-soco83-st-oom-floor`.

**If it does not land:** nothing is committed beyond the records; the result is written up and the owner rules.

## 8. Retrievability (rule 34)

Each shard pushes its FULL bundle (including `dispatch/<Y>_P1.parquet`) to its own branch `claude/soco85-<Y>` via a
`.gitignore` negation and a plain `git add`. The parent fetches, verifies (`git ls-tree` > 0 files, hard stops),
composes `results/calibration/soco85_span` and, only if promoted, lands it on `main` before this lane's PR merges.
