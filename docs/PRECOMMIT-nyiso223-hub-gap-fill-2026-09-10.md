# PRECOMMIT — nyiso-223: the hub-daily UNPRICED-DAY gap fill

**Session:** nyiso-223 · **ISO:** NYISO · **Date:** 2026-09-10
**Branch:** `claude/nyiso-223-scarcity-structure-ydjbfw`
**Control:** the committed keeper `2026-09-09-nyiso-221-fuelvintage-span`
(`results/calibration/nyiso_fuelvintage_A`, `git_sha da2e7076`) for 2023–2025, and the
committed 2022 touchpoint bundle `results/calibration/nyiso213_tp2022` for 2022.
G-CTRL **form 4** — **NO control solve is spent** (rule 29(b) `[R-SCREEN]`).

**PUSHED BEFORE THE FIRST LP.** Every number below is registered in advance.

---

## 0. The chartered lever is DEAD. Phase 0 killed it with zero LP spent.

The charter sent this session at **reserve / scarcity price formation** — the ORDC curve,
the reserve requirement, the shortage-pricing path across NYISO's 9 locational families.
Rule 29 `[R-SCREEN]` step 0 is mandatory, it was run first, and **it refutes the lever
before a single solve.** That is the step working exactly as designed, and it is reported
as this session's first result rather than buried.

### 0.1 The statewide families never bind — in any year, in any hour

From the committed `hourly/reserve_family_<year>.parquet` sidecars (P1 rows), the ONLY
artifact in which a locational family's binding is observable:

| family | requirement MW | RCPF $/MW | **binding hours 2022 / 2023 / 2024 / 2025** | max dual realised |
|---|---|---|---|---|
| `nyca_30min_total` | 2620 | 750 | **0 / 0 / 0 / 0** | −0.0 |
| `nyca_10min_total` | 1310 | 750 | **0 / 0 / 0 / 0** | −0.0 |
| `nyca_10min_spin` | 655 | 775 | **0 / 0 / 0 / 0** | −0.0 |
| `east_10min_total` | 1200 | 775 | 9 / 0 / 3 / 2 | 775.0 (2022, once) |
| `seny_30min_total` | 1300(+increment) | 500 | 12 / 4 / 1 / 8 | 500.0 (2022, once) |
| `nyc_30min_total` | ~980 | 25 | 70 / 15 / 9 / 25 | 25.0 |
| `nyc_10min_total` | ~490 | 25 | 154 / 21 / 22 / 48 | 25.0 |
| `li_30min_total` / `li_10min_total` | 396 / 120 | 25 | 4/3 · 0/0 · 0/0 · 0/0 | 25.0 |

The families that DO bind are the downstate locational pair whose **published** RCPF is
**$25/MW** — they cannot make a $300 hour by construction, and the model already reaches
their ceiling. The three statewide families that could ($750/$775) **never bind at all**,
in 35,040 hours across four years.

### 0.2 And they cannot be MADE to bind, because the model is not short in those hours

In the 101 hours NYISO's measured RT price exceeded $300 in 2022, the model's own fleet
(from the committed `class_hourly_2022.parquet`) sits far below its own annual maximum:

| class | year-max MW | **mean MW in the measured top-101 hours** | % of its own year-max |
|---|---|---|---|
| ST_GAS | 6,453 | 2,117 | **32.8 %** |
| CT_PEAKER | 2,533 | 1,273 | **50.2 %** |
| CC_REGULAR | 6,335 | 4,484 | 70.8 % |
| oil | 8,263 | 136 | **1.6 %** |
| import | 6,021 | 3,130 | 52.0 % |

**There is no MW shortage in the model in the hours the market priced scarcity.** A
reserve demand curve prices a shortage; with this much headroom no ORDC step, requirement
or shortage-pricing change can fire there. The lever is refuted on its own mechanism, not
on a residual.

### 0.3 The model and the market disagree about WHICH hours are tight

| | value |
|---|---|
| \|model top-101 ∩ measured top-101\| (by max zonal price) | **14 / 101** |
| \|model top-800 ∩ measured top-800\| | 296 / 800 |
| median model rank of the measured top-101 hours | **2,010 of 8,760** |

The market's scarcest hours are, to the model, ordinary mid-merit hours.

### 0.4 Every reserve-side cell is ALREADY adjudicated — DO-NOT-REDO holds

`docs/codebase-site/data/mechanism-matrix/NYISO.js`: `nyiso_spin_reserve_online` **I**,
`nyiso_east_reserve_families` **I**, `nyiso_synchronised_reserve` **G**,
`nyiso_incity_commitment_obligation` **R**, `nyiso_rcpf_postsolve_overlay` **G**,
`maxgen_emergency_tier_pricing` **I**. §0.1's census is new evidence, and what it says is
that these stay closed: `nyca_10min_spin` binds 0 h even in 2022, the year with 5× the
scarcity of any training year.

---

## 1. What phase 0 found INSTEAD — and it is a controlled experiment

Decomposing 2022's price gap (measured zone-mean RT $74.75 vs model $66.30 = **−$8.45**):

**By actual-price decile** — the entire gap is the top decile (**−$8.93** of −$8.45; the
lower nine deciles are net **+$0.48**).

**By month** — December **−$3.41**, February −$1.62, January −$1.41 of the annual mean.
Three winter months carry **76 %**.

**And then, inside December, the split that names the defect:**

| window | hours | measured $/MWh | model $/MWh | gap | contribution to the ANNUAL mean | measured >$300 h | model |
|---|---|---|---|---|---|---|---|
| **Dec 1–21** — days the Transco Z6 NY archive PRICES | 504 | 72.39 | 71.83 | **−0.55** | −0.03 | 27 | 0 |
| **Dec 22–31** — days the archive NEVER PRICED | 240 | 187.19 | 63.87 | **−123.32** | **−3.38** | 63 | 0 |
| ↳ Dec 23–26 (Winter Storm Elliott) | 96 | 366.40 | 68.57 | **−297.83** | **−3.26** | 61 | 0 |

**On the December hours it has gas prints, the model prices December to within
$0.55/MWh. On the 240 hours it does not, it misses by $123.32.** One 2.7 %-of-year window
carries **40 % of 2022's entire annual price gap**. That is as close to a controlled
experiment as phase 0 gets, and it identifies the defect as an **input**, not a missing
mechanism.

### 1.1 The missing prints are UNRECOVERABLE, and that is verified rather than assumed

`data/raw/gas-prices/transco_z6_ny_daily.csv` ends December 2022 at **2022-12-21**. The
source is the EIA Natural Gas Weekly Update archive, which **published no page between
2022-12-22 and 2023-01-12** — verified by HTTP 404 on `…/2022/12_29/` and `…/2023/01_05/`
and by the archive index itself (`…/12_22/` → 200, then nothing until `…/2023/01_12/`).
No substitute regional daily series in the repository covers those days
(`algonquin_citygate_daily.csv` is Wednesday-sampled and has the same gap; Henry Hub daily
is complete but **FELL** through Elliott, $7.15 → $3.52, so it cannot supply the level).

**So this arm does not repair the gap. It repairs HOW THE GAP IS FILLED.**

### 1.2 The gap is systematic, not a 2022 accident

Trailing December archive gaps, by year: 2018 **12 d**, 2019 **13 d**, 2022 **10 d**,
2023 **11 d**, 2024 **13 d** (2020/2021/2025 reach the 31st). Plus shorter June / July /
November gaps. **The fabricated days are systematically the coldest and most volatile of
the year, in six of eight archived years.**

---

## 2. THE ARM — `nyiso_hub_gap_month_level` (bool, default **False**)

`data/fuel/hubs.py::_nyiso_hub_daily_gas_prices` places each measured Transco Z6 NY print
on its true calendar day and `np.interp`s between them. **`np.interp` CLAMPS outside the
observed span**, so a calendar day the archive never priced inherits the *nearest print's
deviation from the month*. In December 2022 the last print is **$6.29** against a
December print-mean of **$7.32** — factor **0.859** — so the model asserts that the entire
Winter Storm Elliott window was **14 % cheaper than its own month**. The measured series
says nothing of the kind; it says nothing at all.

**Armed, an unpriced calendar day takes the month's own observed level (shape factor
1.0).** Strictly the weaker assertion.

- **Rules 14 `[R-ACCURATE]` + 13 `[R-MEASURED]`.** A reconciled reading of the real series
  beats a fabricated one; the construction is identical in a forecast year, so it
  regenerates from forward drivers and responds to changed conditions.
- **ZERO free parameters, zero new constants.** No number is introduced anywhere.
- **Exactly mean-preserving** — the `fbar` renormalisation is applied *after* the gate, so
  the monthly hub level, annual gas burn and fuel mix are untouched by construction. It
  moves **which** days are dear, never **how dear the month is**.
- **Default OFF**, dropped from the cache key at its `False` default
  (`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`), so every registered keeper in every ISO and
  every forecast is byte-identical and keeps its key. Verified: `cache_key()` moves only
  when armed.
- Registered in the SAME COMMIT as the field in `_CACHE_KEY_OPTIONAL_FIELDS`,
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` and `TIER_TAGS` (the nyiso-119 discipline), with
  its matrix row + a cell in all seven ISO shards (rule 28 `[R-MECH-MATRIX]` duty (c)).

### 2.1 Measured pre-solve footprint (ZERO LP — the rule-29 step-0 arithmetic)

Computed by calling the real seam with the flag off and on:

| year | annual mean hub $/MMBtu, off → on | hours moved | max \|Δ\| $/MMBtu | **Dec 22–31 mean, off → on** |
|---|---|---|---|---|
| 2022 | 8.4431 → **8.4431** (+0.00000) | 4,440 | 2.741 | 8.049 → **8.949** (+11.2 %) |
| 2023 | 3.3566 → **3.3566** (+0.00000) | 4,416 | 0.780 | 3.919 → **3.683** (−6.0 %) |
| 2024 | 2.7969 → **2.7969** (−0.00000) | 5,880 | 1.998 | 3.877 → **4.061** (+4.7 %) |
| 2025 | 5.5602 → **5.5602** (+0.00000) | 6,552 | 7.587 | 7.256 → 7.256 (no Dec gap) |

**Mean preservation holds to five decimal places in every year** — the identity the arm
asserts, checked before the solve.

**AND ITS PER-YEAR DIRECTION IS NOT SELECTABLE.** 2022's Elliott window goes **UP**,
2023's equivalent window goes **DOWN**, 2024's goes up, 2025's does not move. A fitted
mechanism does not move against the residual in one of the years it touches; a
construction repair does. This is the arm's own falsification test and it is registered
here, before the solve.

---

## 3. G-DRIFT — the code-level drift audit (rule 29(b); no control solve)

`git diff da2e7076 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
→ 8 files. Every hunk classified:

| file | classification | reason |
|---|---|---|
| `config/constants.py` | **INERT** | comment-only; zero non-comment changed lines |
| `config/scenarios.py` | **INERT** | adds `ercot_ep_gas_basis_receipts_fallback` only — default-off AND absent from the keeper's recipe AND another ISO's branch |
| `data/fuel/basis/ercot.py` | **INERT** | another ISO's branch, gated on that default-off flag |
| `config/solve_surface_declared.py` | **INERT to the LP** | read only by the cache-key fingerprint (`solve_surface.py:330`); re-keys, never re-solves differently |
| `scripts/lib/holdout_policy.py` | **INERT** | `[R-HOLDOUT]` removal — gates only, no solve path |
| `scripts/run_calibration.py` | **INERT** | ditto (CLI flag removal) |
| `scripts/run_calibration_full.py` | **INERT** | ditto (`enforce_holdout_year_gate` deleted) |
| `data/raw/_validation-source/actual_lmp.json` | **INERT for NYISO** | verified: the NYISO subtree is **byte-identical** to the keeper's; the +66 lines are ERCOT's 2021 `rt_lw` |

**All hunks INERT ⇒ G-CTRL form 4 is valid and the committed keeper IS the control. No
control solve is spent.**

---

## 4. SPAN — 2022–2025, one bundle. And why 2021/2020 are NOT in it.

`[R-HOLDOUT]` was removed 2026-09-09, so any year may now be solved, scored and registered
with no authorization. Under rule 16 `[R-ALLYEARS]` the keeper should therefore span every
year NYISO **can** score. It cannot score 2021 or 2020:

- **2021 — DATA-BLOCKED.** `data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_2021.csv`
  does not exist, and the keeper arms `nyiso_dynamic_reserve_requirements`. Disarming it
  to force 2021 would be a different config wearing the keeper's name.
- **2020 — DATA-BLOCKED** on a second input: `eia_generation_profiles.parquet` starts 2021.

(`docs/FINDING-nyiso-2020-touchpoint-data-blocked-2026-09-09.md` §7.) **The solvable span
is 2022–2025 and this bundle is all four years.** That is a change in itself: the keeper's
2022 currently lives as a *separately registered folded touchpoint*, not as a year of the
bundle.

**Honest statement of what these numbers are** (`[R-HOLDOUT]` coda): no year in this
program is protected from being iterated against any more, so **no number here is a
certified out-of-sample skill number**, 2022 included. They are model-SELECTION evidence.

---

## 5. SHARD PLAN (rule 32 `[R-SHARD]`) — the parent NEVER solves

Four independent per-year shards, one year each, own branch, own `--out-dir`, ≤ 20 min:

| shard | year | out-dir |
|---|---|---|
| `nyiso223-y2022` | 2022 | `results/calibration/nyiso223_gapfill_2022` |
| `nyiso223-y2023` | 2023 | `results/calibration/nyiso223_gapfill_2023` |
| `nyiso223-y2024` | 2024 | `results/calibration/nyiso223_gapfill_2024` |
| `nyiso223-y2025` | 2025 | `results/calibration/nyiso223_gapfill_2025` |

Each runs exactly:

```
uv run python scripts/replay_keeper.py results/calibration/nyiso_fuelvintage_A \
  --years <YEAR> --set nyiso_hub_gap_month_level=true \
  --out-dir results/calibration/nyiso223_gapfill_<YEAR> \
  --note "nyiso-223 hub-daily unpriced-day gap fill"
```

Shards report numbers in their final message and **push no bundle**; bundles are
gitignored the moment they are written (rule 31 `[R-RETAIN]` — gitignore, never `rm`).
The parent composes, scores and owns the single registration seam.

---

## 6. PRE-REGISTERED PREDICTIONS — distance to the threshold, not direction

Tolerances read from `scripts/calibration_verdict.py` FIRST: `PRICE_MEAN_TOL = 0.10`,
`PRICE_SHAPE_NRMSE_MAX = 0.20`, C3c band `[0.5×, 2×]` of actual,
`FORCED_SHARE_MERCHANT_MAX = 0.30` / `FORCED_SHARE_PEAKER_MAX = 0.15`.

Sizing: Dec 22–31 2022 gas +$0.90/MMBtu × ~7.5 MMBtu/MWh marginal CC ≈ **+$6.8/MWh on 240
hours** ⇒ **+$0.19/MWh equal-hour annual**, a little more load-weighted (winter hours).

### 6.1 The headline call — **THIS ARM DOES NOT CLOSE 2022**

| criterion | keeper | predicted arm | distance to threshold | **verdict call** |
|---|---|---|---|---|
| **C3a 2022** | −13.8 % | **−13.6 % to −13.2 %** | needs **+$3.09/MWh**; this buys **≈ +$0.20** | **STILL FAILS** ±10 % |
| **C3b 2022** | 0.242 | **0.238–0.244** | needs ≤ 0.20 | **STILL FAILS** |
| **C1 2022 `CC_REGULAR`** | +4.99 TWh / +3.8 pp | **+4.95 to +5.02 TWh** | needs ≤ +3.5 TWh | **STILL FAILS** |
| **C3c 2022** | 10 h vs 101 | **10–13 h** | band [50.5, 202] | **stays ledgered CAVEAT** |

I am registering a **failure** prediction on the target because the arithmetic says so.
The arm is run because it is **correct**, not because it closes a gate — rule 1
`[R-STRUCT]`, first half.

### 6.2 The training years — the real risk is a REGRESSION, and it is named in advance

The arm moves 2023's Dec 22–31 gas **DOWN** 6 %, i.e. against the residual.

| criterion | keeper 2023 / 2024 / 2025 | predicted | **verdict call** |
|---|---|---|---|
| **C3a** | +4.3 / +5.3 / −7.3 % | **+4.1…+4.4 / +5.2…+5.6 / −7.4…−7.1 %** | **PASS** — nearest limit 2025 at 2.6 pp of room |
| **C3b** | 0.122 / 0.179 / 0.160 | **0.121…0.126 / 0.177…0.184 / 0.158…0.163** | **PASS** — 2024 tightest, ≥ 0.016 of room |
| **C3c** | 2 / 0 / 3 h vs 10 / 13 / 42 | **unchanged 2 / 0 / 3** | **CAVEAT**, and I check the DISTANCE: 2024's model max is **$226.8** against a **$300** bar, so no gas move of this size can produce a 2024 hour. This is the nyiso-222 prediction defect, corrected. |
| **C1** | 14/14 in band | **unchanged in band**; \|Δ\| per class **< 0.05 TWh** | **PASS** — annual gas price is unchanged, so class energy cannot move materially |
| **C2** | PASS | **\|Δ\| < 0.05 TWh** | **PASS** |
| **C8** | ST_GAS 16.1 / 20.9 / 18.1 % | **± 0.5 pp** | **PASS**, cap 30 % |
| **C6** | PASS | `authorized_price_tuning` **NONE** — this is a structural lever, not the offer channel | **PASS** |
| **determination 2023–2025** | CALIBRATED, C3c lone ledgered caveat | **CALIBRATED, unchanged** | |

### 6.3 The falsification tests — what would show the arm is NOT what I claim

1. **Mean preservation.** Any class's annual energy moving > 0.10 TWh in any year
   falsifies "mean-preserving"; the pre-solve identity says annual gas is unchanged to
   5 dp, so the LP has nothing to re-allocate at the annual scale.
2. **Confinement.** Any hour OUTSIDE a month carrying an archive gap changing price by
   > $0.01 falsifies "it touches only unpriced days".
3. **Direction.** If 2023 improves on C3a, the arm is not doing what §2.1 says it does —
   2023's own gas move is **downward**.
4. **A PASS→FAIL flip on any load-bearing criterion** (C1/C2/C3a/C3b) is a STOP.

---

## 7. Governance

- **Rule 1 `[R-STRUCT]`** — structural mechanism; the authorized offer-curve channel is
  **NOT** used. `governance.authorized_price_tuning` = **NONE**
  (`scripts/gen_nyiso214_attestation.py` form).
- **Rule 21 `[R-DOF]`** — **ZERO new free parameters**; the DOF ledger is carried verbatim
  from the keeper.
- **Rule 24 `[R-REGISTRY]`** — the field is in `ScenarioConfig` and will appear in
  `run_config.json`; no env knob, no hardcoded dict, no fallback literal.
- **Rule 25 `[R-ISO-SCOPE]`** — the seam is NYISO's own daily-hub leg; every other ISO's
  cell is `.` and nothing transfers.
- **Rule 27 `[R-PUSH]`** — `scenarios.py` (20,436→20,470 lines) and `hubs.py`
  (1,379→1,406) were edited **in place with exact anchors**, never regenerated. A
  symbol-level `ast` diff vs HEAD confirms **zero** functions or constants removed, one
  field added. Blob verification follows the push.
- **Rule 28 `[R-MECH-MATRIX]`** — row added to the base file + a cell in **all seven**
  ISO shards, same PR; `check_mechanism_matrix.py` and its `--base origin/main` diff gate
  both exit 0.
- **Rule 29 `[R-SCREEN]`** — step 0 done and it KILLED the chartered arm (§0) and sized
  this one (§2.1). **No separate screen year is spent**: the mechanism's footprint is
  computable exactly with zero LP, its identity is checked pre-solve, and the solvable
  span is only four years each of which the arm touches.
- **Rules 31 / 32** — bundles gitignored not deleted, nothing removed before the owner
  rules, the promotion question asked explicitly in the final report; every solve in a
  shard, the parent solves nothing.

---

## 8. Disposition, stated in advance

This lane does **not** self-promote and does **not** withhold. On the registered
predictions the arm is a **zero-parameter correctness repair that changes no
determination**: it does not close 2022 and it should not move a training-year gate. Its
case is rules 14/13 and the §2.1 non-selectable direction; its cost is that it buys no
gate. **The call is the owner's**, under the standing formula.
