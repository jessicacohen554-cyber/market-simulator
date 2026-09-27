# PRECOMMIT — soco-81: must-run-floored coal priced at its own measured INCREMENTAL heat rate (two-sided)

Lane soco-81, 2026-09-27. Written and pushed **before any shard was launched**. The parent solves nothing (rule 32(a)).
Each year is solved in its own shard (rule 36); each shard pushes its full bundle (rule 34).

- **Authority:** owner ruling 2026-09-27 on `FINDING-soco-75-2026-09-27.md` §6 (`docs/calibration-log/soco.md`,
  "owner rulings 2026-09-27"): build the SOCO-scoped, per-plant, two-sided mode of the coal incremental-HR measurement.
- **Control:** keeper `2026-09-27-soco76-egrid-identity-hr` (bundle `results/calibration/soco76_span`). Its committed
  numbers are the control (rule 29(b) form 4). No control solve. The soco76 leg refs are gone from origin, so leg-level
  checks run against zero-LP `fleet_only` rebuilds instead (§7.2).
- **Expected:** 2020 C4 coal moves to a PASS; 2019 COAL_BIT stays FAIL. Determination stays NOT-YET.

## 0. G-DRIFT (rule 29(b)), keeper legs `5b8af962` → HEAD

`5b8af962` (the soco-76 PRECOMMIT, pre-rebase) is patch-identical to `549bf57b` on `main`. `git diff 549bf57b
origin/main` over the solve path, every hunk classified:

| hunk | class | reason |
|---|---|---|
| `campd_unit_fuel_split` + `campd_fuel_split_selector` plumbing (scenarios, campd_bins, coal, arrays, assembly, offer_curves, reserves/spec, resolved_inputs; MISO `-fuelsplit-` CSVs) | INERT | default off, absent from the SOCO recipe, and forced off under `campd_per_unit_attribution` (SOCO keeper: true) |
| coal take-floor soft shortfall price (`coal_fuel_inventory.coal_take_shortfall_price`, LP `n_take_slack` block, `run_calibration.run_year`) | INERT | only built when `coal_fuel_inventory_take_floor` is armed; SOCO recipe: absent (refused, soco-80) |
| `IMPORT_TRANCHES_BY_YEAR["CAISO"]` 2019–2021 rows | INERT | CAISO's table |
| `forecast_parity_registry` NYISO row | INERT | bookkeeping, not the solve path |
| **this lane:** `coal_econ_marginal_hr_two_sided` + artifact + `bins_to_fleet(year=)` | LIVE only when armed | default off; with it off the hook is skipped (census "off" builds reproduce the keeper recipe) |

**Form 4 is valid. The keeper is the control.**

## 1. The mechanism

- **Field:** `ScenarioConfig.coal_econ_marginal_hr_two_sided` (default `False`; cache key dropped at its declared default;
  TIER 1 structural gate). CLI `--coal-econ-marginal-hr-two-sided`.
- **Artifact:** `data/raw/_processed-legacy/coal_incremental_hr_ratio_SOCO.csv`, sha256
  `c07b531c1b0a27f2e6c8f4fd6bbc008f3873616e11a987ac9bf5d951303d886d`, from
  `scripts/data/derive_coal_incremental_hr_ratio.py` (`ISO_SCOPE = ("SOCO",)`, rule 25).
  - Incremental HR: `derive_campd_marginal_hr.derive_unit_bands` unchanged (p3/p97, normalized quadratic, econ_low
    x = 0.5, econ_high x = 0.9), over the same CEMS hours the average-HR artifact averages.
  - Ratio = generation-weighted plant incremental / `campd_coal_heat_rates_SOCO.csv` `heat_rate_gross`, same plant-year.
  - Pooled row = mean of the year ratios. It reproduces FINDING-soco-75 §3 exactly (Bowen 0.981/1.003, Miller
    0.924/0.993, Scherer 0.931/0.972, Daniel 0.893/0.910, Gaston 0.904/0.892).
- **Application** (`fleet/assembly.bins_to_fleet`):
  - **Scope:** a coal tranche set with a measured min-load floor (`_mustrun` + `_sync` > 0). This is a unit
    parameter, not a plant list (rule 18).
  - **What moves:** `_committed` and `_econlo` take `avg × ratio_econ_low`; `_econhi` takes `avg × ratio_econ_high`.
  - **What stays:** `_mustrun`/`_sync` (sunk fuel) and `_peak` (scarcity wall). Floorless cyclers keep the average
    (SOCO-63 §5).
  - **Rule 19:** the ratio REPLACES the band multiplier, so the class floor `coal_econ_marginal_hr_bound` never
    reaches these tranches. Not stacked.
- **Year rule (rule 13):** the solve year's ratio where the average-HR artifact has that plant-year, else pooled. A
  forecast year therefore reads pooled.
- **Free parameters: zero** (rule 21).
- **Scope vs FINDING-soco-75 §6.** `_committed` is included because, at a floored plant, it sits ABOVE the floor. This
  is the exact scope soco-75's greedy promise was computed on (`_soco75_incremental_hr.main_greedy --scope mustrun`).

## 2. Census (zero LP)

`scripts/probes/_soco81_census.py fleet`, record `docs/handoffs/r-soco/soco81_fleet_census.json`. `fleet_only` rebuild
on the soco76 recipe (the nine §5 `--set` fields included), flag off vs on, every year:

- **Exactly 11 tranches move in every year 2019–2025.** Bowen 703 and Gaston 26 move their `_committed` only (neither
  has an econ tranche). Miller 6002, Scherer 6257 and Daniel 6073 move `_committed` + `_econlo` + `_econhi`.
  About 5.4–6.0 GW in total.
- **Cyclers are untouched:** Barry 3, Crist 641, Wansley 6052, plus the 2025 retirees 8 and 708.
- **Nothing else moves.** Every unit's `pmax`, `min_gen` and `availability` is identical. Every moved tranche's HR
  equals average × the artifact ratio to 4 dp.
- **Two-sided in practice.** The same plant can move up and down in the same year. 2025 Miller `_econhi` +$0.72,
  `_econlo` −$1.20. Bowen `_committed` rises in 2020, 2024 and 2025. Daniel `_econhi` 2020 rises +$2.44.

Ratios, lo / hi (year rows):

| plant | tranches | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| Gaston 26 | committed | 0.927/0.911 | 0.934/0.931 | 1.030/1.005 | 0.800/0.799 | 0.909/0.941 | 0.883/0.888 | 0.842/0.767 |
| Bowen 703 | committed | 0.958/0.979 | 0.995/1.025 | 0.964/0.989 | 0.963/0.978 | 0.962/0.969 | 1.004/1.027 | 1.019/1.050 |
| Miller 6002 | committed+econlo+econhi | 0.896/0.983 | 0.899/0.958 | 0.918/0.949 | 0.934/0.969 | 0.929/1.006 | 0.943/1.052 | 0.949/1.031 |
| Daniel 6073 | committed+econlo+econhi | 0.870/0.885 | 0.943/1.077 | 0.938/0.966 | 0.890/0.865 | 0.856/0.860 | 0.842/0.804 | 0.913/0.916 |
| Scherer 6257 | committed+econlo+econhi | 0.963/1.043 | 0.901/0.917 | 0.958/1.005 | 0.938/0.981 | 0.930/0.961 | 0.910/0.963 | 0.920/0.933 |

## 3. Greedy (zero LP), baseline-differenced

`_soco81_census.py greedy`, record `docs/handoffs/r-soco/soco81_greedy.csv`.

- **Construction.** Each moved plant's tranche set is dispatched as a price-taker against its zone's committed P1
  price, at the keeper offer and at the arm offer. The hourly difference is added to the plant's committed payload MW,
  clipped to [0, nameplate], and taken from CC_REGULAR.
- **Scoring.** C1 by `calibration_verdict.score_fuelmix`; C4 by `_soco73_phase0.c4_coal`.
- **Limits.** Prices are held fixed; soco-72 measured the LP at ~3× its greedy, soco-76 at ~1×. The soco76 legs are
  gone, so the committed payload stands in for unit hourlies.

| year | row | keeper | greedy arm |
|---|---|---|---|
| 2019 | C1 COAL_BIT | −4.16 FAIL | −3.91 **FAIL** |
| 2019 | C1 COAL_PRB | +0.86 | +1.05 |
| 2019 | C4 coal NRMSE | 0.2500 | 0.2346 |
| **2020** | **C4 coal NRMSE** | **0.3012 FAIL** | **0.2833 PASS** |
| 2020 | C1 COAL_PRB / CC_REGULAR | −0.16 / +2.25 | +0.42 / +1.66 |
| 2021 | C4 coal NRMSE | 0.2078 | 0.2015 |
| 2022 | C1 COAL_PRB (thinnest) | +2.69 | +2.72 |
| 2022 | C4 coal NRMSE | 0.2401 | 0.2511 |
| 2023 | C4 coal NRMSE | 0.2674 | 0.2574 |
| 2024 | C4 coal NRMSE | 0.2543 | 0.2399 |

Plant deltas (TWh), 2020: Miller +0.87, Scherer +0.50, Bowen +0.00, Daniel 0, Gaston 0.

**Premise holds.** soco-75 promised 2020 C4 0.304 → 0.289 on the soco72 basis; on soco76 it is 0.301 → 0.283.

## 4. What is NOT tested here (DO-NOT-REDO)

- Cells already refused for SOCO stay refused: take-or-pay and `coal_fuel_inventory_take_floor` (G, soco-80),
  incremental HR as a floor (I), campaign floors, family vintage, and CT start (`tranche_startup_amortization`, owner
  NO 2026-09-27).
- The cyclers are out of scope by physics (SOCO-63 §5). Arming them was offered in soco-75 and refused.

## 5. Recipe and hard stops

Each shard runs ONE year `<Y>` ∈ {2019, …, 2025} at the pinned SHA `<SHA>` (the commit carrying this document):

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
uv venv .venv && uv pip install -r requirements.txt && uv pip install --no-deps -e .
.venv/bin/python scripts/hydrate_data.py --profile soco
PYTHONPATH=. .venv/bin/python scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. .venv/bin/python scripts/data/curate_demand_profile.py
PYTHONPATH=. .venv/bin/python scripts/run_calibration_full.py --restore-shared-inputs results/calibration/soco76_span
.venv/bin/python scripts/replay_keeper.py results/calibration/soco76_span --years <Y> \
  --out-dir results/calibration/soco81_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --set egrid_identity_heat_rates=true --set coal_econ_marginal_hr_two_sided=true \
  --note "soco-81 <Y>: soco-76 keeper recipe + coal_econ_marginal_hr_two_sided (SOCO must-run-floored coal at measured incremental HR)"
```

**Hard stops.** A shard that sees otherwise stops and does not push.

- `git rev-parse HEAD` equals the pinned SHA.
- `run_config.json` `environment.packages` equals {highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3,
  pyarrow 24.0.0, pydantic 2.13.4}.
- `sha256sum data/raw/_processed-legacy/coal_incremental_hr_ratio_SOCO.csv` = `c07b531c…303d886d`.
- `sha256sum data/raw/_processed-legacy/egrid_identity_heat_rates_SOCO.csv` = `32c46c93…8390985f`.
- The solve log carries `SOCO coal incremental HR (two-sided, year <Y>): committed/econ tranches repriced at 5
  must-run-floored plant(s) [26, 703, 6002, 6073, 6257]`.
- The solve log carries `container preflight:` and `memory peak:`.
- `scenario_config` shows all ten `--set` fields true, plus `gas_basis_differential_measured_by_year` true.
- Every `offer_curve_by_group` band is 1.0.
- `meta.json` carries `coal_econ_marginal_hr_two_sided: true`.
- `gas_prices[<Y>]` equals the keeper's (2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52).
- `dispatch/<Y>_P1.parquet` is present.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1 (the 11 tranches).** In every leg, the moved `_econlo`/`_econhi` tranches solve at the census arm median `mc` ±$0.01.
  `_committed` does too, unless P1 adds a start markup (reported, not a stop).
- **E2 (direction).** Coal rises in 2020 (Miller, Scherer) and in 2019, 2021, 2023 and 2024. CC_REGULAR falls.
  Nuclear, hydro and solar |Δ| ≤ 0.1 TWh.
- **E3 (the failing rows).**
  - 2020 C4 coal: 0.26–0.29 across 1–3× the greedy. **Expected to PASS.**
  - 2019 COAL_BIT: −3.9 to −3.4 pp. **Still FAIL.**
- **E4 (side effects).**
  - 2022 COAL_PRB +2.72 to ~+2.8 (thin, below +3).
  - 2022 C4 coal 0.251–0.27 (still PASS).
  - 2019 COAL_PRB +1.0 to +1.5.
- **E5.** Unserved energy is 0 MWh in every year.
- **E6.** C6 and C8 PASS. D-2 and D-4 are unchanged in kind (no floor is added).
- **Expected determination: NOT-YET** (2019 COAL_BIT).

## 7. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff all four hold**:

1. All seven legs solve cleanly, with the §5 hard stops met.
2. **The mechanism fires exactly as censused.** In every leg:
   - the 11 tranches' median `mc` equals the zero-LP flag-on `fleet_only` build ±$0.01 (a `_committed` tranche may
     differ only by a P1 start markup, reported);
   - every other non-`_committed` unit's median `mc` equals the flag-off build ±$0.01.
   This is checked by `scripts/probes/soco81_compose_span.py`.
3. No year's unserved energy increases.
4. C6 and C8 PASS, and `legitimacy_diagnostics` records no new D-4 FAIL.

- **This holds whatever C1 and C4 do.** An average heat rate that carries sunk no-load fuel is an input error, not a
  price choice (rules 1 and 14). If a row moves the wrong way, that is reported at full magnitude as the next lead.
- **Promotion itself** is covered by the owner's standing ruling ("If structural integrity improves but gates regress
  that may still be a keeper").
- **If it lands (rule 35):**
  1. enumerate the SOCO year union (2019–2025) from every sidecar;
  2. run `audit_keepers` E1;
  3. `prune_iso_runs --iso SOCO --force-uncite` removes `2026-09-27-soco76-egrid-identity-hr`.

## 8. Retrievability (rule 34(e))

- Each shard pushes its full bundle, `dispatch/<Y>_P1.parquet` included, to `claude/soco81-<Y>` through a
  `.gitignore` negation and a plain `git add`.
- The parent fetches each leg, verifies it, and composes `soco81_span`. The composite (slim set + `hourly/`), sidecar
  and payload land on `main` with this lane's PR.
- A leg not landed on `main` is costed as a re-solve: ~2 min of LP per year.
