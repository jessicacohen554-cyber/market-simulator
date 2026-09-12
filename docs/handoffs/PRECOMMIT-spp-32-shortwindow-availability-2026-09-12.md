# PRECOMMIT — SPP-32: the measured sub-5-day unit-availability family, armed for SPP.

**Lane** SPP-32 · **Base** `9e499b0e8d6f851a4e726bbd42b207ca5368654c` · **Keeper / control**
`2026-09-10-spp-27-commitment-grain`, bundle `results/calibration/spp27_span` (COMMITTED; read and
differenced, **never re-solved** — rule 29(b) form 4) · **Predecessor** `PLAN-spp-31-complete-frontier-2026-09-12.md`
· **Parent LP: ZERO** (rule 32 `[R-SHARD]` (a)). Every gate, prediction and screen year below is
**sealed here before any solve**.

---

## 0. WHAT THIS ARM IS, AND WHAT IT IS NOT

**IS:** rule 14 `[R-ACCURATE]`. SPP's LP currently ignores every sub-5-day unit outage in its own
CAMPD record. Two committed measured extracts exist or are landed with this commit and neither is
read by SPP's keeper.

**IS NOT a C3c arm.** `FINDING-spp-29-c3c-price-tail-2026-09-11.md` closed that route and §4 below
records, before the solve, that this family **cannot** close SPP's price tail. **No gate here reads
C3c, and a C3c movement in either direction is not evidence for or against this arm.**

**Rule 28 `[R-MECH-MATRIX]`:** `unit_outage_short_windows` and `unit_outage_short_windows_gas` are
both **`U` (UNTESTED)** in SPP's shard, so this is a first test, not a re-test (28(a) honoured).
Rule 28(d): PJM's and MISO's `K` and NEISO's `R` fill **no** SPP cell — the extract below is derived
from **SPP's own CAMPD record**, and no other ISO's number crosses.

---

## 1. PHASE 0 — the census, at ZERO LP

### 1a. The coal extract already exists and is unarmed

`data/raw/campd-unit-outages-short-SPP.csv` — **620 windows, 24 plants, 39 units, 620 of 620 rows
`plant_group == COAL`**, derived by `scripts/data/derive_campd_unit_outages.py --short-windows`
(committed sidecar). SPP's keeper carries `unit_outage_short_windows = False`.

### 1b. The gas extract did NOT exist; it is derived and committed with this PRECOMMIT

`data/raw/campd-unit-outages-shortgas-SPP.csv` — **2,838 windows, 39 plants, 75 units**
(CC_REGULAR 2,204 · ST_GAS 608 · CC_CHP 26), from
`derive_campd_unit_outages.py --iso SPP --years 2023 2024 2025 --short-windows
--short-window-groups gas --merit-order-guard`.

**ZERO PARAMETERS WERE CHOSEN BY THIS LANE** (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`). The recorded
invocation is **byte-identical to PJM's committed sidecar on every knob** — `fullstop_override_cf`
0.02, `fullstop_override_days` 5, `high_load_pctl` 0.85, `min_inmerit_hours` 6, `min_outage_days`
1.0, `merit_order_guard` true, everything else false — differing only in `iso` and `years`. Nothing
was swept, and no value was selected against any criterion.

**Rule 23 `[R-FROZEN-DERIVE]` is not engaged**: this is a NEW artifact for an ISO that had none, not
a re-derivation of an existing one. The coal extract was **not** re-derived and is byte-unchanged.

### 1c. Footprint by year — the rule 29 `[R-SCREEN]` (1) screen-year statistic

Removed capacity-hours = `unit_capacity_mw × duration_days × 24`.

| start year | coal windows | coal GWh | gas windows | gas GWh | **total windows** | **total GWh** |
|---|---|---|---|---|---|---|
| 2023 | 163 | 5,174.373 | 935 | 10,762.570 | 1,098 | 15,936.944 |
| 2024 | 211 | 6,446.563 | 840 | 9,297.096 | 1,051 | 15,743.659 |
| **2025** | **246** | **7,050.714** | **1,063** | **11,354.227** | **1,309** | **18,404.941** |

> ### **SCREEN YEAR = 2025, NAMED HERE BEFORE THE SCREEN RUNS.**
> It is the year the mechanism's **own measured footprint is largest** — on window count and on
> removed capacity-hours, in the coal scope, the gas scope and the total, i.e. on **every** basis.
> It is **not** the year of the largest residual (rule 29 `[R-SCREEN]` (1)). Had the bases
> disagreed, the tie-break declared here would have been total removed GWh.

---

## 2. THE ARMS

Nested by construction and verified in the code: `data/fleet/arrays.py:1338` opens the whole
short-window block on `unit_outage_short_windows`, and `:1363` passes `gas_scope` **inside** it — so
the gas flag is inert unless the coal flag is on. Two arms, screened separately so the gas increment
is attributable (rule 19 `[R-ONE-MECH]`):

| arm | config delta against the keeper | out-dir | branch |
|---|---|---|---|
| **A** | `unit_outage_short_windows=True` | `results/calibration/spp32_A_2025/` | `claude/spp32-A-2025` |
| **B** | `unit_outage_short_windows=True` **and** `unit_outage_short_windows_gas=True` | `results/calibration/spp32_B_2025/` | `claude/spp32-B-2025` |

**Rule 19 `[R-ONE-MECH]` enumeration.** What else touches SPP availability: the ≥ 5-day CAMPD
unit-outage overlay (`outage_source = "historic"`, already on) — **disjoint by DURATION**, windows
here are < 5 days by construction; the wind EFOR haircut `wefor_multiplier` 0.7 — a different
technology; the per-plant must-run floors (mechanism-16) — a floor, not a ceiling, and it acts on
`pmin`, not `availability`. Coal and gas scopes are **disjoint by plant group** (`COAL` vs
`{CC_REGULAR, CC_CHP, ST_GAS, ST_CHP}`). Nothing is counted twice; this **widens a discard**.

**Rule 13 `[R-MEASURED]` forward story.** A unit's forced-outage / dead-span window is a physical
availability event, and the detector regenerates for any vintage from CAMPD's own hourly record —
the admissibility test rule 13 sets. It is registered in `_BACKCAST_ONLY_OVERLAY_FIELDS` as a
backcast overlay, exactly as PJM and MISO carry it on their keepers.

**Rule 21 `[R-DOF]` effect: ZERO free parameters added.** No threshold, share, multiplier or level.
SPP's ledger stays **n_entries 3 / n_residual 2**. The two fields are booleans registered in
`_CACHE_KEY_OPTIONAL_FIELDS` at their `False` defaults, so no other ISO's cache key moves
(rule 25 `[R-ISO-SCOPE]`).

**Rule 1 `[R-STRUCT]`:** `offer_curve_by_group` stays at the keeper's uniform 0.93, byte-identical.
Not re-cut, not swept, not examined against any gate.

---

## 3. G-DRIFT — the code-level drift audit, so form 4 stands and NO CONTROL SOLVE IS SPENT

`git diff 09d9fc00ea6a9f39eafdf444a6ff8a64d3b515f8 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
(`09d9fc00…` is keeper 9's recorded `basis_sha`) returns **six files, 408 insertions**. Every hunk
classified, with its reason:

| file | change | verdict | reason |
|---|---|---|---|
| `config/scenarios.py` | +`unit_outage_short_windows_gas`, +`mustrun_chp_btm_holdout` | **INERT** | both `bool = False`; both registered in `_CACHE_KEY_OPTIONAL_FIELDS` **and** `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"False"` in the same commit, so every pre-existing SPP key is byte-stable; both absent from the keeper's recorded config |
| `data/fleet/arrays.py` | gas-scope pass-through | **INERT** | `getattr(config, "unit_outage_short_windows_gas", False)`, and the enclosing block at `:1338` is itself off in the keeper |
| `data/outages.py` | gas extract reader | **INERT** | reached only when `gas_scope=True`; and `campd-unit-outages-shortgas-SPP.csv` did not exist at the keeper's solve |
| `scripts/run_calibration_full.py` | `mustrun_chp_btm_holdout` plumbing | **INERT** | default `False` at every call site; the body is behind `if mustrun_chp_btm_holdout:` |
| `scripts/run_calibration.py` | gas-flag solve-path override | **INERT** | guarded `if unit_outage_short_windows_gas is not None:`, default `None` |
| `model/lp/model.py` | move `np.asarray(mc, float32)` before `h.run()`; `del cost`, `del mc` | **INERT** | HiGHS has already copied the cost vector into its own `colCost_` when `changeColsCost` returns; nothing mutates `mc` between the old and new evaluation points; the float64→float32 `asarray` still copies, so the result's no-aliasing guarantee holds. **This is the ONE hunk whose inertness rests on code reading rather than on a default-off gate, and it is named as such rather than buried.** |

**ALL HUNKS INERT ⇒ rule 29(b) form 4 is VALID: keeper 9's committed bundle is the control and NO
CONTROL SOLVE IS SPENT.**

---

## 4. WHAT THIS ARM WILL NOT DO — stated before the solve, so it cannot be claimed afterwards

In 2024's 35 DA-tail hours (33 of them **14–17 January 2024**, Winter Storm Heather), the two
extracts overlap the tail as follows:

| scope | windows overlapping the tail | MW-h removed | mean MW removed per tail hour |
|---|---|---|---|
| coal | 5 | 6,019 | **172.0** |
| gas | 19 | 13,498 | **385.7** |
| **total** | **24** | **19,517** | **557.6** |

Against the **median 8,233 MW** the model holds above its \$74.80 marginal unit in those hours
(`FINDING-spp-29` §5), that is **6.8 %**. **Card R-bf's availability route is therefore ANSWERED
NEGATIVE for this mechanism family, at zero LP, and the arms below are NOT chartered against it.**
This is recorded as a phase-0 measurement, not as a reason to skip the arm: the arm's basis is rule
14, not the tail.

---

## 5. THE SCREEN GATES — STRUCTURAL, PRE-REGISTERED, STOP-ONLY

Rule 29 `[R-SCREEN]`: these may **kill** an arm; they may **never promote** one; none reads the
target residual; none reads C3c. Scored on the 2025 screen year against the keeper's committed 2025.

**Keeper 2025 baseline (P1), re-derived this session from the committed sidecars** —
COAL_PRB 80.4149 · CC_REGULAR 34.9097 · CT_PEAKER 14.2422 · ST_GAS 12.0198 · COAL_LIGNITE 6.7981 ·
CC_CHP 1.9343 · wind 122.0210 · nuclear 15.7804 · hydro 8.8204 · solar 2.3244 TWh; demand 301.8402
TWh; **slack 0.0000 MWh, dump 0.0000 MWh**; load-weighted mean price \$28.7893; max zonal dual
\$73.7731; hours > \$200 = **0**.

- **G1 — DIRECTION.** Arm A: COAL_PRB + COAL_LIGNITE generation **falls** (> 0 TWh). Arm B: the
  above **and** CC_REGULAR + ST_GAS + CC_CHP together fall relative to arm A. *An arm whose own
  target classes do not move is INERT and is killed here.*
- **G2 — CONFINEMENT.** Arm A moves **no** gas-class availability (the extract is 620/620 COAL);
  arm B moves **no** CT_PEAKER availability (the derive skips CT_PEAKER by convention) and no
  wind / solar / hydro / nuclear availability in either arm. *Movement outside the extract's own
  plant groups is a plumbing defect and kills the arm.*
- **G3 — MAGNITUDE BOUND.** The fossil generation drop is **> 0** and **below** the removed
  availability priced at the class's own model capacity factor:
  arm A ≤ 7,050.714 GWh × 0.547 ≈ **3.86 TWh**; arm B ≤ that plus 11,354.227 GWh × 0.491 ≈
  **9.4 TWh** in total. *A response above the bound means the overlay is being applied to more
  capacity than the extract names.*
- **G4 — IDENTITY.** Energy conserved: demand unchanged to ≤ 0.01 TWh, `dump` stays **0.0000 MWh**,
  and `slack` stays **0.0000 MWh**. *Slack appearing means the overlay has removed capacity the
  system needed — a real adequacy signal, and it must be reported, not absorbed.*
- **G5 — NO NON-TARGET REGRESSION (stop only).** No load-bearing criterion (C1 free classes, C2,
  C3a, C3b) flips **PASS → FAIL** on 2025. **C3c is explicitly excluded from this gate in both
  directions** (§4). *A flip kills the arm; the absence of a flip promotes nothing.*

**An arm clearing all five earns the full span** `--year 2023 2024 2025` as ONE bundle
(rule 16 `[R-ALLYEARS]`), three shards, one year each. **An arm that fails any gate is reported as
this lane's result and its remaining years are never spent.**

---

## 6. SHARDS — rule 32 `[R-SHARD]`

Two screen shards, launched together (rule 12: separate invocations run concurrently; two is inside
the cap). Each: **one year, ≈ 166 s of LP** (keeper 9's measured 499 s / 3 years,
`SHARDREPORT-spp27-span.md:24`), comfortably inside the 20-minute commit ceiling with a cold
clone + hydrate.

- `source_revision` = the **full 40-character SHA of this PRECOMMIT's commit**, pinned in each
  shard prompt, with `git rev-parse HEAD` equality as the shard's first hard stop. Never a branch.
- `DATA PROFILE: spp`.
- Each shard owns its `--out-dir` and its branch, commits **only** its own bundle path, and is
  forbidden by name from `git add -A`/`git add .`, `dashboard_add_run.py`, `build_manifest.py`,
  `build_status.py`, `prune_iso_runs.py`, anything under `frontend/data/backcast/**`, any edit under
  `src/` or `scripts/`, opening a PR, and deleting any result.
- Hard stop on config signature: the shard must observe `offer_curve_by_group` uniform **0.93**,
  `mustrun_window_commitment_grain = True`, and its own arm's flags — **and nothing else changed**.
- **The parent owns the seam**: composition, scoring, the gate table, the matrix cell and the
  promotion question all happen once, here, after the shards land.

---

## 7. WHAT WOULD MAKE THIS LANE REPORT AGAINST ITSELF

Named now so it cannot be rationalised later: **if arm B's response exceeds G3's bound, or slack
appears under G4, the honest reading is that 2,838 gas windows over three years is too many for a
merit-order guard to have filtered** — SPP's CC fleet runs at ~49 % CF, and a 1–5 day dead span at
that CF can be economics rather than an outage. In that case the arm is killed and the finding is
that the gas detector's identification does not transfer to SPP's fleet conduct, whatever it does in
PJM. That would be a genuine rule-28(d) result and it will be reported as one.

## 8. GOVERNANCE

- Rule 31 `[R-RETAIN]`: nothing deleted. The screen bundles are gitignored on the shards and their
  numbers are carried into this document's successor RESULT, which is the record.
- Rule 15 `[R-DASHBOARD]`: a screen bundle is **never** registered. Only a full span that clears the
  gates is a candidate, and promotion remains the owner's act.
- `[R-HOLDOUT]` removed 2026-09-09: no year is protected, and no number this lane produces is a
  certified out-of-sample skill claim.
- **No `complete` or `frontier` declaration is added, requested or implied by this lane.**
