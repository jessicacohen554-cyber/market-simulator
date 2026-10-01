# PRECOMMIT — SOCO-60 (2026-09-23): the SOCO-59 2025 hydro repair, combined with the hydro-4 keeper

**Lane** SOCO-60 · **DATA PROFILE** soco · **Model** Opus (rule 27 — scope writes `scripts/`).
**Control of record** `2026-09-22-soco-h4-hydro-ror` (`results/calibration/soco_h4_ror_span`), rule 29
(b) **form 4** — no control solve. **Arm** ONE delta: `--set hydro_eia930_monthly=true` on the h4-ror
recipe (`hydro_backfill_year=2024` carried span-wide; a measured no-op in 2023/2024).
**Written and pushed BEFORE any LP is solved.**

Preconditions verified on `main` @ `ec090957`: `keepers/SOCO.json` keeper ==
`2026-09-22-soco-h4-hydro-ror`; `constants.EIA930_PS_SPLIT_COMPLETE_FROM == {"NEISO": 2025, "SOCO": 2025}`.

---

## 0. HEADLINE, EX ANTE

1. **This arm buys no gate.** 2023/2024 are predicted byte-identical to the keeper (the pin is refused
   there). In 2025 every C1/C2 row is SKIPPED (preliminary EIA-923 vintage); only C4 and C8 are scored,
   and neither is near its gate. **If the only argument for this arm were that 2025 C4 coal passes, it
   would not be taken** — it already passes by 0.098 of NRMSE.
2. **It is taken on rule 14 `[R-ACCURATE]` alone.** The keeper's 2025 hydro is 2024's water on 2025's
   calendar (6.329 TWh, 2024's monthly shape, a SOCO-53b stand-in its own RESULT §4.1 says must be
   replaced). The arm puts 2025 on its own measured EIA-930 series: **5.926 TWh, January halved,
   June ×2.47.** Zero new fields, zero free parameters.

## 1. RULE 19 AT THE HYDRO GRAIN — the RoR carve and the pin compose, and nothing else moves

`scripts/probes/_soco60_phase0.py`, **each side in its own process** (SOCO-59 P14). `build_hydro_fleet`
with `ror_split=True, backfill_year=2024`, `eia930_monthly` False (ctl) vs True (arm). The classifier is
the curated `hydro-plant-modes` SOCO partition, content hash **`ea00e49bf5be`** — identical to the one the
keeper's 2025 leg pinned (`meta.json → _shared/SOCO/hydro_plant_modes-ea00e49bf5be.parquet`).

| year | units | hydro TWh ctl → arm | RoR plants (in LP) | RoR TWh ctl → arm | RoR flat MW-avg ctl → arm | identical |
|---|---|---|---|---|---|---|
| 2023 | 42/42 | 6.8150 → 6.8150 | 14 | 2.424 → 2.424 | 276.7 → 276.7 | **byte-identical** |
| 2024 | 42/42 | 6.3015 → 6.3015 | 14 | 2.188 → 2.188 | 249.7 → 249.7 | **byte-identical** |
| 2025 | 42/42 | 6.3290 → **5.9258** | 14 | 2.191 → **2.028** | 250.1 → **230.9** | no — the repair |

2025 monthly, ctl → arm (TWh): Jan 0.856→**0.432**, Feb .829→.761, Mar .945→.664, Apr .592→.684,
May .626→**.959**, Jun .280→**.692**, Jul .341→.360, Aug .277→.395, Sep .390→.230, Oct .343→.235,
Nov .360→.278, Dec .489→.235. RoR fleet flat MW Jan 423→213, Jun 126→307, Jul 146→155.

**The interaction is exactly the expected one:** the pin rescales each plant's monthly budget
(within-month plant shares preserved) *before* the RoR carve, and the carve is the pinned
`budget[g,m]/hours[m]` on every RoR plant-month (checked: `allclose`). RoR share of energy stays ~34 %.

**One side effect, reported not repaired — the nameplate clip.** The pin is a uniform per-month rescale,
so in 2025 May/June it pushes three small RoR plants above nameplate (706: 8.5 MW-avg vs 5.4 MW;
54322, 54462). `build_hydro_fleet` clips the flat level to nameplate: **5 plant-months, 5.45 GWh
(0.09 % of 2025 hydro; 0.27 % of RoR energy)** vs 3 plant-months / 0.21 GWh in the control. Below the
hydro-4 G2 tolerance (0.1 %). The repair for it exists (`nameplate_aware_target`, default off) and is
not this lane's delta (rule 19: one delta).

**Rule 19 at the fleet grain** (`_soco59_rule19.py --bundle results/calibration/soco_h4_ror_YEAR`,
keyed by `unit_id`, `fleet_only` rebuilds off each control leg's own recipe): 327 units every year,
0 added / 0 removed. 2023 and 2024: `fuel_prices`, `mc_base`, `pmax`, `availability`, `heat_rate`
**0.000000000000, 0 keys moved**. 2025: `fuel_prices` / `mc_base` / `pmax` / `heat_rate` 0 moved;
**`availability` and `min_gen` move on exactly 14 units, the same 14, all `hydro`** — the RoR plants,
whose flat level is both their cap and their floor. **Zero thermal keys move in any year.**

What separates an armed 2023/2024 leg from the control is therefore not the LP (predicted identical) but
(a) `meta.json` `hydro_eia930_monthly=true` / `hydro_backfill_year=2024` and (b) `solve_surface.rows ==
184` (the SOCO registry row) against the control's 183. The compose script asserts both, in both
directions.

## 2. THE 2025 SCARCITY RISK — sized ex ante; unserved energy does not rise

The keeper's 2025 leg sheds **287.1 MWh in 2 zone-hours** (hours 5030–5031, 2025-07-29; RESULT-hydro-4
§3, a routed demand finding). `scripts/probes/_soco60_scarcity.py` bounds the arm from the control leg's
`unit_hourly` sidecar: non-hydro units rise to their hourly `cap_mw`, everything else in the balance is
held at the control's value, RoR is fixed at the side's flat level, and the reservoir class water-fills
each month under its 2,379 MW nameplate. **Validated on the control:** the construction finds the same
single binding hour (5030) at 178 MWh vs the actual 287 (pooling SOCO's three zones is optimistic).

| | RoR MW Jan / Jul | reservoir GWh Jan / Jul | min unserved (relaxation) | binding hours |
|---|---|---|---|---|
| control | 423 / 146 | 541 / 232 | 178.4 MWh | 5030 |
| **arm** | 213 / 155 | 273 / 245 | **170.2 MWh (−8.3)** | 5030 |

- **The drier winter does not bind.** In the arm's worst January hour, non-hydro headroom still exceeds
  demand by **1.6 GW with zero reservoir water**; Oct–Dec by 2.3–5.5 GW.
- **July is capacity-bound, not energy-bound**: the peak need exceeds the reservoir nameplate (2,549 vs
  2,379 MW) while July uses 7 GWh of 245 available. The arm's July water is *up* (+5.6 %), so its RoR
  base rises +9 MW and unserved falls by ~that × the binding hours.
- The only other months with any positive need are Jun / Aug / Sep (≤ 1.6 GWh against 172–469 GWh).

## 3. CHECK D — every scored row, against `main`'s bench part (the repaired one: 2023 hydro 6.815)

2023/2024 rows cannot move (§1). 2025 C1/C2/sysvol are SKIPPED. The scored 2025 rows:

| row | keeper | gate | margin |
|---|---|---|---|
| C4 2025 coal | r 0.873 / NRMSE 0.202 | r ≥ 0.70, NRMSE ≤ 0.30 | 0.098 NRMSE |
| C4 2025 gas | r 0.955 / NRMSE 0.085 | same | 0.215 NRMSE |
| C8 2025 ST_GAS | 18.1 % (0.546 / 3.016 TWh) | < 30 % | 11.9 pp |
| C8 2025 CT_PEAKER / CC_REGULAR / COAL | 0.0 % | 15 / 30 / 30 % | — |
| C8 2025 hydro | 0.0 % (D-2 does not attribute the RoR stamps — RESULT-hydro-4 §4.3) | 30 % | — |

The single failing row is **2024 CC_REGULAR (+9.80 TWh, +3.59 pp)**, untouchable here. Thinnest passing
C1 row: 2023 ST_GAS (−2.81 pp, 0.19 pp margin), untouchable here.

**Magnitude analog, measured:** the same pin delta WITHOUT the RoR split is SOCO-59's 2025 leg minus
hydro-4's backfill-only `soco_h4_fix_2025` leg (`95d058b3…`, fetched): hydro −0.409, CC_REGULAR
+0.438, CT_PEAKER +0.124, ST_GAS −0.154, COAL_BIT +0.067, COAL_PRB −0.050 TWh. `ST_GAS` falls although
water falls — the shape effect (winter water moves to May/June).

## 4. PREDICTIONS — ex ante, analog bands ±2× symmetric

| # | prediction | falsifier |
|---|---|---|
| P1 | 2023 and 2024 legs: `class_hourly`, `system`, `class_band_hourly`, `storage`, `unit_hourly` sidecars **byte-identical** to the keeper's legs | any byte differs AND any class moves ≥ 0.001 TWh |
| P2 | 2025 LP hydro 6.329 → **5.915–5.925 TWh** (target 5.926 less the 5.45 GWh clip) | outside |
| P3 | 2025 class Δ vs keeper: CC_REGULAR **+0.22…+0.88**; CT_PEAKER **+0.06…+0.25**; ST_GAS **−0.08…−0.31**; COAL_PRB+COAL_BIT \|Δ\| < 0.20 | any class outside its band |
| P4 | 2025 unserved **250–300 MWh**, only in hours 5030–5031; **no unserved hour in any other month** | outside, or any new scarcity hour |
| P5 | 2025 RoR plants read exactly their stamped flat level (arm stamps, §1) in every hour | any RoR hour off its stamp by > 1 MW |
| P6 | C4 2025 coal NRMSE **0.18–0.22**, r **0.85–0.89**, PASS | outside, or FAIL |
| P7 | C4 2025 gas NRMSE **0.07–0.12**, r ≥ **0.93**, PASS | outside, or FAIL |
| P8 | C8 2025 ST_GAS **0.18–0.21**, PASS; hydro 0.000 | outside |
| P9 | determination `NOT-YET`; C1 13/14; 2024 CC_REGULAR +9.80 TWh / +3.59 pp unchanged; `grade_summary` 5/4/1 | any status or grade change |
| P10 | DOF ledger unchanged in count (the keeper's) — zero new free parameters | any added entry |
| P11 | `solve_surface.rows == 184` on every arm leg; the SOCO registry row is the only surface difference vs the control's 183 | anything else |

The 2025 load-weighted price is not predicted (it is dominated by the two $61,900 scarcity hours); it is
reported.

## 5. G-DRIFT (rule 29 (b)) — the keeper's committed legs are a valid control

`git diff a5e5f237 HEAD` and `git diff 4b6c6d96 HEAD` over `src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`: 7 files, the
same set from both bases.

| hunk | class | reason |
|---|---|---|
| `nwpp_grid_carried_wind_served` (scenarios.py field + cache-key registration + TIER_TAGS; `run_calibration.py`, `run_calibration_full.py`, `runner.py`, `eia930/demand.py`, `eia930/envelopes.py` plumbing) | **INERT** | default-off `ScenarioConfig` flag absent from the keeper's recipe, NWPP-only branch (`iso == "NWPP"`) |
| `constants.EIA930_PS_SPLIT_COMPLETE_FROM` gains `"SOCO": 2025` | **INERT for the control** | read only by `eia930_wat_level_folded`, reached on the backcast path only through the `eia930_monthly` pin (off in the control recipe) and the benchmark's `_hydro_benchmark_is_923_only` (already live in `main`'s bench part). It IS this arm's mechanism. |

**All hunks INERT for the control ⇒ form 4 valid.**

## 6. THE SOLVE — three shards, one year each (rule 36 (a)), parent LP cost ZERO

Pinned to this PRECOMMIT's commit SHA. Each shard recovers its control leg at zero LP and replays it:

```
git fetch origin <leg sha> && git checkout <leg sha> -- results/calibration/soco_h4_ror_<Y>/
PYTHONPATH=. python3 scripts/data/curate_hydro_plant_modes.py --iso SOCO
python3 scripts/replay_keeper.py results/calibration/soco_h4_ror_<Y> --years <Y> \
  --out-dir results/calibration/soco60_arm_<Y> \
  --set hydro_backfill_year=2024 --set hydro_eia930_monthly=true \
  --note "SOCO-60 ARM <Y>: hydro_eia930_monthly=true on the h4-ror keeper, year-isolated (rule 36)"
```

Control legs: 2023 `ba61f3135a4407243054ede9530690401d1b7ce9`, 2024
`f2511588a57dbdd97a960c2c010ed6a7478cac8f`, 2025 `9d113ba2a8784321edae35d59b2605d0be80b616`.
Hard stops: pinned SHA · dependency asserts · classifier content hash `ea00e49bf5be` in the leg's
`meta.json` · **post-solve** signature (seven prb postures incl. `hydro_ror_split: true`,
`gas_plant_monthly_fuel_pricing: false`, resolved `coal_prb_sigmoid_overrides` null, `meta.json`
`hydro_backfill_year == 2024` AND `hydro_eia930_monthly == true`, `solve_surface.rows == 184`, every
`offer_curve_by_group` band 1.0) · foreground solve · `--note`. Full-bundle push by `.gitignore` negation
and plain `git add` (rule 34 (a)). The parent composes with `scripts/probes/soco60_compose_span.py`
and repairs `_shared/SOCO/` with `run_calibration_full.py --iso SOCO --rebuild-benchmark <composite>`.

## 7. PROMOTION RULE, FIXED NOW

Owner's standing SOCO ruling: *"Is this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper."* The combined run is recommended iff
P1 holds (2023/2024 identical — otherwise it is not a combination but something new, and it goes back to
the owner) and no scored status regresses; the 2025 input is more accurate by construction. A 2025 C4/C8
move within its band is not a reason either way (rule 1). On promotion, both `2026-09-22-soco-h4-hydro-ror`
and `2026-09-22-soco59-hydro-split` are superseded (the owner ruled promote on both); the unruled
`2026-09-20-soco53g-prb-own-iso` is kept (rule 31).
