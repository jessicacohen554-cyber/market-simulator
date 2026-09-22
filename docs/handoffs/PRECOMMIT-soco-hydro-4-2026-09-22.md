# PRECOMMIT — SOCO hydro-4: hydro dispatch physics (2026-09-22)

Lane: SOCO hydro-4. Control: the committed keeper `2026-09-22-soco58-warm-committed`
(`results/calibration/soco58_warm_committed`, years 2023–2025), rule 29 (b) form 4 — **no control
solve**. Parent LP cost: **zero** (rule 32 (a)). Written and pushed **before** any shard solves.

## 1. The defect (zero-LP, keeper's own committed `class_hourly_<y>.parquet`)

| year | model hydro TWh | 0-MW hours | p05 MW | p95 MW | top-decile share | measured (EIA-930 `NG: WAT`) top-decile | measured 0-hrs | measured p05 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 6.815 | 1,674 | 0.0 | 3,268 | 0.342 | 0.176 † | 0 | 77 |
| 2024 | 6.301 | 1,962 | 0.0 | 3,128 | 0.302 | 0.174 † | 0 | 74 |
| 2025 | **0.327** | 4,561 | 0.0 | 256 | 0.605 | 0.141 | 0 | 75 |

Top-decile share here is computed against EIA-930 SOCO demand (hydro-1 §D used model load; values
differ in the third decimal). † = PS-folded series, an upper bound (see §2.2).

**The G3 target is the measured SOCO fleet, not 0.10.** SOCO hydro is genuinely a peaking fleet —
measured top-decile share 0.14–0.18 — so "toward 0.10" would over-flatten it. G3 reads direction
and distance against the measured column.

## 2. Two findings made before any solve

### 2.1 2025 is the SOCO-53b hole, and it makes both arms degenerate in 2025

The keeper's 2025 budget is the EIA-923 **early release: 5 of 42 plants, 0.328 TWh** (EIA-930
measured 5.926 TWh; `--hydro-backfill-year 2024` restores 42 plants / 6.329 TWh). Already routed as
SOCO-53b (`FINDING-soco-58` §7.1), never executed. Zero-LP consequence for this lane:

| year | ARM 1 floor, MW-avg | share of hydro energy forced | ARM 2 flat, MW-avg | share forced |
|---|---:|---:|---:|---:|
| 2023 | 265.6 | 0.341 | 276.7 | 0.356 |
| 2024 | 196.9 | 0.274 | 249.7 | 0.347 |
| 2025 (keeper budget) | 37.4 | **1.000** (floor > budget, clipped) | 1.7 | 0.047 |

On the 2025 hole ARM 1 is a fully-flat fleet and ARM 2 is inert — **both would test the hole, not
the mechanism.** 2025 legs are therefore NOT launched in this batch; the 2025 instrument is put to
the owner (rule 35 (c): no promotion until 2025 is covered).

### 2.2 SOCO's `NG: WAT` IS PS-folded before 2024-07-15 — registry absence is not cleanliness

SOCO is absent from `EIA930_PS_FOLDED_INTO_WAT` and `EIA930_PS_SPLIT_COMPLETE_FROM`, but it files
`NG: PS` only from **2024-07-15 01:00 local** (24 h in 2024-H1-equivalent, 8,633 h in 2025).
EIA-930 `WAT` exceeds EIA-923 `HY` by +24 % (2023) and +10 % (2024). Same class as NEISO (neiso-72).
**Effect on ARM 1 (reads monthly Q05 of `NG: WAT`), measured in 2025 where both series exist:**
folding PS discharge in moves the monthly Q05 by **≤ +11 MW** (max, May/Jun), i.e. ≤ 2 %. `WAT`
never goes negative in 2023–24, so the fold is discharge-only, not net-of-pumping. ARM 1 is
therefore admissible in 2023–24 under rule 14's misalignment clause with that bound stated.
The registry entry itself (a first-wholly-split year of 2025) is a separate code fix, recorded not
made here — it touches only the `eia930_monthly` pin, which the keeper does not arm.

## 3. The two arms (separate, never stacked — rule 19)

| arm | delta vs keeper | shard out-dirs |
|---|---|---|
| ARM 1 | `hydro_min_flow_floor=true` | `soco_h4_mff_2023`, `soco_h4_mff_2024` |
| ARM 2 | `hydro_ror_split=true` | `soco_h4_ror_2023`, `soco_h4_ror_2024` |

ARM 2 classifier: `curate_hydro_plant_modes.py --iso SOCO` → 45 plants / 3,320 MW, 17 RoR-class;
`sha256 46d94a07153ca1f8ee8d48e6a8a065aaee6f6b397fc035c1f7c37b80542a4e45`. Completion validation
**30/40 plants, 71.3 % of labelled MW** — weak, but completion methods cover only **6.4 % / 5.5 %**
of 2023 / 2024 hydro energy; 94 % is direct EHA `Mode` labels. RoR class = 35.6 % / 34.7 % of energy
(Walter Bouldin, Lay, Mitchell, Jordan, Millers Ferry, Holt, Sinclair, Yates …). RoR nameplate clip
removes 176 / 93 MWh (0.003 % / 0.002 %) — below G2 by 30×.

## 4. Gates (fixed here, before any solve)

- **G1 liveness** — the stamped level is present and binds: ARM 1 floor MW-avg ≈ §2.1 values; the
  arm's hydro hourly minimum ≥ the month's stamped fleet level − 1 MW in every month; ARM 2 flat
  plants read exactly their stamped level. FAIL = mechanism inert.
- **G2 invariant** — |annual hydro TWh (arm) − keeper| / keeper < 0.1 %. A breach is a defect.
- **G3 target** — 0-MW hours fall toward the measured 0; top-decile share falls toward the measured
  0.176 / 0.174 (upper bounds). Overshoot below the measured value is reported as over-flattening.
- **G4 no silent breakage** — C1 / C2 / C3a / C3b re-scored per year against the keeper; every
  movement reported at full magnitude, **no criterion selects between the arms** (rule 1).

**Arm choice rule (fixed now):** the arm is chosen on which driver is real for SOCO's fleet —
per-plant EHA operating mode (ARM 2) vs a fleet-level measured minimum release (ARM 1) — never on
which one moves a criterion. Both are reported.

## 5. Shards

One shard per (arm, year), rule 36; pinned SHA = the commit carrying this file; each pushes its full
bundle incl. `dispatch/<y>_P1.parquet` via a `.gitignore` negation + plain `git add` (rule 34 (a)).
Parent `.gitignore` carries `results/calibration/soco_h4_*_20[0-9][0-9]/` (rule 31: kept out of
`main`, never `rm`'d).

---

## ADDENDUM A (before any 2025 solve) — owner ruling on 2025: "Repair + arms"

2025 runs as three year-isolated shards, all carrying `hydro_backfill_year=2024` (SOCO-53b repair,
routed via `replay_keeper.py --set` as a `solve_and_persist` kwarg):

| leg | deltas vs keeper | role |
|---|---|---|
| `soco_h4_fix_2025` | `hydro_backfill_year=2024` | 2025 control for the arms (this IS an arm of its own: SOCO-53b) |
| `soco_h4_mff_2025` | + `hydro_min_flow_floor=true` | ARM 1, diffed vs `fix_2025` |
| `soco_h4_ror_2025` | + `hydro_ror_split=true` | ARM 2, diffed vs `fix_2025` |

Each arm stays a single lever relative to its control. Instrument choice: `--hydro-backfill-year 2024`
(EIA-923 plant census, 42 plants, 6.329 TWh, carrying 2024's monthly generation) over
`--hydro-eia930-monthly` (5.926 TWh measured): the pin would need SOCO's PS time-split registered
first (§2.2), which is out of scope. Stated misalignment: the backfilled level is **+6.8 %** over
2025 measured `NG: WAT` (which is PS-clean in 2025) and carries 2024's monthly shape.

Zero-LP G1 on the repaired budget: ARM 1 floor 213.4 MW-avg = 0.295 of energy; ARM 2 flat 250.1 MW-avg
= 0.346, nameplate clip 211 MWh (0.003 %). **G2 for the 2025 arms is measured against `fix_2025`**;
`fix_2025` vs keeper is reported (it moves annual hydro 0.327 → 6.329 TWh by design).
