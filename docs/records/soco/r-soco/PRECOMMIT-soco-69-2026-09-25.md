# PRECOMMIT — soco-69: `coal_mustrun_requires_measured_row` on the SOCO keeper recipe, 2019–2025

Lane soco-69, 2026-09-25. This document was written and pushed **before any shard was launched**. The parent
solves nothing (rule 32(a)). Each year is solved in its own shard (rule 36), and each shard pushes its full bundle
(rule 34). The evidence is in `FINDING-soco-69-2026-09-25.md`.

## 1. Lever

**The field.** `coal_mustrun_requires_measured_row` is an **existing** registered `ScenarioConfig` field
(pjm-h14; PJM `K`, NEISO `K`). It is default off, carries its cache-key drop at `"False"`, and already has a matrix
row. SOCO's cell is `U`. No code changes.

**The construction.** The seam is `campd_bins.py::fleet_to_bins`. A COAL plant with no `(plant, COAL)` row in
`thermal_tranches_SOCO.csv` gets `pct_mr = 0`. It carries no `_mustrun` tranche, and that capacity joins its own
econ bands at its own `mc`.

**Why this lever** (FINDING §1–§2):

- The ST_GAS deficit is merit order: availability is 0.08–0.36 TWh a year.
- In 2019–2022 the displacing class is coal (+4.4 … +9.5 TWh).
- That coal excess sits on an **unmeasured 45 %, $4.50/MWh must-run slab** at five plants. The slab binds in
  3.99 / 7.34 / 4.72 / 0.23 / 0.67 / 1.09 / 0.93 TWh of hours when the plant's own CEMS coal units are offline.

**Rule check:**

| rule | how this lever meets it |
|---|---|
| 17 | This is the defect by definition. |
| 21 / 24 | Zero free parameters: a withdrawal, not a level. |
| 19 | One mechanism is removed. The measured Bowen, Miller and Scherer rows are untouched. |
| 25 | SOCO's own census. |

**Not a re-test of any `R`/`I`/`G` cell.**

- `tranche_startup_amortization` stays `G`, and the owner question is re-raised.
- The `offer_curve_by_group` bands are not a lever, because SOCO has no price reference.

## 2. Census (zero LP; FINDING §0, §3)

- **G-DRIFT against `34f3d4aa`: all INERT.** Every LP input, labels included, is bit-identical in all seven
  years. The committed `soco68_span` bundle is the control.
- **The arm removes only these unmeasured coal `_mustrun` tranches.** Their capacity moves to the same plants'
  `econlo` / `econhi` at unchanged `mc`. Class availability and class `min_gen` are byte-identical.

  | year | plants whose `_mustrun` tranche is removed | count |
  |---|---|---|
  | 2019–2020 | {3, 26, 641, 6052, 6073} | 5 |
  | 2021 | {3, 26, 6052, 6073} | 4 |
  | 2022–2024 | {3, 26, 6073} | 3 |
  | 2025 | {3, 26, 6073, 8, 708, 6052} | 6 (8, 708 and 6052 are dark) |

## 3. Recipe

Each shard runs one year, `<Y>` ∈ {2019, …, 2025}, pinned to the SHA that carries this document. The shard pins
it itself as step 0:

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
python3 scripts/hydrate_data.py --profile soco
PYTHONPATH=. python3 scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. python3 scripts/data/curate_demand_profile.py
python3 scripts/replay_keeper.py results/calibration/soco68_span --years <Y> \
  --out-dir results/calibration/soco69_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --note "soco-69 <Y>: soco-68 keeper recipe + coal_mustrun_requires_measured_row (no must-run tranche on coal plants absent from thermal_tranches_SOCO.csv; rule 17)"
```

**Hard stops. A shard that sees otherwise stops and does not push.**

- `git rev-parse HEAD` equals the pinned SHA.
- `run_config.json` `scenario_config` shows all eight `--set` fields true.
- Every band is 1.0.
- `dispatch/<Y>_P1.parquet` is present.
- `gas_prices[<Y>]` equals the keeper's value (2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52).
- The solve log contains `container preflight:` and `memory peak:`.
- `hourly/unit_hourly_<Y>.parquet` contains **no** COAL `_mustrun` unit at a plant outside {703, 6002, 6257}.

## 4. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

These are measured against the keeper's committed legs (`soco68_<Y>` / `soco68_span`) and anchored on the FINDING
§3 greedy.

- **E1 (direction, every year).** COAL_BIT falls, and ST_GAS rises or stays equal.
  - **COAL_BIT**, expected between ×0.4 and ×1.3 of the greedy:

    | year | greedy COAL_BIT Δ, TWh |
    |---|---|
    | 2019 | −11.2 |
    | 2020 | −12.2 |
    | 2021 | −5.0 |
    | 2022 | −1.4 |
    | 2023 | −3.4 |
    | 2024 | −2.3 |
    | 2025 | −1.1 |

  - **ST_GAS:** 2019 and 2020 rise between +0.4 and +2.5 TWh. In the other years ΔST_GAS is 0 … +1.2.
  - **CC_REGULAR** rises (greedy +0.9 … +4.4). **CT_PEAKER** rises or stays equal (greedy +0.2 … +6.2).
  - **Nuclear, hydro, wind and solar:** |Δ| ≤ 0.1 TWh.
  - **The measured plants.** The `_mustrun` output at Bowen, Miller and Scherer is equal to the keeper's to within
    0.01 TWh.
- **E2 (2019 C1).** ST_GAS moves from −7.94 TWh / −3.12 pp toward band, and the greedy puts it at −2.65 pp,
  PASS. **2019 COAL_BIT is expected to FAIL:** the greedy puts it at −3.93 pp, against +0.45 pp in the keeper.
  The failing C1 row is therefore expected to MOVE, not vanish, and the determination is expected to stay NOT-YET.
- **E3 (other C1 rows).**
  - **2020 COAL_BIT** (greedy −2.94 pp) is declared a coin toss.
  - **2023 CT_PEAKER** rises (greedy +2.77 pp) and stays PASS.
  - No other row changes status.
- **E4 (unserved).** Unserved stays 0 MWh in every year. The arm moves no capacity out of the fleet.
- **E5 (other criteria).**
  - C2 and C6 PASS.
  - C8: the COAL_BIT forced share falls or stays equal.
  - C4: coal NRMSE may move either way and is reported, not predicted.
  - C3a/b/c stay UNSCORABLE.
  - `gen_soco60b` B1/B2 are unchanged, because they are benchmark-side.

## 5. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff** all three of these hold:

- All seven legs solve cleanly with the §3 hard stops met.
- In every leg, the set of removed `_mustrun` tranches equals the §2 census. The measured plants' `_mustrun`
  hourly capacity is identical to the keeper's leg.
- No year's unserved energy increases against the keeper.

This holds **whatever C1–C8 do**. The mechanism withdraws a floor with no driver, window or measured level, which
binds in hours the plant's own record shows offline. Rule 17 calls that a bug by definition. Gate regressions,
including the expected 2019 COAL_BIT failure, are reported at full magnitude. The owner decides (rule 31), and the
owner's standing ruling is "if structural integrity improves but gates regress that may still be a keeper".

If the owner promotes, rule 35 prunes `2026-09-25-soco68-summer-basis`. The incoming run covers the full union
{2019, …, 2025}, the year set enumerated from every registered SOCO sidecar.

## 6. Retrievability (rule 34(e))

- **Legs.** Each shard pushes `results/calibration/soco69_<Y>/` (full bundle, including `dispatch/`) to
  `claude/soco69-<Y>`.
- **Composite.** The parent composes `soco69_span` and lands it on `main` via the lane PR. The per-year dirs are
  gitignored in the parent.
- **Cost.** Any leg not landed is costed as a re-solve, ~3–15 min of LP per year.

## 7. Addendum: G-DRIFT at the solve SHA (rule 29(b)), recorded before any shard ran

The instrument in FINDING §0 ran at `d5d5e0e8`. `main` then advanced before this document was pinned, so the
solve-path diff `d5d5e0e8..<pinned SHA>` over `src/market_sim`, `scripts/run_calibration*.py`,
`scripts/replay_keeper.py`, `scripts/lib` and `data/raw/{_validation-source,reference,_processed-legacy}` was also
classified:

| file | change | classification |
|---|---|---|
| `config/scenarios.py` | the field `wefor_residual_short_screened_coal` | INERT: default `False`, absent from the keeper recipe and from the eight `--set` fields |
| `data/fleet/arrays.py` | a relief gated on that field | INERT: the same gate |
| `data/outages.py` | the helper `short_screened_coal_shares`, read only inside that gate | INERT: the same gate |
| `data/floor_mechanisms.py` | a registry entry for that field | INERT: the same gate |

The one new field is miso-273's, and its matrix row is miso-273's duty. **All hunks are INERT, so form 4 stands
and the committed `soco68_span` remains the control.**
