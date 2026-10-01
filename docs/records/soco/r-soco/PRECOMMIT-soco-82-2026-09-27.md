# PRECOMMIT — soco-82: regenerate `campd-unit-outages-perunitdark-SOCO.csv` (F1 retiree append; Wansley's dark windows)

Lane soco-82, 2026-09-27. Written and pushed **before any shard was launched**. The parent solves nothing (rule 32(a)).
Each year is solved in its own shard (rule 36); each shard pushes its full bundle (rule 34).

- **Control:** keeper `2026-09-27-soco81-coal-incremental-hr` (bundle `results/calibration/soco81_span`, legs at
  `e688d3f2`). Its committed numbers are the control (rule 29(b) form 4). No control solve.
- **What changes:** one committed input artifact, re-derived by its own frozen deriver with its own recorded invocation.
  No code, no `ScenarioConfig` field, no free parameter.
- **Expected:** 2021 C4 coal improves; 2019 COAL_BIT stays FAIL (−3.99 → about −4.0 pp). Determination stays NOT-YET.

## 0. G-DRIFT (rule 29(b)), keeper legs `e688d3f2` → HEAD

`git diff e688d3f2 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference`: 15 files. Every hunk is INERT for SOCO.

| change | where | why inert for SOCO |
|---|---|---|
| SPP-93 `spp_zone_partition` (topology_variant, iso_configs, eia860 `_assign_zones`, zonal_shares, renewables, zone_assignment, runner, both CLIs, `spp_plant_reserve_zone.csv`) | SPP | every seam sets/reads `north_south` when `iso != "SPP"`; the West/East branches are guarded by `iso == "SPP"` |
| R-CAISO-8 `caiso_intertie_partial_year_measured` + `ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO["CAISO"]` 1.166 → 1.154 | CAISO | default off; a CAISO-keyed dict entry |
| NYISO-NEXT-8 import-ladder re-derive (`interchange/spec.py`) | NYISO | NYISO-keyed tables |
| `scenarios.py` +57 | all | two new default-off / `north_south` fields, both absent from the SOCO recipe |
| soco-81 `coal_econ_marginal_hr_two_sided` (`7b069a14`) | SOCO | the rebased copy of the code the keeper legs ran at `e688d3f2`; no hunk in the diff |

Instrument: the §2 `fleet_only` rebuilds at HEAD with the committed artifact reproduce the keeper's recipe (flag set
identical to `soco81_span/run_config.json`).

## 1. The artifact and why it drifted (rule 23: the data change, cited)

`data/raw/campd-unit-outages-perunitdark-SOCO.csv` (the keeper's `campd_dark_unit_year_windows` +
`campd_per_unit_attribution` input) was derived by F2 `5ff0cb9cb` (2026-09-24 15:53 UTC). **F1 `31e54d8a5`
(16:31 UTC, 37 minutes later)** appended the NWPP/SOCO BAs to
`data/raw/eia-860/eia860_generator_retired_within_window.parquet` ("Retiree parquet gains the NWPP/SOCO BAs it
predated"). The deriver loads that parquet into its plant universe (`load_retired_within_window`), so a re-derive
after F1 sees three SOCO coal plants F2 could not:

| plant | added windows | years | in any SOCO LP fleet? |
|---|---|---|---|
| Wansley 6052 (units 1, 2) | 37 | 2019–2022 | **yes, 2019–2021** (not 2022: retired Aug 2022, absent from vintage 2022) |
| Gorgas 8 (units 8, 9, 10) | 4 | 2019 | no |
| Hammond 708 (unit 4) | 3 | 2019 | no |

**Attribution is byte-exact.** HEAD's deriver with the pre-F1 retiree parquet (`git show
31e54d8a5^:data/raw/eia-860/eia860_generator_retired_within_window.parquet`) swapped in reproduces the committed CSV
byte-for-byte; with the current parquet it adds exactly these 44 rows and drops none
(`scripts/probes/_soco82_dark_drift.py drift`). Every added row is `capacity_source = observed_peak`.

The re-derive uses the committed sidecar's own `derive_invocation` (`--iso SOCO --years 2019..2025
--per-unit-crosswalk --dark-unit-years`); the new sidecar differs only in `artifact_rows` (2451 → 2495) and
`windows_by_start_year` (2019–2022). New sha256 `03ce606c…a2fd37c` (was `ae0912a9…85cfa2f1`).

**Why this is a repair, not a lever.** The same coal detector already writes windows for every other SOCO coal unit
in the keeper (mechanism K). Wansley was missing only because its units were not in the retiree parquet at derive time
(a data-completeness defect F1 fixed). Rule 14: the accurate input stands whatever it does to the fit.

## 2. Census (zero LP; `docs/records/soco/r-soco/soco82_fleet_census.json`)

Seven `fleet_only` rebuilds per artifact on the keeper recipe (§5 flag set), committed vs regenerated:

| year | units whose arrays move | what moves | Wansley availability mean |
|---|---|---|---|
| 2019 | 4 (`COAL_SOCO_GA_p6052_{committed,econlo,econhi,peak}`) | availability only | 0.914 → **0.233** |
| 2020 | same 4 | availability only | 0.914 → **0.020** |
| 2021 | same 4 | availability only | 0.914 → **0.118** |
| 2022–2025 | **none** | — | — |

`mc`, `pmax`, `min_gen`, heat rate and VOM are identical for every unit in every year.

## 3. Greedy (zero LP): the keeper's committed Wansley MW clipped to the new availability

| year | keeper Wansley TWh | clipped | C1 COAL_BIT (lost → CC bound) | C4 coal NRMSE (lost bound) |
|---|---|---|---|---|
| 2019 | 0.333 | 0.150 | −3.99 → −4.05 FAIL | 0.219 → 0.218 |
| 2020 | 0.003 | 0.003 | −2.37 → −2.37 | 0.285 → 0.286 |
| 2021 | 5.577 | **4.189** | +0.32 → −1.42 | **0.204 → 0.148** |

EIA-923 has Wansley at 1.8 TWh (2019) and 1.1 TWh (2021); CEMS 2020 is 0.15 TWh. The other bound (clipped energy
refilled 1:1 by other coal) leaves every C1 row unchanged. The LP lands between the two.

## 4. What is NOT tested here (DO-NOT-REDO, and this lane's zero-LP refusals)

- Take-or-pay and `coal_fuel_inventory_take_floor` (G), incremental HR as a floor (I), incremental HR on cyclers
  (SOCO-63 §5), campaign floors, family vintage, CT start (owner NO).
- **Replacement (spot) fuel cost for coal: refused on the data.** Southern's Schedule VI dispatch formula prices fuel
  at marginal replacement cost. EIA-923 Page 5 receipts give Barry's 2019 spot coal at $3.48/MMBtu against $3.03
  contract (spot is *dearer*), and Wansley's 2019 receipts are all spot at $3.08, which is what the model already
  uses. The sign is wrong for the 2019 row.
- The 2019 cycler gap itself: see the FINDING (`FINDING-soco-82-2026-09-27.md`). Southern's own FERC-714 system lambda
  sits below Barry's and Wansley's variable cost in 97 % / 93 % of their synced 2019 hours, which makes this an
  out-of-merit conduct question for the owner, not a lever.

## 5. Recipe and hard stops

Each shard runs ONE year `<Y>` ∈ {2019, …, 2025} at the pinned SHA `<SHA>` (the commit carrying this document):

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
uv venv .venv && uv pip install -r requirements.txt && uv pip install --no-deps -e .
.venv/bin/python scripts/hydrate_data.py --profile soco
PYTHONPATH=. .venv/bin/python scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. .venv/bin/python scripts/data/curate_demand_profile.py
PYTHONPATH=. .venv/bin/python scripts/run_calibration_full.py --restore-shared-inputs results/calibration/soco81_span
.venv/bin/python scripts/replay_keeper.py results/calibration/soco81_span --years <Y> \
  --out-dir results/calibration/soco82_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --set egrid_identity_heat_rates=true --set coal_econ_marginal_hr_two_sided=true \
  --note "soco-82 <Y>: soco-81 keeper recipe on the regenerated perunitdark-SOCO outage extract (F1 retiree append)"
```

**Hard stops.** A shard that sees otherwise stops and does not push.

- `git rev-parse HEAD` equals the pinned SHA.
- `sha256sum data/raw/campd-unit-outages-perunitdark-SOCO.csv` = `03ce606cfe118ef28e560739d12a005b2240aa112609e119c51a9f86ea2fd37c`.
- `sha256sum data/raw/_processed-legacy/coal_incremental_hr_ratio_SOCO.csv` = `c07b531c…303d886d`;
  `egrid_identity_heat_rates_SOCO.csv` = `32c46c93…8390985f`.
- `run_config.json` `environment.packages` equals {highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3,
  pyarrow 24.0.0, pydantic 2.13.4}.
- The solve log carries `container preflight:` and `memory peak:`.
- `scenario_config` shows all ten `--set` fields true, plus `gas_basis_differential_measured_by_year` true.
- Every `offer_curve_by_group` band is 1.0.
- `gas_prices[<Y>]` equals the keeper's (2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52).
- `dispatch/<Y>_P1.parquet` is present.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1.** 2022–2025: every class |Δ TWh| ≤ 0.01 against the keeper (inputs array-identical, §2).
- **E2.** 2021: Wansley falls from 5.58 TWh to ≤ 1.9 TWh (its new availability bound); coal falls by 0–4.2 TWh and
  CC_REGULAR rises. C4 coal NRMSE 0.148–0.204 (PASS). C1 COAL_BIT between −1.42 and +0.32 pp (PASS).
- **E3.** 2019: COAL_BIT −4.05 to −3.99 pp, **still FAIL**. 2020: every row within ±0.02 pp.
- **E4.** Unserved energy 0 in every year. C6 and C8 PASS; D-2 / D-4 unchanged in kind (no floor touched).
- **Expected determination: NOT-YET** (2019 COAL_BIT).

## 7. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff all four hold**:

1. All seven legs solve cleanly, with the §5 hard stops met.
2. **The input fires exactly as censused:** in 2019–2021 Wansley's four tranches never dispatch above the regenerated
   availability × pmax; in 2022–2025 every class TWh equals the keeper's ±0.01 TWh.
3. No year's unserved energy increases.
4. C6 and C8 PASS, and `legitimacy_diagnostics` records no new D-4 FAIL.

- **This holds whatever C1 and C4 do.** A unit modelled 91 % available through months its CEMS shows it dark is an
  input error (rule 14).
- **Promotion itself** is covered by the owner's standing ruling ("If structural integrity improves but gates regress
  that may still be a keeper").
- **If it lands (rule 35):** enumerate the SOCO year union (2019–2025) from every sidecar; run `audit_keepers` E1;
  `prune_iso_runs --iso SOCO --force-uncite` removes `2026-09-27-soco81-coal-incremental-hr`.
- **If it does not land**, the regenerated artifact is NOT committed to `main` (the keeper must keep reading the file it
  was solved on) and the drift is recorded in the FINDING.

## 8. Retrievability (rule 34(e))

- Each shard pushes its full bundle, `dispatch/<Y>_P1.parquet` included, to `claude/soco82-<Y>` through a
  `.gitignore` negation and a plain `git add`.
- The parent fetches each leg, verifies it, and composes `soco82_span`. The composite (slim set + `hourly/`), sidecar
  and payload land on `main` with this lane's PR.
- A leg not landed on `main` is costed as a re-solve: ~2 min of LP per year.
