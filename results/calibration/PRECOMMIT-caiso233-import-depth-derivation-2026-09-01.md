# PRECOMMIT — caiso-233: deriving the four ungrounded CAISO import SPOT depths

**Registered 2026-09-01, session caiso-233. Branch
`claude/caiso-import-capacity-derivation-0e5j0q`, cut fresh from `origin/main`
(`c904b1d6`).**

Keeper at entry: **`2026-09-01-caiso-231-b1-ungrounded`**, determination
**NOT-YET**, C3a the SOLE load-bearing FAIL. CAISO holds **no `complete` and no
`final` marker**; the holdout freeze is **ACTIVE**. Every read in this session
stays inside **2023–2025**.

---

## §1 — THE OBJECT (and a correction to the charter's enumeration)

The charter names "the four `IMPORT_TRANCHES["CAISO"]` SPOT CAPACITIES … 8,805 MW
… invariant across all three years". The **set** is right and the **criterion**
is right; the **enumeration** in the charter is off by one rung, and this
document targets the set the criterion actually selects:

| rung | MW | limb | year-varying? |
|---|--:|---|---|
| `PNW_hydro_base` | 1,072 / 1,558 / 1,566 | **FIRM** — MEASURED (DMM RA × MIC north share) | yes |
| `DSW_solar_PV` | 1,251 / 1,813 / 1,805 | **FIRM** — MEASURED (DMM RA × MIC south share) | yes |
| **`PNW_midC`** | **1,800** | **SPOT — ungrounded** | no |
| **`DSW_CCGT`** | **1,800** | **SPOT — ungrounded** | no |
| **`DSW_CT`** | **2,200** | **SPOT — ungrounded** | no |
| **`WECC_scarcity`** | **3,000** | **SPOT — ungrounded** | no |
| | **= 8,800 MW** | | |

`DSW_solar_PV` is the DSW **firm** block — it is MIC-measured, per-year, and
`caiso.CAISO_FIRM_IMPORT_TRANCHES` contains it — so it fails the charter's own
"invariant" test and is **already closed**. The invariant, uncited rung the
charter omitted is **`PNW_midC` 1,800 MW**. The corrected total is **8,800 MW**,
which is also the figure the caiso-191 desk adjudication used, and the set
`{n for n,_,_ in static if n not in firm}` that
`scripts/probes/_caiso186os_dof_repair.py` itself labels
`RESIDUAL (static, no cited primary source)`.

Re-opening a MEASURED rung to move a residual would be a rule-1 `[R-STRUCT]`
violation, so `PNW_hydro_base` and `DSW_solar_PV` are **held fixed** throughout.

## §2 — METHOD (the peer-ISO port, fixed before execution)

`scripts/data/derive_caiso_import_depths.py` — the capacity-limb companion to
`derive_caiso_import_tranches.py` (prices only, by its own docstring). Ported
from `derive_neiso_import_tranches.py`, the sibling that closed this same
G-26 / audit C-6 gap:

    routine_depth(corridor) = p98( measured corridor net import )     [CAP_PCTL]
    spot_depth(corridor)    = routine_depth(corridor) − firm(corridor)
    scarcity                = p99.9( measured TOTAL ) − Σ routine     [SCARCITY_PCTL]

with the firm block carved out of its corridor's p98 exactly as NEISO carves
Highgate's published converter rating out of the HQ seam p98, and the DSW spot
remainder split into `DSW_CCGT` / `DSW_CT` as **equal blocks** (the NEISO
`NYISO_CT_base`/`_peak` and NYISO equal-MW rung convention — **zero free
parameters**; the split point is fixed by convention, not chosen).

Inputs, both already on disk and already wired: `corridor_net_import` and
`CAISO_CORRIDOR_DIBA` imported from `derive_caiso_import_tranches.py` (not
re-implemented), over
`data/raw/eia-930-interchange/CISO interchange hourly.parquet`.

## §3 — PRE-REGISTERED HONESTY GATES

Held to the **SAME bar the PRICE limb was held to and failed** — the constants
are `derive_caiso_import_tranches.py`'s own `CV_MAX` / `LOYO_MAX`, copied from a
file already on `main`, so the bar is **not settable by this session**:

* **G-STABILITY** — each derived rung's coefficient of variation across
  2023–2025 ≤ **0.20**.
* **G-LOYO** — derive on two years, predict the held-out year; worst held-out
  relative depth error ≤ **0.25**.

**STOP CONDITION (pre-registered).** If either gate fails, **file the FINDING and
do NOT solve.** Do not soften a threshold, do not re-scope the gated rung set to
whichever subset passes, and do not fall back to a residual-tuned depth. A failed
gate honestly reported is the correct outcome; manufacturing a pass is a rule-13
`[R-MEASURED]` act.

**Ordering, stated plainly.** The gate thresholds were fixed in the script before
it was executed; the derivation and both gates run at the **estimation stage**,
before any LP, exactly as `derive_caiso_import_tranches.py` is designed to
("If either gate fails the script prints FAIL and the caller files the FINDING and
does NOT solve. No LP is run here."). This document is the pre-registration of the
**solve** — which the stop condition may prevent from ever being reached.

## §4 — PRE-REGISTERED SOLVE DESIGN (reached only on a gate PASS)

* **A0 control** — `--replay-bundle results/calibration/caiso231_b1_ungrounded`
  at HEAD, isolating the delta from HEAD drift.
* **B1 treatment** — the same, plus the derived depths as the **only** delta.
* `--year 2023 2024 2025` in **one invocation, years sequential** (rules 12/16);
  the two invocations launched concurrently (rule 12's cap of 2 for CAISO's
  per-plant multi-zone LP). Scored on **P1**.

## §5 — PRE-REGISTERED C3a DIRECTION AND MAGNITUDE

Baseline, re-verified at HEAD from committed artifacts
(`calibration_verdict.py --run-id 2026-09-01-caiso-231-b1-ungrounded`):
**2023 +4.1 % (pass) / 2024 +12.5 % FAIL / 2025 +15.6 % FAIL.**

* **DIRECTION (the falsifiable claim): NEGATIVE in all three years.** The derived
  ladder is *shallower* than the incumbent, so B1 removes economic import depth;
  FINDING-caiso232 §D measures corr(monthly residual, model import volume) =
  **+0.419**, so less import volume must move λ **down**.
* **MAGNITUDE: small — |ΔC3a| ≤ 3 pp per year.** FINDING-caiso202 §C attributes
  **<5 %** of the C3a positive gap directly to the import legs on the per-hub-priced
  keeper, so a depth change of this size cannot close C3a and is **not expected
  to**. A larger move than this would itself be evidence the mechanism is acting
  through something other than the declared channel and must be diagnosed, not
  banked.
* **This is a DOF-closure lane, not a residual lane.** Per rule 1 `[R-STRUCT]` and
  the owner's standing standard — *"If structural integrity improves but gates
  regress that may still be a keeper"* — the derivation is **never** weighed
  against the price residual. A C3a regression does not veto a grounded depth,
  and a C3a improvement does not license an ungrounded one.

## §6 — OUTCOME (recorded 2026-09-01, same session)

**THE STOP CONDITION FIRED.** Both pre-registered gates FAILED:
year-stability FAIL (`PNW_midC` CV 0.253, `WECC_scarcity` CV 0.550 against the
0.20 bar) and LOYO FAIL (worst held-out error 40.1 % / 491.7 % / 57.9 % against
the 0.25 bar). **No LP was built and no solver was called.** §4's arms were never
run, so there is nothing to register (rule 15 applies to completed runs — the
caiso-134/140/150/202/232 disposition). The bar was not moved and the gated rung
set was not re-scoped.

Full result, the failure decomposition, and what the exercise *did* establish:
`FINDING-caiso233-import-depth-derivation-2026-09-01.md`.
