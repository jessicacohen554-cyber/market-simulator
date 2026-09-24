# PRECOMMIT — SOCO-61 (2026-09-24): a CC unit dark all of 2024 is modelled fully available; the per-unit outage extract drops whole-year darkness at a running plant

**Lane** SOCO-61 · **DATA PROFILE** soco · **Model** Opus (rule 27 — scope writes `src/` and `scripts/`).
**Control of record** keeper `2026-09-23-soco60-boundary-span` (`results/calibration/soco60_boundary_span`),
rule 29 (b) **form 4** — no control solve. Its per-plant legs (`soco60_armB_<Y>`, SHAs `02b50bfc…`,
`1f129c95…`, `df1d5eb0…`) were recovered at zero LP; all 12 hourly sidecars are byte-identical to the
committed composite.
**Arm** ONE delta: `--set campd_dark_unit_year_windows=true` (new `ScenarioConfig` field, this PR).
**Written and pushed BEFORE any LP is solved.**

Preconditions verified on `main` @ `9820e1c4`: soco-60b merged; `keepers/SOCO.json` keeper ==
`2026-09-23-soco60-boundary-span`.

---

## 0. HEADLINE, EX ANTE

1. **Object targeted: (1) the thin 2024 CC_REGULAR share margin and (2) the CC per-plant misallocation.**
   Not (3): coal and steam are under-dispatched for merit-order reasons, not availability (§2).
2. **The lever is a data-admissibility repair, not a new availability mechanism.** Tenaska Lindsay Hill
   (55271) unit CT3, 313.1 MW, a third of the plant, **ran zero hours in 2024**. CAMPD files 8,784 rows
   for it, all `opTime` 0; the same unit id produced 642 GWh in 2023 and 308 GWh in 2025. The committed
   per-unit outage extract carries **no 2024 window** for it, so the model has it fully available all
   year, and the plant runs +1.73 TWh over its EIA-923 actual.
3. **It buys no gate; every status is predicted unchanged.** *If the only argument for this arm were that
   the 2024 CC_REGULAR share margin widens, it would not be taken.* It is taken on rule 14 alone: the
   model cannot dispatch a turbine that did not run.

## 1. THE DEFECT, TRACED

`derive_campd_unit_outages.py` skips a unit that never produced gross output in a year, on purpose:
*"we cannot distinguish a real full-year outage from a unit monitored under another id, and have no
capacity basis for it."* Its only full-year hook, `eia923_netzero`, works at **plant** grain. A unit dark
all year at a plant whose peers ran therefore falls through both layers.

Neither doubt applies to CT3: its **own id** files every hour of 2024 (so it is not monitored elsewhere),
and it has an EIA-860 capacity basis (313.1 MW, `eia_digits_cc`, the same basis as its 2023 and 2025
windows).

| year | CT1 op h | CT2 op h | CT3 op h | CT3 gross | CT3 windows in the committed extract |
|---|---|---|---|---|---|
| 2023 | 5,300 | 4,422 | 2,863 | 642 GWh | 10 (incl. 2023-08-23 → 12-31) |
| **2024** | 3,733 | 3,732 | **0** | **0** | **none** |
| 2025 | 3,904 | 2,141 | 1,433 | 308 GWh | 10 (incl. 2025-01-01 → 06-18) |

**Census (zero LP, `scripts/probes/_soco61_phase0.py dark_units`).** Across SOCO's CAMPD 2023–2025, the
units dark all year with same-id output in an adjacent year are: Lindsay Hill CT3 (2024, **CC_REGULAR**),
plus Walton Discover 2B, Baconton CT1 and four Walton Bainbridge oil CTs. The latter are all CT peakers,
which the outage overlay excludes by convention. **Exactly one unit-year in an outage-bearing class.**

## 2. THE THREE LEADS, MEASURED

**Lead (1), CC capability** (`_soco61_phase0.py cc`: model availability vs CAMPD monthly hourly-gross p99):

| 2024 | model − 923 | model util of avail | avail mean MW | CAMPD p99 MW | months avail > p99 |
|---|---|---|---|---|---|
| E B Harris 7897 | +2.01 | 1.000 | 798 | 1,361 | 0 |
| **Lindsay Hill 55271** | **+1.73** | 0.793 | 502 | **576** | **10** |
| H A Franklin 7710 | +1.48 | 1.000 | 1,509 | 2,073 | 0 |
| Central Alabama 55440 | +0.88 | 0.834 | 598 | 930 | 0 |

The big over-dispatched plants run **below** their measured capability; their overshoot is economic
(heat rate already measured, SOCO-57), and no availability lever reaches them. **Lindsay Hill is the only
over-dispatched CC plant whose model capability exceeds what it physically delivered**, and CT3 is why.

**Lead (2), coal availability** (`_soco61_phase0.py coal`). The under-dispatched coal plants run at
**0.35–0.70** of their model availability (Scherer 0.35, Bowen 0.60, Miller 0.70), with availability far
above their actual output. The shortfall is merit order (SOCO-56 §2), not availability. **Closed ex ante;
no lever.** Barry (3) coal remains over (+1.65 TWh in 2024; the stale EIA-860 row, SOCO-56 §3), untouched.

**Lead (3), ST vs CC fuel separation.** The model's ST_GAS generation-weighted `mc` ($32–34/MWh) sits at
the CT level. SOCO-54 §4's measured separation still has no forward-regenerable input in this repo.
**Not opened.**

## 3. THE CONSTRUCTION — zero free parameters, byte-identical off

- **Deriver:** `--dark-unit-years` (default off, requires `--per-unit-crosswalk`, standard extract only)
  emits ONE full-year window for a unit when **all** of these hold, each categorical: every hour of the
  year has a row under its own id; no hour has positive `opTime`; the same facility/unit id reported
  positive gross in year − 1 or year + 1; it has an EIA-860 capacity basis; and a peer unit at the
  facility ran. Output goes to the separate companion `campd-unit-outages-perunitdark-SOCO.csv`
  (sha256 `3b3e5a0d…`). **The control re-derive (`--per-unit-crosswalk` alone) reproduces the committed
  `-perunit-` extract byte-for-byte, before and after the edit; the companion differs by exactly one row.**
- **Solve side:** `ScenarioConfig.campd_dark_unit_year_windows` (default False, registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` at `"False"` in the same commit). `outages.unit_outage_csv_for_iso(dark_unit_years=)`
  selects the companion; `fleet/arrays.py` passes it predicated on `campd_per_unit_attribution`;
  `resolved_inputs` records the path actually read. Ignored under `campd_outage_merit_order_guard`.
- **Matrix:** new row `campd_dark_unit_year_windows` + a cell in all nine shards (SOCO `O`, others `U`).

**Rule 19 at the `unit_id` grain** (`_soco61_phase0.py fleet` / `fleetcmp`, `fleet_only` rebuilds off
each keeper leg, **each side in its own process**): 327 units every year, unit list identical.
2023 and 2025: `fuel_prices` / `mc_base` / `pmax` / `availability` / `heat_rate` / `min_gen` all
**0.000000000000, 0 keys moved**. 2024: only `availability` moves, on **exactly the four
`CC_REGULAR_SOCO_AL_p55271_*` tranches**. Lindsay Hill availability energy **4.394 → 2.024 TWh**, still
above its 1.752 TWh EIA-923 actual and 1.800 TWh CAMPD gross. `min_gen` is 0 on those tranches, so no
floor exceeds the new cap.

## 4. CHECK D — every scored row (keeper, `main`'s bench part)

2023 and 2025 cannot move (§3). The 2024 rows:

| row | keeper | gate | effect of the arm |
|---|---|---|---|
| C1 CC_REGULAR | +4.43 TWh / **+2.7 pp** | ±7.66 / ±3.00 | toward actual |
| C1 CT_PEAKER | +1.73 / +0.7 pp | same | **away from actual** — margin 5.9 TWh / 2.3 pp |
| C1 ST_GAS | −4.91 / −1.9 pp | same | toward |
| C1 COAL_PRB | −4.59 / −1.6 pp | same | toward |
| C1 COAL_BIT | −1.89 / −0.6 pp | same | toward |
| C4 coal | r 0.847 / NRMSE 0.240 | r ≥ 0.70, ≤ 0.30 | toward (reproduced exactly, then perturbed: 0.234) |
| C4 gas | r 0.952 / 0.113 | same | — |
| C8 ST_GAS | 17.1 % | < 30 % | falls (energy up, floors unchanged) |

**The two rows the brief names as risks (2023 ST_GAS, 2024 COAL_PRB) receive energy; they cannot cross.**
2024 has no unserved energy in the keeper (2025's 267 MWh is untouched).

**Greedy re-stack** (`_soco61_phase0.py restack`, cheapest idle firm headroom by hourly `mc`; hydro,
VRE, nuclear, biomass excluded as energy-limited): 1.853 TWh leaves Lindsay Hill in 7,596 hours and is
re-served by CT_PEAKER +0.646, other CC +0.536, COAL_PRB +0.439, ST_GAS +0.196, COAL_BIT +0.036 TWh.
C4 2024 coal under that coal delta ×0.5 / ×1 / ×2: NRMSE 0.237 / **0.234** / 0.230, r 0.846 / 0.844 / 0.835.
CC per-plant Σ\|model − 923\| 2024: **11.073 → 9.341 TWh**.

## 5. PREDICTIONS — ex ante, greedy ±2× symmetric

| # | prediction | falsifier |
|---|---|---|
| P1 | 2023 and 2025 legs: `class_hourly`, `system`, `class_band_hourly`, `storage` byte-identical to the keeper legs | any byte differs AND any class moves ≥ 0.001 TWh |
| P2 | 2024 Lindsay Hill (55271) 3.485 → **1.40–2.02 TWh** (greedy 1.632) | outside |
| P3 | 2024 class Δ: CC_REGULAR **−0.66…−1.85**; CT_PEAKER **+0.32…+1.29**; COAL_PRB **+0.22…+0.88**; ST_GAS **+0.10…+0.39**; COAL_BIT **0…+0.15** | any outside, or any sign wrong |
| P4 | C1 2024 CC_REGULAR **+2.58…+3.77 TWh**, share **+1.96…+2.44 pp**, PASS | outside, or FAIL |
| P5 | C1 2024 CT_PEAKER ≤ +3.02 TWh / ≤ +1.2 pp, PASS | FAIL |
| P6 | C4 2024 coal NRMSE **0.228–0.238**, r **0.83–0.85**, PASS; C4 gas PASS | outside, or FAIL |
| P7 | C8 2024 ST_GAS forced share **0.150–0.168** | outside |
| P8 | CC per-plant Σ\|m − 923\| 2024 **7.6–10.2 TWh** | outside |
| P9 | every status unchanged: C1 14/14 · free 10/10, C2/C4/C6/C8 PASS, grade 5/5/0 | any status change |
| P10 | 2024 unserved 0; 2025 267.4 MWh unchanged | any change |
| P11 | DOF `n_residual` unchanged at 1 (a categorical data gate, `n_scalars` 0) | any new residual entry |
| P12 | solve surface 185 rows, moved = {ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE} (unchanged); SOCO's cache key moves (field armed) | anything else |

## 6. G-DRIFT (rule 29 (b)) — the keeper's legs are a valid control

`git diff eab5c585 origin/main` (the legs' solve SHA) over `src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`: 7 files.

| hunk | class | reason |
|---|---|---|
| `demand_balance_screen` (scenarios field + cache key + TIER_TAGS; `runner.py`, `run_calibration*.py`, `eia930/demand.py`) | INERT | default-off, absent from the keeper's recipe (pjm-h19) |
| `run_calibration_full` miso-267 changes to `_backfill_eia923_*`, `_reattribute_dual_fuel_oil`, `_benchmark_eia923_frame` | INERT for the LP | benchmark-only, called post-solve; the bench part both runs score against is `main`'s |
| `constants.py`, `benchmark_semantics.py` comment renames (`_soco60b_phase0.py`) | INERT | comments |

## 7. THE SOLVE — three shards, one year each (rules 34 (c) / 36 (a)), parent LP cost ZERO

Only 2024 moves, but every year the keeper carries is solved, so the composite is one recipe. Pinned
to this PRECOMMIT's commit SHA. Each shard:

```
git fetch origin <leg sha> && git checkout <leg sha> -- results/calibration/soco60_armB_<Y>/
PYTHONPATH=. python3 scripts/data/curate_hydro_plant_modes.py --iso SOCO
python3 scripts/replay_keeper.py results/calibration/soco60_armB_<Y> --years <Y> \
  --out-dir results/calibration/soco61_arm_<Y> --set campd_dark_unit_year_windows=true \
  --note "SOCO-61 ARM <Y>: campd_dark_unit_year_windows=true on the soco60-boundary keeper, year-isolated (rule 36)"
```

Control legs: 2023 `02b50bfcfd03e0644170b537162dbeea75ea3885`, 2024 `1f129c954ac094dbf0cb782461b7f591b80e3b09`,
2025 `df1d5eb0c4c04fc48ba49538ae132f1810651ca8`. Hard stops: pinned SHA · dependency asserts ·
`scripts/probes/soco61_compose_span.py --expect-arm true --check-only` on the leg (keeper posture, 185
surface rows, classifier snapshot, the field armed **and** `resolved_inputs.campd_unit_outages.path` =
the `-perunitdark-` file, sha256 `3b3e5a0d…`) · every `offer_curve_by_group` band 1.0 · foreground
solve · `--note`. Branches `claude/soco61-arm-<Y>` (the `soco60*` names collided once). Full bundle
pushed by `.gitignore` negation + plain `git add` (rule 34 (a)).

## 8. PROMOTION RULE, FIXED NOW

Owner's standing SOCO ruling: *"Is this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper."* The run is recommended iff P1 holds,
Lindsay Hill's 2024 output lands at or above its own measured output's neighbourhood (P2), and no scored
status regresses. A move within the P3–P8 bands is not a reason either way (rule 1).
