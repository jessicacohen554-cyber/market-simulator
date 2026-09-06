# RESULT — the 2023 HSL-withheld ceiling screen: G-3 and G-4 PASS, **G-5 FAILS, arm KILLED** (ercot-251)

> Scored against `docs/PRECOMMIT-ercot251-nohsl-ceiling-screen-2026-09-06.md`, committed before
> the solve. **Not registered** (rule 29(2)); bundle **deleted before merge** (rule 29(c)) —
> every number it produced is carried here. **2022 was not touched.** The screen may kill an
> arm and never promote one, and it did kill this one.

## 1. The gate board

| gate | threshold (pre-registered) | measured | verdict |
|---|---|---|---|
| **G-1** plumbing | no "no measured HSL potential … skipped" warning; ceilings arm | log reads `ercot_wtx_curtailment_driver: 2023 West/Panhandle VRE ceiling active (depth wind=0.1354 solar=0.1614, unpooled families, panhandle_owner=share)` | **PASS** |
| **G-2** confinement | multipliers exactly 1.0 outside West/Panhandle | verified pre-solve on the instrument | **PASS** |
| **G-3** ceiling recovers ≥ half the injection | renewable ≤ **144.836 TWh** | **141.797 TWh** (+1.941 vs the 139.856 actual) — **80.5 %** of the +9.960 injection recovered | **PASS** by 3.04 |
| **G-4** dispatch response | CC_REGULAR ≥ **136.761 TWh** | **144.238 TWh** — within **0.523 TWh** of the keeper's 144.761 | **PASS** |
| **G-5** no collateral flip | C2/C3a/C3b must not flip PASS→FAIL vs the keeper's 2023 | **C3a −17.85 %** (arm $39.73 vs RT actual $48.36) against the keeper's **−6.56 %** ($45.19) — outside the ±10 % band | **FAIL** |

Pre-registered rule: **all must pass; any FAIL is a STOP.** The arm is killed as configured.

## 2. What passed is genuinely informative

The mechanism does what its arithmetic says. The ceiling took back **8.02 of the 9.96 TWh** the
gross-up injected, and CC_REGULAR — the class whose 2022 miss started this — landed **0.52 TWh
from the keeper's measured-HSL value**, against a ±8.00 TWh band. Per-fuel hourly fit stayed
excellent (wind r 0.998 / NRMSE 0.042; solar r 0.998 / 0.077; gas r 0.992).

So on the **volume** question the repair works: a reference-rate gross-up with the ceilings
armed reproduces the measured-HSL dispatch almost exactly.

## 3. What failed, and why it is not an artifact

Mean LMP falls from the keeper's $45.19 to **$39.73** — from −6.6 % to **−17.9 %** against the
$48.36 RT actual, outside C3a's ±10 % band.

**Attribution (the check that matters, since G-5's reference is the drift-exposed keeper rather
than actuals).** Hour by hour against the keeper:

| hours | mean Δprice (arm − keeper) |
|---|---|
| renewables ≈ equal (\|Δ\| < 50 MW, n = 291) | **−$1.90** |
| top decile of renewable excess | **−$8.78** |
| all hours | −$5.18 |

Where the two runs' renewables agree the prices nearly agree; where the arm carries more
renewable the price gap triples. **The price loss tracks the construction under test, not
residual HEAD drift** — the ~$1.90 in the agreeing hours bounds drift and everything else. The
FAIL is real, and this attribution makes it stronger rather than weaker.

The mechanism is redistribution as much as level: the arm is above the keeper in **6,043** hours
and below in **2,708**, for a net of only +1.94 TWh. A 1.4 % energy excess costing 12 % of price
is the signature of that excess landing in already-soft hours and deepening the trough. The
solve's own `[7c]` operating-shape gate independently flagged 4 regressions vs the keeper
baseline (cf_emd CC_CHP / CC_REGULAR / COAL; r CT_CHP), consistent with the same reading.

## 4. What this means for the 2022 C1 miss — the trade, stated plainly

Arming this repair on a no-HSL year would likely **trade a C1 failure for a C3a failure**. The
2022 carve-out touchpoint sits at C3a **+0.0 %** with the full ±10 % band either side; a shift
of the size measured here (−11 pts) would put it outside. Meanwhile G-4 says CC_REGULAR would
very likely come back inside its band.

That is a real trade, and it is the owner's call, not the screen's. What the screen forecloses
is arming the repair **blind** on the assumption it was a free correctness win.

**Unchanged by this result:** the gate's premise is still false (FINDING §1–§2 rests on the code
and its own forecast leg, not on this screen), and the first-order fix is still the measured
2022 HSL archive — with which the bound is not a reference-rate approximation at all, no
gross-up happens, and neither this trade nor this repair arises.

## 5. STOP honored

The depths (`ercot_wtx_curtail_depth_wind/solar`) are frozen under rule 23 `[R-FROZEN-DERIVE]`
and were **not** re-run, re-tuned or swept to make G-5 pass — PRECOMMIT §5 forbids exactly that,
and it is what makes this a screen rather than a fit. One arm, one solve, one report.

**Screen state reverted** (PRECOMMIT §7): the withheld
`data/raw/ercot-hsl/ercot_2023_hsl_hourly.parquet` restored and verified byte-identical; the
predicate change in `scripts/run_calibration.py` **reverted** (the pre-registered default when
the owner has not admitted the repair on its merits); the bundle
`results/calibration/ercot251_screen_nohsl_ceiling/` deleted.

## 6. Open decision for the owner

Admit the provenance-predicate repair as a **correctness fix** despite the price cost, or leave
the gate as-is? Arguments both ways are now measured rather than assumed:

* **for** — the current predicate's stated premise is false, and it silently disables two real
  mechanisms on a grossed-up bound; the repair costs zero DOF and restores CC_REGULAR to within
  0.5 TWh of the measured-HSL result;
* **against** — on the only years it is live (all held out), it moves mean price ~12 % low,
  which on 2022 would break a criterion that currently passes.

A third option the screen supports: admit the repair **and** treat the price consequence as the
next object — the residual excess is a *shape* problem in soft hours, which is where the ERCOT
C3c/ORDC price-function work already lives.
