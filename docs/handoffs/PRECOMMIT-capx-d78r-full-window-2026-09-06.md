# PRE-REGISTRATION — capx D78-R: the sector-gate seam repair on the FULL 2021–2025 window, with the sign line moved to the DECIDED COHORT and the WINDOW TOTAL — fixed BEFORE any solve

**Lane:** capx D78-R (director r#48; pack §D78-R; D78 §8 item 2 is this lane's spec).
Predecessors: `FINDING-capx-d78-2026-09-06.md` (the three-leg screen, identities to the digit, G6
fired), `PRECOMMIT-capx-d78-sector-gate-offer-seam-2026-09-06.md` (§6 the full-window leg runner —
already committed as `docs/handoffs/d78/run_full.sh`; §7 the flip condition),
`FINDING-capx-d58-2026-09-06.md` §5 (the band-calibration lesson), `FINDING-capx-d74-2026-09-06.md`
§9 item 3 (the bracket procedure this document follows).
**Branch:** `claude/capx-d78r-full-window-s35hos`, FRESH off `origin/main` **`acbb5350`**.
**Date:** 2026-09-06. **Model:** Opus. **DATA PROFILE:** `pjm`.
**Pushed before any solve.**

**NOTHING ARMS, AND THIS LANE WRITES NO MECHANISM CODE.** The seam repair is already on main
(#5144, merge `9d25457b`); `retirement_sector_gate` stays default-off and un-overridden for PJM.
This lane is **two solves and a grading**. No new field, no default flip, no `_pjm_config`
override, no parameter value, no keeper, no marker. The owner decides on §6.

---

## 0. Preconditions, checked

| precondition | reading |
|---|---|
| The D78 seam repair (`exit_exempt_unit_ids`) is on main | **PASS** — `retirements.py:2964` (the parameter), `:3707–3708` (the partition after the clearing), `:3133` (the docstring); merge `9d25457b` (#5144) is an ancestor of `acbb5350` |
| `retirement_sector_gate` default-off, registered at `"False"` | **PASS** — unchanged by #5144 (D78 added no field) |
| `capacity_market_supply_clearing_by_iso` armed for PJM through `_pjm_config` (D57 / Q44) | **PASS** — the bare `pjm-t1h` recipe clears the stack, so the seam under test is live |
| The full-window leg runner committed | **PASS** — `docs/handoffs/d78/run_full.sh` (D78 PRECOMMIT §6), unmodified by this lane |
| D65-B-R is the sole board writer until its batch registers | **STANDING** — no D65-B-R FINDING on main at `acbb5350`. This lane commits its sidecar and its `VERDICT_MAP` entry and **HOLDS the `ff-verdicts.json` / `program-status.json` snapshot row**, stated in the FINDING either way (§7) |
| D81 collision (`retirements.py` clearing path) | **NONE** — D78-R touches no code (pack §D81: *"D78-R touches no code, so compose"*) |
| `data/clean` present | **ABSENT at session start**, rebuilt in full with `scripts/regenerate_clean.py` before any leg (as D78 did); the exit code is reported in the FINDING |

---

## 1. What this lane solves — two legs, at HEAD, PJM solo, sequential

| leg | recipe | out-dir | order |
|---|---|---|---|
| **control-P** | bare `pjm-t1h`, gate off | `results/hindcast/pjm-2021-2025-realized-t1h-d78-control-P` | **first**, solo |
| **repaired arm** | `--retirement-sector-gate` | `results/hindcast/pjm-2021-2025-realized-t1h-d78-sectorgate` | second, solo |

Both: `run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year 2025 --vintage 2020
--fuel-variant realized --entry-screen-diagnostics`, through the committed
`docs/handoffs/d78/run_full.sh`, each under a **HEAD guard** (`H0=$(git rev-parse HEAD); <solve>;
[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`). Years sequential inside each invocation, one
invocation at a time (rule 12; a PJM year is ~7–9 GB on this 15 GB / 4-core box).

**Control first is load-bearing**, not incidental: §3's window band is computed **on the control
leg** (D74 §9 item 3) and written into this document as a **numbered addendum BEFORE the arm is
solved**, so it cannot be written to fit the arm.

**Rebase discipline.** `git fetch origin main` between the two legs, never during one. If main
moved, the delta is re-audited as a §2 addendum **before** the arm is solved: an all-INERT delta is
rebased onto and both legs remain comparable; a **LIVE** hunk means control-P is re-solved on the
rebased HEAD before the arm runs. Rule 22: forecast-mode hindcast, 2021–2025, nothing outside
training solved, scored or registered.

---

## 2. G-DRIFT (rule 29(b)) — every solve-path hunk from D78's close `f3fb0988` to HEAD `acbb5350`, classified — **VERDICT: ALL INERT for this recipe**

`git diff --stat f3fb0988 HEAD -- src/market_sim scripts/run_capacity_hindcast.py
scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference` → **10 files, +598 / −750**. Hunk by hunk:

| file(s) | hunks | class |
|---|---|---|
| `config/scenarios.py` (+72) | **miso-225**: two new fields `miso_gas_variable_transport`, `miso_seam_neighbour_anchored_ladder`, both `bool = False`; both registered in `_CACHE_KEY_OPTIONAL_FIELDS` **with** `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` `"False"` (so they DROP from the key at default, the nyiso-119 discipline); a `_BACKCAST_ONLY_OVERLAY_FIELDS` row; two `TIER_TAGS` rows; and a **comment-only** block in `__post_init__` (pure `+` lines, no validation added) | **INERT** — default-off, MISO-scoped, key-dropped |
| `model/interchange/spec.py` (+75) | miso-225: `MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR` and `..._POOLED` — new module-level tables, read only through the new flag | **INERT** — additive data, no consumer at default |
| `model/interchange/miso.py` (+29) | miso-225: `inject_miso_seam_ladder_prices(..., neighbour_anchored: bool = False)`; the overlay applies only `if neighbour_anchored and ladder is not None`; the function still returns `False` immediately for `iso != "MISO"` | **INERT** — default argument `False`; PJM returns at the ISO guard |
| `data/fuel/basis/miso.py` (+141) | miso-225: `_load_miso_gas_variable_transport`, `_miso_gas_variable_transport_vector`, and two point-of-use guards, all inside `apply_miso_gas_marginal_commodity`, which is MISO-gated and armed only by `miso_gas_marginal_commodity_pricing` (default `False`) | **INERT** — off, and another ISO |
| `scripts/run_calibration.py` (+30) | miso-225: the seam-pair point-of-use `raise` and the neighbour-anchored log branch in `run_year` | **INERT** — and doubly so: **`run_capacity_hindcast.py` does not import `run_calibration`** (verified by grep), so this file is not on this lane's solve path at all |
| `data/raw/reference/miso_gas_variable_transport{,.pool}.csv` (+135) | miso-225's frozen derive output | **INERT** — read only under the armed flag; MISO |
| `data/raw/_validation-source/caiso_offer_*` (3 files) | CAISO offer-surface measurements | **INERT** — another ISO's inputs |
| `scripts/run_capacity_hindcast.py`, `scripts/run_calibration_full.py`, `scripts/lib/*` | **no change** | — |

**Config axis, measured not assumed** (`docs/handoffs/d78/keys_probe.py` re-run at HEAD): the
full-span keys resolve to **`15a723ba3b6dc856`** (control-P) and **`bc387828f931e0ac`** (arm) —
**byte-identical to the values D78 declared and realized** (PRECOMMIT-d78 §4). The screen-span keys
likewise (`afda79ba04cbfdbf` / `d527c3299b8c00b5`), and the D65-B attribution still closes
(`move_attributed_to_d65b_entirely: true`). **No key moved since D78's close.** A matched key is
not itself a G-DRIFT verdict (rule 29(b)); the hunk table above is the verdict, and the unmoved key
is corroboration.

**Consequence.** G-DRIFT **form 4 is valid on the code axis**, but this lane still solves its own
control-P because **there is no committed gate-off PJM bundle at this recipe to difference against**:
D78's three screen bundles were deleted under rule 29(c), and the registered `pjm-t1h`
(`pjm-2021-2025-realized-t1h-d57-clearing`, key `f0e050e820c1159a`) is **pre-hunk** — its key is not
`15a723ba3b6dc856`. Differencing against it is precisely the error D58 §5 disclosed against itself.
The control leg is therefore solved, not assumed, and §3's brackets come off it.

---

## 3. THE SIGN LINE, RESTATED — what a candidate-set gate CAN obey

### 3.0 Why G6 was the wrong line, stated first

D78's G6 asked that **executed** economic exits not rise in **either screen year**. They rose in
2022 (7,333.7 → 8,736.7 MW). D78 §4 shows, unit by unit, that the failing pool shrank *exactly* as
the mechanism says (G3 PASS) and that the **R-NEW admission cap re-filled the budget** the 226
sector-1 rows freed: 1,225.8 MW of lag-3 sector-1 coal that would have executed in **2024** was
replaced by 1,871.4 MW of lag-1 merchant gas-steam / CHP executing in **2022** — 70 rows the control
`entry_capped` in 2022 and executed in 2023. The cohort is the same; its **timing** moved a year
earlier. A per-year executed count is therefore a **lag-composition** quantity, not a candidate-set
quantity, and no candidate-set gate can promise anything about it. **This lane does not gate it.**

### 3.1 What is gated (STOP gates; structural, may kill the arm, never promote it)

Screen years are those the 2021–2025 hindcast actually screens; **2022 is the FIRST screen on a
fleet identical to the control's**, so the exact identities live there and the fleet-delta forms
apply from 2023 on (D78 §3.4 established the two forms). No gate reads `retire.total_gw`,
`false_retire`, recall, precision, or any residual.

| # | question | pass condition |
|---|---|---|
| **W0** | **the reproduction test** — the full window re-solves 2021→2022 on a path identical to D78's screen span, so D78's measured 2022 screen must come back to the digit | control-P 2022: failing pool **677 rows / 29,727.898 MW**, `n_offers` **1,370**, `offered_mw` **150,857.184**, `price_takers_mw` **30,577.888**, price **67.760162 $/MW-day**, position **1.048349**, decided **79 rows / 13,177.472 MW**, executed **7,333.7 MW**. Arm 2022: pool **451 / 26,251.375**, decided **128 / 13,354.701**, executed **8,736.687**, and the auction identical to control-P's. Tolerance ±0.001 MW / ±0.000001 $/MW-day. **A miss is a LIVE hunk §2 missed, or a span-dependence in the solve: STOP, re-audit, no grading.** |
| **W1** | **candidate identity** (the charter's (b) fidelity; D78 G3 generalized) | **2022 (identical fleets), EXACT:** the arm's failing pool = control-P's **minus exactly its sector-1 rows**; the **arm-only set is EMPTY**; every shared row's MW identical to the decimal. **2021, and 2023–2025 (fleet-delta form):** every unit present in BOTH pools carries an identical MW to the decimal, and every one-sided row is explained *entirely* by (i) sector-1 gating or (ii) the fleet delta the arm's own earlier exits create — no third explanation |
| **W2** | **decided-cohort composition, EXACT, every year** | **Zero sector-1 rows** in the arm's `decided`, `entry_capped`, `floor_retained`, `throughput_deferred`, `pipeline_events` sets and in `retirements` with `reason == "economic"`, in **every** year 2021–2025 |
| **W3** | **decided-cohort provenance, EXACT, every year** | Every row the arm decides or executes and the control does not is a row the control **`entry_capped` in the same screen year**, or one present only through the fleet delta the arm's own earlier exits create. Nothing enters the arm's candidate universe that was not in the control's on an identical fleet |
| **W4** | **the WINDOW TOTAL, banded on the control leg** | Σ over 2021–2025 of the arm's **`decided_mw`** lies within **Σ_y `decided_mw`(control-P) ± Σ_y g_y**, where **g_y := the largest single-row MW in control-P's year-y failing pool (`decided` ∪ `entry_capped`)**. Numbers filled from control-P in the **§3.3 addendum before the arm is solved** |
| **W5** | **no non-target flip** (the charter's (a) purity) | 2022: `thermal_additions`, `renewable_additions`, `storage_additions`, `announced_derates`, `confirmed_derates`, `ccs_retrofits`, `entry_decided_mw_by_tech`, `peak_demand_mw`, `screen_peak_demand_mw`, `screen_adequacy_requirement_mw`, and every `capacity_clearing` key **identical** to control-P (the D58 §5 instrument miss — `capacity_clearing` omitted from `FOOTPRINT_KEYS` — is not repeated). 2023–2025: the same keys identical **up to the fleet delta**; every unit present in both years' stacks carries an identical offer and `A_g`; `requirement_mw` identical; the census differs by the exit delta alone |

**W4's rationale, stated before the number exists.** `entry_capped` is non-empty in the control
(598 rows / 16,550.4 MW in 2022), so the R-NEW admission cap **binds**: the decided total is
*budget*-determined, not candidate-determined. A candidate-set gate re-spends the same budget from a
smaller pool, so its decided total can differ only by the **granularity of whole-unit admission at
the budget boundary** — bounded by the largest single row the pool can offer. A breach means the
**budget itself moved**, which is a second seam and exactly what a STOP gate should catch. D78's own
2022 screen moved the decided total by **+177.2 MW on 13,177.5 (+1.3 %)**, and its two-screen-year
decided total by **−43.9 MW on 16,282.9 (−0.27 %)** — the band's shape is calibrated by that
measurement, its numbers by control-P.

### 3.2 What is REPORTED at full magnitude and NOT gated (rule 14)

- **Per-year executed economic exits**, both legs, every year — the quantity G6 wrongly gated.
- **The window's executed economic total.** Decided MW whose execution lag exceeds `2025 − y` never
  executes inside the window, and the arm's lag mix differs from the control's by construction
  (§3.0), so the executed total is a window-edge artifact as much as a mechanism effect. Reported
  with its decomposition by execute-year and by fuel; **not a gate in either direction**.
- **FC-3 `retire.total_gw`, `unit_recall_gt300`, `plant_release_precision`, `false_retire`** — the
  §4 pre-declared signs. These feed the flip condition's limb (c) **as a comparison against
  control-P**, never as a band against the actuals (rule 1 `[R-STRUCT]`, rule 14).

### 3.3 ADDENDUM SLOT — the W4 numbers, to be filled from control-P BEFORE the arm is solved

> *Reserved. Filled by a commit that lands after control-P finishes and before `run_full.sh arm`
> starts, carrying: per screen year y ∈ 2021–2025, control-P's `decided_mw`, `capped_mw`, and
> `g_y`; then Σ `decided_mw` and Σ `g_y`, i.e. the W4 interval as two numbers. Nothing else.*

---

## 4. PRE-DECLARED SIGNS — graded at full magnitude, misses included

1. **W0 reproduces** — D78's 2022 screen numbers return to the digit on both legs (§3.1 W0's table).
   *Falsifier:* any of them off by more than the stated tolerance.
2. **W1/W2/W3 hold** — the 2022 pool is the control's minus exactly its sector-1 rows; zero sector-1
   rows anywhere in the arm's decision ledgers in any year. *Falsifier:* one merchant row in the
   2022 arm-only set, or one sector-1 row in any arm decision set.
3. **The window decided total is inside W4's band**, and the arm's per-year decided MW tracks the
   control's within the same per-year granularity. *Falsifier:* a breach — i.e. the budget moved.
4. **The window's executed economic total RISES relative to control-P, or falls by less than the
   sector-1 executed MW the gate removes** — the §3.0 re-fill, restated for five years. Reported,
   **not a gate**. D78's two-screen-year value was **+11.3 %**.
5. **`retire.total_gw` moves DOWN** from control-P, by an amount bounded above by the sector-1
   economic MW control-P releases across the window and below by the cap's re-fill. **Reported, not
   a criterion in either direction** (rule 14) — D58 PREDECL §3 P5 established that PJM's control
   OVER-retires, so a reduction moves the band *toward* the actual, and that is a consequence, never
   evidence for the mechanism; a worse band would not be evidence against it.
6. **`unit_recall_gt300` does not RISE** — a matched large sector-1 exit is no longer reachable, so
   recall can only hold or fall. D78 PRECOMMIT §5 item 7 banded 11–13/20; control-P sets the bar and
   is read first. Reported.
7. **Window `economic` release precision does not FALL** — the released MW the gate removes is
   sector-1, and PJM's real large-exit cohort is only ~10 % sector-1 (D58 §0), so the removed MW is
   disproportionately *not* at a real-exit plant. This one **is** limb (c) of the flip condition.
   *Falsifier:* precision below control-P's.
8. **Keys realized as §5, no collision.**

**Rule 14's line, stated before the solve.** Nothing in items 4–6 is a criterion; each is reported
whichever way it moves, and the arming recommendation in §6 does not read any of them.

---

## 5. Cache keys (through `run_capacity_hindcast.build_config` → `apply_iso_scenario_defaults` → `cache_key()`; re-resolved at HEAD `acbb5350`)

| config | key | check |
|---|---|---|
| control-P, 2021–2025 | **`15a723ba3b6dc856`** | as D78 PRECOMMIT §4; unmoved at HEAD |
| repaired arm, 2021–2025 | **`bc387828f931e0ac`** | as D78 PRECOMMIT §4; unmoved at HEAD; no collision under `results/`, `frontend/`, `docs/`, `src/`, `scripts/`, `tests/` |
| `ScenarioConfig()` default / bare backcast pins | **unmoved by this lane** | this lane writes no code |

**K-a:** any collision, or a realized key ≠ its value here unexplained from the resolved config →
STOP for that leg.

---

## 6. THE FLIP CONDITION — the arming recommendation, PRE-STATED (D58 §5 / D78 PRECOMMIT §7, restated for the full window)

Recommend **ARM for PJM** (`retirement_sector_gate: True` in `iso_configs._pjm_config`
`default_scenario_overrides` — **recommended, never written by this lane**; a `ScenarioConfig`
default flip is a broader act and is not recommended from this leg) **iff ALL FOUR hold**:

- **(a) purity** — **W5** holds on the full window (2022 exact; 2023–2025 in fleet-delta form): the
  gate is once more a candidate-set partition that touches no second seam.
- **(b) fidelity** — **W1 + W2 + W3** hold: the failing pool falls by exactly the sector-1 rows on
  the first identical-fleet screen, zero sector-1 rows reach any decision ledger in any year, and no
  row enters the candidate universe that was not in the control's.
- **(c) composition** — from the full window's `score.json`: window **`plant_release_precision`
  `economic` precision does not fall below control-P's**, and every admitted / decided / executed
  row is at a non-sector-1 plant. `retire.total_gw`, recall and `false_retire` are reported at full
  magnitude beside it and are **not** conditions.
- **(d) LOYO** — `loyo.folds[y].recall` / `recall_band` (scorer-side, no re-solve): the arm **does
  not lose a fold control-P holds**, and `loyo.holds_2of3` does not degrade.

Recommend **HOLD-and-route** if **(a)** fails (the seam is not closed, or a third seam moved).
Recommend **DECLINE** if **(b)**, **(c)** or **(d)** fails. **`retire.total_gw`, `false_retire` and
recall are explicitly NOT conditions in either direction** (rule 14).

---

## 7. STOPs — any one kills the arm; none is promoted past

1. **W0 miss** — D78's 2022 screen not reproduced at HEAD on either leg.
2. **Any key ≠ §5** unexplained from the resolved config, or a collision.
3. **A merchant row in the 2022 arm-only failing set** (W1) — the decoupling reaches beyond sector 1.
4. **A sector-1 row in any arm decision ledger, any year** (W2), or a row entering the arm's
   candidate universe from nowhere (W3).
5. **The 2022 price, `requirement_mw`, `census_mw` or any `capacity_clearing` key moving by any
   amount** between control-P and the arm (W5).
6. **The window decided total outside W4's control-derived band** — the budget moved.
7. **A non-target load-bearing footprint key flipping** on any year (W5).
8. **Wall/RSS beyond the D57 envelope** (14 min / 9.3 GB per solve year).
9. **HEAD moving during a leg** (the guard's `exit 90`), or a LIVE hunk landing between legs without
   control-P being re-solved.

---

## 8. Registration and retention

- **The arm registers SUFFIXED**: bundle `pjm-2021-2025-realized-t1h-d78-sectorgate` →
  `VERDICT_MAP` **`pjm-t1h-d78r-sectorgate`**, through `scripts/register_forecast_run.py --bundle`
  (the committed hindcast sidecar + the slim
  `results/hindcast/<dir>/{meta,run_config,forecast_verdict}.json`, as D57/D62/D63/D74 did). **The
  bare `pjm-t1h` key is untouched.**
- **Board lock.** D65-B-R is the sole writer of `ff-verdicts.json` / `program-status.json` until its
  batch registers; no D65-B-R FINDING is on main at `acbb5350`. This lane therefore **holds the
  `ff-verdicts.json` snapshot row** and commits only the sidecar + `VERDICT_MAP` entry — stated in
  the FINDING either way.
- **control-P is NEVER registered and its bundle is DELETED before merge** (rule 29(c)); the arm's
  bundle keeps only its slim registered files, exactly as every registered PJM T1-H run does. This
  document and the FINDING carry **every number this lane will ever cite**.
- **Rule 28(b):** PJM's `retirement_sector_gate` cell in `docs/codebase-site/data/mechanism-matrix/PJM.js`
  only, with this lane's letter and evidence; no other shard, no new row (this lane adds no field).

---

## 9. Rules, stated

**Rule 1 `[R-STRUCT]`** — the mechanism is PJM's must-offer rule (D78 design §1); every gate is an
identity or a control-derived bracket, none a residual, and no gate reads a score band.
**Rule 12** — PJM solo, two invocations sequential, years sequential within each.
**Rules 13 / 14** — a published market rule that regenerates per delivery year; the sign line is
stated before the solve, on the quantity the mechanism can actually control, and every reported
number is at full magnitude whichever way it moves.
**Rule 19 `[R-ONE-MECH]`** — the D58 one-filter-two-jobs violation is already removed on main;
nothing is stacked on it here. **Rule 21** — zero DOF. **Rule 22** — forecast-mode hindcast
2021–2025; nothing outside training solved, scored or registered; the freeze asserted by the run
banner. **Rules 24 / 25** — no tunable added or changed; PJM's cell only, MISO's `K` untouched.
**Rule 27** — this lane writes no `src/` code; docs edited locally and pushed as exact on-disk bytes,
blob-verified for any file ≥300 lines. **Rule 28** — cell update (b); no row (c).
**Rule 29** — G-DRIFT before any LP (§2); the pre-declaration pushed before any solve; STOP-only
structural gates; control-P's bundle deleted before merge.

## 10. Reproduction

```
uv run python docs/handoffs/d78/keys_probe.py                          # keys at HEAD, zero LP
bash docs/handoffs/d78/run_full.sh control-P                           # leg 1
bash docs/handoffs/d78/run_full.sh arm --retirement-sector-gate        # leg 2 (after the §3.3 addendum)
uv run python docs/handoffs/d78r/window_compare.py --ctl <ctl> --arm <arm>
```

---

# ADDENDUM 1 — the §3.3 W4 band, computed on control-P, BEFORE the arm is solved

**Status:** control-P finished at `16:38:38Z` (22.0 min wall; HEAD guard `41b46142` held; key
**`15a723ba3b6dc856`** realized as declared; run banner asserts the holdout freeze active, solve
years **{2021, 2023, 2024, 2025}**, 2022 **bridged**, scoring bounded to the training window).
**The arm has NOT been solved.** Everything below is a control-only read
(`docs/handoffs/d78r/control_band.json`).

## A1.1 control-P, per screen year

| year | pool rows / MW | of which sector-1 | decided rows / MW | of which sector-1 | capped rows / MW | executed economic MW | `g_y` (max single pool row) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 0 / 0 | — | 0 / 0 | — | 0 / 0 | 0 | 0 (cap does not bind) |
| 2022 | 677 / 29,727.898 | 226 / 3,476.523 | 79 / 13,177.472 | 21 / 1,694.218 | 598 / 16,550.426 | 7,333.700 | **1,254.600** |
| 2023 | 154 / 5,795.183 | 18 / 622.699 | 108 / 3,105.455 | 10 / 332.306 | 46 / 2,689.728 | 3,105.455 | **955.500** |
| 2024 | 3 / 976.806 | 3 / 976.806 | 0 / 0 | — | 3 / 976.806 | 1,189.408 | **594.606** |
| 2025 | 0 / 0 | — | 0 / 0 | — | 0 / 0 | 0 | 0 (cap does not bind) |

## A1.2 THE BAND (W4), fixed here

```
sum_y decided_mw(control-P)  =  16,282.927 MW
sum_y g_y                    =   2,804.706 MW
W4 BAND  =  [ 13,478.221 MW , 19,087.633 MW ]
```

`g_y` is the largest single-row MW in control-P's year-y failing pool (`decided` ∪ `entry_capped`),
and 0 in a year where the cap does not bind — the §3.1 definition, applied verbatim, with no
number chosen by hand. **The arm's window decided total must land inside that interval.**

## A1.3 Two control-only readings, recorded now so they cannot be fitted later

1. **W0's control half already PASSES.** control-P's 2022 screen reproduces D78's measured control
   **to the digit**: pool **677 rows / 29,727.898 MW**, `n_offers` **1,370**, `offered_mw`
   **150,857.184**, `price_takers_mw` **30,577.888**, `price_usd_per_mw_day` **67.760162**,
   `cleared_position` **1.048349**, decided **79 / 13,177.472**, executed **7,333.700**; and 2023
   decided **108 / 3,105.455**. The §2 G-DRIFT verdict is therefore confirmed by measurement on the
   control side before the arm is touched, and the full window's 2021→2022 path is identical to
   D78's screen span as §3.1 W0 assumed.
2. **The control's sector-1 decided MW in 2022 is 21 rows / 1,694.218 MW** — which is exactly
   D78 §4's decomposition read forward (468.460 MW executing 2022 + 1,225.758 MW of lag-3 coal
   executing 2024). The gate has that much budget to free in 2022, 332.306 MW in 2023, and the
   2024 pool is **entirely** sector-1 (3 rows / 976.806 MW, all capped).

**Reported, not gated** (§3.2): control-P's window executed economic total is
**11,628.563 MW** (2022 7,333.700 + 2023 3,105.455 + 2024 1,189.408), and its 2024 executed
economic MW is **entirely sector-1** (13 rows / 1,189.408 MW).

## A1.4 Instrument repair, disclosed (the D58 §5 discipline)

`window_compare.py` as committed at `41b46142` read the clearing price under the key `"price"`;
the ledger's keys are **`price_usd_per_mw_day`** and **`cleared_position`**. Left alone, W0 would
have read `None` and FAILED spuriously on both legs. **Fixed before the arm was solved**, with
`cleared_position` added to W0's row set as a second identity rather than dropped. This is the same
class of error D58 §5 disclosed against itself (`FOOTPRINT_KEYS` omitting `capacity_clearing`), and
it is recorded here rather than in the FINDING because it was found and fixed **before** the
measurement it would have corrupted. No gate, threshold, band or pass condition was changed — only
the key the instrument reads.

**The arm is solved next, at the same HEAD, with this band already fixed.**

---

# ADDENDUM 2 — main moved with LIVE hunks between the legs: both legs are re-solved, and W0 is RESTATED before the re-solve

**Trigger.** The §1 rebase discipline requires `git fetch origin main` between the legs. Main moved
`acbb5350` → **`c3988c73`** (21 commits) while control-P was solving. The delta is audited here,
hunk by hunk, **before** anything is re-solved. Branch rebased onto `c3988c73`; new HEAD
**`f7057f4c`**. Control-P's first solve (at `41b46142`) is **discarded, not graded** — its numbers
appear nowhere in this lane's findings.

## A2.1 G-DRIFT `acbb5350..c3988c73` on the solve path — **THREE LIVE HUNKS**

`git diff --stat acbb5350 c3988c73 -- src/market_sim scripts/run_capacity_hindcast.py scripts/lib
data/raw/_validation-source data/raw/reference` → 12 files, +1,169 / −216.

| file | hunk | class |
|---|---|---|
| `config/iso_configs.py` (+36) | **capx D67-ARM, owner ruling Q52**: `"capacity_adequacy_requirement_published_by_iso": {"PJM": True}` added to `_pjm_config` `default_scenario_overrides`. The adequacy requirement's OPERAND becomes PJM's published whole-RTO Reliability Requirement, at the one `gross_adequacy_requirement_mw` seam **the reliability floor and the reserve-margin backstop both reach through** | **LIVE** |
| `model/capacity_evolution/retirements.py` (+84/−) | **capx D81**: the PENDING dated plants and the this-year retrofits move from `exempt_unit_ids` onto **`exit_exempt_unit_ids`** — the very seam this lane measures. Such a unit now OFFERS its accredited MW at its net-ACR cap instead of landing in `Q_0` at $0 | **LIVE** |
| `model/capacity_evolution/evolve.py` (+96) | **capx D81**'s call-site re-routing of the dated exemption (same seam); plus D65-B-R's `_CCS_RETROFIT_LEDGER_SCALING_FIELDS` record | **LIVE** (D81 half); the CCS half INERT below `ccs_retrofit_available_year` 2028 |
| `results/evolution_ledger.py` (+11) | D65-B-R: the retrofit log's per-host scaling record | **INERT** — ledger-only, and CCS is inert below 2028 |
| `config/scenarios.py` (+101) | D67's `capacity_adequacy_requirement_published_by_iso` field (default `None`, reached here only through the PJM override above) and SCN-CAP's `mass_cap_tons_by_year` | **INERT in itself** — the LIVE path is the `_pjm_config` override, counted once above; `mass_cap_enabled` is `False` on this recipe |
| `policy/cap_and_trade.py` (+56) | SCN-CAP `scheduled_power_sector_budget`, read only under `mass_cap_tons_by_year` | **INERT** — `mass_cap_enabled: False`, `mass_cap_tons: None` |
| `config/constants.py` (55 lines) | owner ruling S9: **comment-only** re-labelling of two carbon-price `mid` knots (`ILLUSTRATIVE` → `committed`); the values are unchanged | **INERT** — and this recipe runs `carbon_price 0.0`, path `zero` |
| `results/cache.py` (+68) | the D65-B-R / capx cache-key re-pin epoch prose | **INERT** in itself; the key move it records is attributed in A2.2 |
| `data/fuel/basis/miso.py` (12 lines) | miso-225 follow-up | **INERT** — MISO |
| `data/raw/_validation-source/caiso_offer_*` (3 files) | CAISO offer-surface measurements | **INERT** — another ISO |

**VERDICT: LIVE.** Under §1's rebase discipline and STOP 9, a LIVE hunk means **control-P is
re-solved on the rebased HEAD before the arm runs**. Both legs are therefore solved at
**`f7057f4c`**, and the A1 band is superseded by A3's.

**Why this is the right call on the merits, not merely on the letter.** D67-ARM changes the
adequacy-requirement operand, which *is* the R-NEW admission-cap budget — the exact quantity W4
bands and the exact mechanism D78 §4 identified as the whole re-fill story. D81 puts a second
exogenous-exit class on **`exit_exempt_unit_ids`**, this lane's own seam. Grading the sector gate
against a control that predates both would recommend arming a mechanism whose interaction with
PJM's shipped posture had never been measured.

## A2.2 The keys MOVED — declared here, before the re-solve

| config | at `acbb5350` (A0 / §5) | **at `c3988c73`** |
|---|---|---|
| control-P, 2021–2025 | `15a723ba3b6dc856` | **`a9c66d8ea25acb9d`** |
| repaired arm, 2021–2025 | `bc387828f931e0ac` | **`bb6a60239d69508b`** |
| control-P, screen span | `afda79ba04cbfdbf` | `6eff06b0ec80f182` |
| arm, screen span | `d527c3299b8c00b5` | `a66b329cf8470dc5` |

Attribution: the D67-ARM override (whose own comment records that the pre-arm posture *"keeps its
key `15a723ba3b6dc856`"*, i.e. the armed PJM default is a different key by design) plus the
D65-B-R / capx cache-key re-pins. **§5's K-a now reads against this row**: the realized keys must
be `a9c66d8ea25acb9d` and `bb6a60239d69508b`.

## A2.3 W0 is RESTATED — its known-answer form is VOID at this HEAD, and that is said BEFORE the re-solve

§3.1's **W0** pinned D78's measured 2022 screen to the digit. Its stated purpose was *"a miss is a
LIVE hunk §2 missed"* — a known-answer test whose validity rested on the §2 all-INERT verdict.
**A2.1 finds LIVE hunks by construction**, and two of them (D67-ARM's requirement operand, D81's
dated must-offer) necessarily move the 2022 screen: the requirement changes the cap's budget, and
the dated block moves from `Q_0` into the offer stack, changing `n_offers`, `offered_mw` and
`price_takers_mw`. **W0 in its original form therefore cannot pass and must not be scored as a
failure.** It is replaced, here and before the re-solve, by:

> **W0′ (REPORTED, not a gate).** Both legs' 2022 screens are reported beside D78's measured
> control, and every difference is **attributed to a named A2.1 LIVE hunk**. A difference that
> **cannot** be attributed to D67-ARM or D81 is a STOP — that is the residual known-answer content
> W0 was carrying, and it survives. The **arm-versus-control** identities W1, W2, W3 and W5 are
> unaffected by this restatement: both legs run the same code, so a candidate-set gate's partition
> is exactly as falsifiable at `f7057f4c` as it was at `41b46142`, and **the flip condition reads
> only those.**

Nothing else in §3, §6 or §7 changes. W1/W2/W3/W5 keep their pass conditions verbatim; W4 keeps its
definition verbatim and takes its numbers from the new control leg in **ADDENDUM 3**; the §6 limbs
(a)–(d) and the §7 STOPs are untouched. **One consequence is recorded now rather than discovered
later:** D81 means the arm's `exit_exempt_unit_ids` set is the sector-1 units **plus** the pending
dated plants and this-year retrofits, in *both* legs — so W2's "zero sector-1 rows in the arm's
decision ledgers" is still exactly the sector gate's own claim, while the dated block is common to
both legs and cancels in the differencing.

**Cost, stated:** control-P's first 22.0 min of LP is discarded. That is the price of the rebase
discipline, and it is cheaper than an arming recommendation against a superseded control.
