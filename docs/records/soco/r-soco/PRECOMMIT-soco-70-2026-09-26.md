# PRECOMMIT — soco-70: measured COAL rows for SOCO's five uncovered coal plants, 2019–2025

Lane soco-70, 2026-09-26. This document was written and pushed **before any shard was launched**. The parent
solves nothing (rule 32(a)). Each year is solved in its own shard (rule 36), and each shard pushes its full bundle
(rule 34).

The keeper it is measured against is `2026-09-26-soco69-coal-mustrun-measured` (bundle
`results/calibration/soco69_span`, legs solved at `ccaa94e03612c640b5f90514bf7efa5c1574b627`). That keeper's own
committed numbers are the control (rule 29(b) form 4). No control solve is spent.

## 1. Lever

**What changes.** Five COAL rows are added to `data/raw/_processed-legacy/thermal_tranches_SOCO.csv`, one each for
Barry (3), Gaston (26), Crist (641), Wansley (6052) and Daniel (6073). The rows are written by
`scripts/data/derive_thermal_tranches.py --iso SOCO --years 2019 … 2025 --coal-unit-coverage`. The 60 existing rows
are **byte-identical**, because the new rows are appended to the file's existing bytes. The sidecar records the
original `--years 2024` derive as `base_derive_invocation`.

- Artifact sha256: `7b7f5f27…df84` → **`ab5ec265d192379551c14facc6f65d8d972f117a565bae36b0179bbf96122ad7`**.
- There is no `ScenarioConfig` change. The recipe is the keeper's eight `--set` fields, unchanged.

**The rows.**

| plant | nameplate MW | online h (pooled) | committed % | must-run % | online_frac |
|---|---|---|---|---|---|
| Barry 3 | 1118.5 | 36,535 | 40.1 | 0.0 | 0.600 |
| Gaston 26 | 832.0 | 28,842 | 52.6 | **48.0** | 0.485 |
| Crist 641 | 924.0 | 12,253 | 15.5 | 0.0 | 0.728 |
| Wansley 6052 | 1744.0 | 6,414 | 20.1 | 0.0 | 0.245 |
| Daniel 6073 | 1004.0 | 45,939 | 34.9 | **34.9** | 0.763 |

**Why these plants had no row.** The incumbent derive (`--years 2024`, facility attribution) writes a row only for
a plant's **primary** (largest-nameplate) group:

- **Barry, Gaston and Daniel.** Their facility-summed CEMS net, coal included, went to the CC or gas-steam row. For
  example, Barry's CC row carries a 150 % `median_cf`.
- **Crist and Wansley.** Their coal units stopped before 2024.

soco-69 withdrew the unmeasured 45 % default slab from these five plants (rule 17). Since then they have dispatched
on econ bands only: 2.16 TWh in 2019, against 13.50 TWh of EIA-923 (census, §2).

**The construction** is `coal_unit_coverage_rows`, and it is the incumbent's COAL branch, unit-scoped:

- **Series.** The net MW of the plant's **coal-fired** CAMPD units only. "Coal-fired" means CAMPD's own
  `primaryFuelInfo` names coal in that unit-year. Gas units at the same facility never enter.
- **Denominator.** That year's EIA-860 vintage coal nameplate, which is what the solve-year fleet carries. It is
  multiplied by the unit-outage derate on the keeper's own extract basis (`-perunitdark-`).
- **Constants.** P5 / P25 / P50, the 5 % online mask, the 1 % sync threshold and the 0.70 / 0.60 / 1.0 caps are
  all **the same constants** the incumbent uses, pooled over the span.

**Rule check:**

| rule | how this lever meets it |
|---|---|
| 14 / 13 | A measured per-plant input replaces an absent measurement. It regenerates for any year CAMPD reports. |
| 17 | The new must-run floors have a driver: the plant's own CEMS must-run conduct. They have a window: `online_frac`, clipped by the keeper's CEMS-derived availability windows, which already carry Gaston's and Daniel's idle stretches as zero availability. They have a forward story: the same derive over the forward year's CEMS. |
| 19 | One mechanism, the existing tranche consumer. No new floor type. `coal_mustrun_requires_measured_row` stays armed and now finds a measured row. |
| 21 / 24 | Zero free parameters. No new field. |
| 23 | **The source-data change is cited, not the residual.** SOCO's backcast span now reaches 2019–2025, and these plants' CEMS coal years sit inside it; the incumbent's 2024-only window predates that span. Existing rows are not re-derived. |
| 25 | SOCO's own CAMPD and EIA-860. |

**Not a re-test of any `R` / `I` / `G` cell:**

- The `thermal_tranche_artifact_coverage` cell is `U`. `coal_mustrun_requires_measured_row` is `K`, and it is
  kept. `campd_per_unit_attribution` is `K`.
- The per-unit tranche companion (`thermal_tranches-perunit-SOCO.csv`) was **deliberately not derived**. The
  SOCO-56 matrix note says it would arm silently under that `K` flag. Its gas-only crosswalk routes coal boilers to
  ST_GAS, and it re-derives every gas row too.
- `tranche_startup_amortization` stays **`G`**, and the SOCO-64/65 owner question is re-raised in the RESULT.
- The `offer_curve_by_group` bands are not a lever, because SOCO has no price reference.

## 2. Task 1 census (zero LP; `scripts/probes/_soco70_phase0.py`)

**CEMS coal-unit conduct against the keeper leg** (TWh; `sync_h` counts hours with gross above 1 % of nameplate):

| year | plant | EIA-923 bench | CEMS gross | keeper model | sync h | load when synced | model on h |
|---|---|---|---|---|---|---|---|
| 2019 | Barry 3 | 4.18 | 4.63 | 0.25 | 8,307 | 0.51 | 497 |
| 2019 | Gaston 26 | 2.79 | 3.35 | 0.04 | 4,739 | 0.88 | 75 |
| 2019 | Crist 641 | 2.67 | 3.08 | 1.58 | 7,618 | 0.45 | 2,410 |
| 2019 | Wansley 6052 | 1.82 | 2.28 | 0.13 | 3,774 | 0.36 | 124 |
| 2019 | Daniel 6073 | 2.05 | 2.36 | 0.16 | 6,183 | 0.39 | 302 |
| 2020 | the five | 8.72 | 10.28 | 0.81 | — | — | — |
| 2023 | 3 / 26 / 6073 | 1.71 / 1.75 / 1.50 | 1.98 / 2.04 / 1.72 | 0.00 / 0.00 / 0.00 | 3,950 / 3,055 / 5,383 | 0.46 / 0.83 / 0.33 | 0 / 0 / 2 |
| 2024 | 3 / 26 / 6073 | 0.70 / 1.83 / 1.47 | 0.84 / 2.04 / 1.66 | 0.89 / 0.00 / 0.00 | 1,789 / 3,008 / 6,237 | 0.43 / 0.84 / 0.30 | 2,147 / 0 / 4 |

The full seven-year table is the probe's `census` output.

- **The model also over-runs in places.** In the gas-price years it runs Wansley at 6.10 vs 1.12 TWh (2021),
  Barry at 5.39 vs 3.31 (2022) and Barry at 3.75 vs 0.68 (2025).
- **Gaston and Daniel run as baseload whenever the keeper's availability lets them.** Their idle stretches are
  zero-availability windows in the keeper's own outage extract: Gaston has 3,336–5,928 h/yr, Daniel 408–3,384.

**Fleet census** (`fleet` mode). Two `fleet_only` rebuilds per year on the keeper recipe compare the incumbent
artifact with the extended one:

- **Every unit outside the five plants is byte-identical in all seven years** on `pmax`, `mc_base`, `min_gen` and
  `availability`.
- **Gaston.** Its econ bands vanish. It gains a `_mustrun` tranche of 399.36 MW at $4.50, and its `_committed`
  band grows from 41.6 to 416.0 MW, which prices at its econ `mc` under `coal_warm_committed`.
- **Daniel.** It gains a `_mustrun` tranche of 350.40 MW. Its `_committed` band grows from 50.2 to 350.4 MW, and
  its econ bands fall from 934 to 283 MW.
- **Barry, Crist and Wansley.** They carry `mustrun_pct = 0`, so no floor. Their `_committed` band grows to 448.5,
  143.2 and 350.5 MW, and that band **keeps the P1 start markup**, because the warm exemption needs a must-run
  tranche. Their econ bands shrink by the same amount.
- **Which plants are present by year.** Crist appears in 2019–2020, Wansley in 2019–2021 and 2025 (dark), and the
  other three in every year.

**Price-taker greedy** (`greedy` mode). Each affected tranche is dispatched against the keeper leg's price, with
the start markup measured on the keeper's committed tranche. Other thermal units are displaced
most-expensive-first, or refilled cheapest-first. C4 is re-scored with `render_calibration_html`'s construction
against the keeper's restored EIA-930 coal series, and it **reproduces the keeper's 0.347 / 0.316 / 0.292
exactly**.

| year | Gaston Δ | Daniel Δ | Barry Δ | COAL_BIT Δ | COAL_PRB Δ | ST_GAS Δ | CT_PEAKER Δ | C4 coal NRMSE, keeper → greedy |
|---|---|---|---|---|---|---|---|---|
| 2019 | +1.67 | +1.58 | −0.06 | +1.62 | +0.99 | −0.85 | −0.85 | 0.187 → 0.150 |
| 2020 | +1.48 | +1.68 | −0.02 | +1.47 | +1.30 | −0.83 | −1.01 | **0.347 → 0.281** |
| 2021 | +1.76 | +0.54 | −0.40 | +1.58 | +0.11 | −0.16 | +0.31 | 0.214 → 0.207 |
| 2022 | +0.87 | +0.10 | −0.17 | +0.66 | +0.10 | −0.35 | 0.00 | 0.228 → 0.239 |
| 2023 | +1.06 | +0.92 | 0.00 | +1.06 | +0.80 | −0.75 | −0.70 | **0.316 → 0.254** |
| 2024 | +1.06 | +0.94 | −0.25 | +0.82 | +0.76 | −0.54 | −0.44 | 0.292 → 0.254 |
| 2025 | +1.11 | +0.47 | −0.07 | +1.00 | +0.40 | −0.40 | −0.36 | 0.183 → 0.184 |

## 3. Recipe

Each shard runs one year, `<Y>` ∈ {2019, …, 2025}, pinned to the SHA that carries this document. The shard pins
it itself as step 0:

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
python3 scripts/hydrate_data.py --profile soco
PYTHONPATH=. python3 scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. python3 scripts/data/curate_demand_profile.py
python3 scripts/replay_keeper.py results/calibration/soco69_span --years <Y> \
  --out-dir results/calibration/soco70_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --note "soco-70 <Y>: soco-69 keeper recipe on thermal_tranches_SOCO.csv + measured COAL rows for plants 3/26/641/6052/6073 (coal-unit coverage, rule 23 source change)"
```

**Hard stops. A shard that sees otherwise stops and does not push.**

- `git rev-parse HEAD` equals the pinned SHA.
- `sha256sum data/raw/_processed-legacy/thermal_tranches_SOCO.csv` equals `ab5ec265…22ad7`, and so does
  `run_config.json` `resolved_inputs.thermal_tranches.sha256`.
- `scenario_config` shows all eight `--set` fields true.
- Every band is 1.0.
- `dispatch/<Y>_P1.parquet` is present.
- `gas_prices[<Y>]` equals the keeper's value (2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52).
- The solve log contains `container preflight:` and `memory peak:`.
- In `hourly/unit_hourly_<Y>.parquet`, the COAL `_mustrun` units sit exactly at {703, 6002, 6257, 26, 6073}
  intersected with the leg's coal plants.

## 4. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

These are measured against the keeper's committed numbers and anchored on the §2 greedy. The C1 pp values are the
keeper's reported share pp plus the greedy Δ over the model total.

- **E1 (direction).**
  - Gaston and Daniel coal energy rise in every year: Gaston between ×0.5 and ×1.3 of the greedy, Daniel between
    ×0.3 and ×1.5. It is wider because Daniel's committed band is at econ price in a CC-heavy plant.
  - Barry, Crist and Wansley each move by |Δ| ≤ 0.6 TWh. Their capacity is re-split, not floored.
  - COAL_BIT and COAL_PRB rise in every year. ST_GAS and CT_PEAKER fall or stay equal in most years.
  - Nuclear, hydro, wind and solar: |Δ| ≤ 0.1 TWh.
  - The `_mustrun` output at Bowen, Miller and Scherer is within 0.3 TWh of the keeper's. Their offer is unchanged;
    only the LP's residual moves.
- **E2 (the failing rows).**
  - **2019 COAL_BIT:** −3.83 → ≈ **−3.2 pp**. **It is expected to STILL FAIL** against its 3 pp band. A PASS
    needs the LP to refill ~0.6 TWh more coal than the greedy does, and that is declared unlikely.
  - **2020 C4 coal NRMSE:** 0.347 → ≈ 0.28, expected **PASS**.
  - **2023 C4 coal NRMSE:** 0.316 → ≈ 0.25, expected **PASS**.
  - **2024 C4 coal NRMSE:** 0.292 → ≈ 0.25, expected to stay PASS.
- **E3 (side-effect risks, declared now).**
  - **ST_GAS** falls. 2019 goes −2.49 → ≈ −2.81 pp and 2021 goes −2.76 → ≈ −2.82 pp. Both are thin PASS, and a
    flip to FAIL is possible.
  - **2020 COAL_BIT** goes −2.87 → ≈ −2.3 pp, PASS.
  - **2023 CT_PEAKER** goes +2.79 → ≈ +2.5 pp, PASS.
  - **2019 CC_REGULAR** goes +2.61 → ≈ +2.5 pp, PASS.
  - **2022 C4 coal** goes 0.228 → ≈ 0.24, PASS.
  - **The expected determination is NOT-YET**, carried by 2019 COAL_BIT alone: one failing C1 row instead of three
    failing rows.
- **E4 (unserved).** Unserved stays 0 MWh in every year. No capacity leaves the fleet.
- **E5 (other criteria).**
  - C2, C6 and C8 PASS.
  - C3a/b/c stay UNSCORABLE.
  - The new floors are reported through D-2 / D-4.
  - `gen_soco60b` B1/B2 are unchanged, because they are benchmark-side.

## 5. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff** all four of these hold:

1. All seven legs solve cleanly with the §3 hard stops met.
2. The mechanism fires exactly as censused. In every leg the coal `_mustrun` plant set equals §3's set, and every
   unit outside the five plants carries hourly `cap_mw` byte-identical to the keeper's leg.
3. No year's unserved energy increases against the keeper.
4. `legitimacy_diagnostics` records **no D-4 off-window-binding FAIL** for a coal must-run floor at Gaston or Daniel.
   Rule 17 is the reason: a new floor that binds while the plant's own record says offline would be the defect
   soco-69 removed, reintroduced.

This holds **whatever C1–C8 do**. The rows are a measured input where there was none (rules 14 / 23). Gate moves are
reported at full magnitude, including a 2019 COAL_BIT that still fails and any ST_GAS row that flips. The owner
decides (rule 31), and the owner's standing ruling is "if structural integrity improves but gates regress that may
still be a keeper". If the owner promotes, rule 35 prunes `2026-09-26-soco69-coal-mustrun-measured`, after the year
union {2019, …, 2025} is enumerated from every SOCO sidecar.

## 6. Retrievability (rule 34(e))

- **Legs.** Each shard pushes `results/calibration/soco70_<Y>/` (full bundle, including `dispatch/`) to
  `claude/soco70-<Y>` through a `.gitignore` negation and a plain `git add`.
- **Composite.** The parent composes `soco70_span` (`scripts/probes/soco70_compose_span.py`) and lands it on
  `main` via the lane PR. The per-year dirs are gitignored in the parent.
- **Cost.** Any leg not landed is costed as a re-solve, ~2–3 min of LP per year.

## 7. G-DRIFT (rule 29(b)), recorded before any shard ran

`scripts/probes/_soco70_gdrift_identity.py` ran against keeper SHA `ccaa94e0`, in two passes:

- **At `7df4a1f3`:** ALL LP INPUTS BIT-IDENTICAL, seven years.
- **At the rebased head `56272c15` + this lane's commit:** ALL LP INPUTS BIT-IDENTICAL, seven years.

In that second pass both arms read the extended artifact through the shared data tree, so the check measures
**code** drift only.

- **Constants.** Three changed by value, all settled by instrument 3: `CAMPD_BINNING_ISOS`,
  `EIA930_PS_FOLDED_INTO_WAT` and `RGGI_MEMBER_STATES_BY_YEAR`.
- **Data drift on `main` since `ccaa94e0`.** Every change is **INERT for SOCO**:
  - CAISO files: `campd_cc_heat_rates_CAISO.csv` and the WECC intertie gap-fill parquet.
  - PJM files: two `memberrepair` outage extracts.
  - Three default-off `hourgrain` outage extracts. The keeper does not arm `unit_outage_window_hour_grain`.
  - A new `eia-923-generation-fuel/` corpus. HEAD code that reads it produced bit-identical arrays in instrument 3.

**All hunks are INERT, so form 4 stands and the committed `soco69_span` is the control.** The one solve-path
change is this lane's lever, the five appended rows.
