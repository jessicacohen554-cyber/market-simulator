# FFR-3C — Attributing the D-1/D-2 capacity-adequacy collapse: the MISO control arm and the G-31 screen-grain term

**Session.** FFR Wave 3, the attribution lane (owner blocker 0 from FFR-3A;
`docs/handoffs/ffr-owner-sitting-2026-08-02.md` Addendum D.1/D.2 — *"HOLD PROMOTION, FIND
ROOT CAUSE"*). Branch `claude/ffr-3c-collapse-attribution-pebd3t`, off `origin/main`
**`5057614`** (the packet's stated HEAD `195ff18` was already four merges stale at session
start).

**The deliverable is ATTRIBUTION, NOT A SMALLER NUMBER.** No `ScenarioConfig` default was
changed, no damper unarmed, no band widened, no parameter tuned, nothing promoted or
registered. Both signed mechanisms stay armed exactly as the owner left them.

---

## 0. One-line answer to the owner's question

**(c) — both, with a measured split, and the split is between MEMBERSHIP and CALENDAR.**

*Which* units the screen retires is real going-forward economics and the corrected rule gets
it more right than the rule it replaced. *When* they leave is a grain artifact: the model
concentrates a whole fleet-cohort's exit into a single year at **2.8×–4.8× the largest
single-year thermal deactivation any of these ISOs has ever recorded**, while the entry side
— by the same owner decision — is capped at **2× its own measured record**. The reserve-margin
trough is the integral of that asymmetry. §3 and §4 carry the measurements; §5 states plainly
what this evidence does **not** separate.

---

## 1. The G-31 screen-grain term — characterized

Addendum A.4 isolated G-31 as an *independent* root-cause term on the observation that the
single-year lumping **survives** the rule change even though `pipeline` removes the
consecutive-loss counters outright. This section answers the three questions the charter
asked: what grain the screen decides on, why lumping survives, and whether the magnitude is
artifact or economics.

### 1.1 What grain does the economic screen actually decide on?

Three grains, all of them coarse, and only the first is the one people mean by "the rule":

| grain | what it is | where |
|---|---|---|
| **Decision** | ONE annual screen on ONE year's dispatch. Decision persistence **D = 0** — a unit is DECIDED at the *first* failing screen. Explicitly "an OPEN DOF held by parsimony — the flat-expectation degenerate NPV form". | `retirements.py:1201`, `scenarios.py:1373` |
| **Execution** | `decided_year + L_f`, where `L_f` is a per-**fuel** CONSTANT (coal 3, gas_ct 2, gas_cc/gas_st/oil 1, nuclear 3). | `retirements.py:1220`, `_execution_lag_years` |
| **Admission cap** | NOT a rate cap. `_apply_reliability_floor` over the *scheduled* exit set, evaluated at the **decision year's** peak and the **decision year's** fleet. | `retirements.py:1301` |

### 1.2 Why does the lumping survive a rule that deleted the counters?

**Because the counters were never a spreading mechanism — they were a delay mechanism, and so
is their replacement.** Deleting one delay and installing a different delay changes the
*offset* of the exit wave, not its *width*.

Neither rule contains any unit-specific dispersion source. Both are deterministic functions of
"did this unit fail the identical bar this year?" plus a per-fuel constant:

* **legacy** (`retirements.py:1834-1846`) — `loss_years[uid] += 1` on a failing year, reset to
  0 on a profitable one; eligible at `>= retirement_years_<fuel>`. Units sharing one price path
  advance their counters in **lockstep** and cross the threshold in the **same** year.
* **pipeline** (`retirements.py:1273-1322`) — D = 0, so they do not even stagger by the
  counter; they are all decided in the failing year itself, then all executed exactly `L_f`
  later.

**Measured, synthetically, with no LP.** Driving `_apply_pipeline_retirements` directly over a
12-unit / 6 GW MISO coal cohort whose units all fail the same bar
(`scratchpad/g31_grain_demo.py`):

| year | decided | executed | model requirement |
|---|--:|--:|--:|
| 2026 | **12** | 0 | 21,990 MW |
| 2027 | 0 | 0 | 23,090 MW |
| 2028 | 0 | **12** | 24,244 MW |
| 2029–33 | 0 | 0 | … |

Three properties fall straight out:

* **G1 — decision grain.** All 12 decided in one year. Width = 1 yr.
* **G2 — execution grain.** All 12 executed in one year, 3 years later. **The lag TRANSLATED
  the wave; it did not SPREAD it.** Width still = 1 yr. A per-fuel constant lag is a rigid
  time-shift operator — it cannot map a one-year failure event onto a multi-year exit schedule,
  which is exactly what "spreading" would require.
* **G3 — cap grain.** The admission cap tested the **2026** requirement (21,990 MW); the exits
  it admitted landed against the **2028** requirement (24,244 MW) — **+10.3 %** of requirement
  that the cap never saw. The cap is evaluated on a counterfactual instant that never occurs:
  the decision year's fleet with the whole schedule's exits removed at once.

### 1.3 The specific step where de-lumping capability was removed

**`staged_oversupply_thinning` + `staged_thinning_max_gw_per_year` were DELETED at the FF-1A
R-NEW flip commit** (owner D2; `scenarios.py:1345-1349`, rule 26 `[R-DELETE]` — deleted, not
zeroed, and correctly so). That mechanism was a **3 GW/fuel/yr throughput cap**, and it is the
only component the model has ever had that spread an exit wave. G-31's own originating report
measured it cutting ERCOT's coal false-retire **13.96 → 6.47 GW (−54 %)**
(`docs/hindcast-reports/ercot-g31-staged-thinning-limited-foresight-2026-07-08.md`).

The stated reason for deleting it (redesign §3.3, RC-0B §a.6) is rule 19 `[R-ONE-MECH]`: *"the
execution-lag pipeline already carries the deactivation queue; a throughput/rate cap on top
would double-count it."*

**That argument conflates two distinct properties of a queue.** A queue has a *latency* and a
*throughput*. The execution lag `L_f` models the latency — how long after the decision a unit
leaves. It says nothing about how many MW can leave per year. `staged_oversupply_thinning`
modelled the throughput. Deleting it did not remove a double-count; it removed the **only**
model of queue throughput and left the latency model standing alone. G2 above is the direct
demonstration: with only the latency term, wave width is invariant.

The redesign memo itself names the identification source a throughput cap *would* need —
*"max observed single-year per-ISO thermal deactivation from the EIA-860 retired sheet —
measurable"* — and then declines to arm one. §1.4 measures it, so the next decision on this is
evidenced rather than argued.

### 1.4 Is the magnitude consistent with a grain artifact or with real economics?

**Measured single-year thermal deactivation, EIA-860 retired sheet (`Status == RE`), 2015–2025,
BA→ISO on the same crosswalk the fleet loaders use** (`scratchpad/measure_exit_throughput.py`):

| ISO | max single yr (GW) | year | median (GW) | max coal yr (GW) |
|---|--:|--:|--:|--:|
| MISO | **7.57** | 2016 | 3.54 | 4.20 |
| PJM | **5.24** | 2015 | 1.32 | 4.62 |
| ERCOT | **4.42** | 2018 | 0.39 | 4.42 |
| CAISO | **1.48** | 2016 | 0.05 | 0.00 |
| NEISO | 0.45 | 2021 | 0.02 | 0.40 |
| NYISO | 0.31 | 2021 | 0.03 | 0.00 |

Against what the model actually does in a single year (FFR-2B §4 / FH-1 §3.3, T1-H arms):

| leg | model single-yr exit | ISO's largest EVER | ratio |
|---|--:|--:|--:|
| MISO `pipeline` coal wave, 2024 | ~11.9 GW | 4.20 GW (coal) / 7.57 GW (all thermal) | **2.8× / 1.6×** |
| PJM `pipeline` coal wave, 2024 | ~14.8 GW | 4.62 GW (coal) / 5.24 GW (all thermal) | **3.2× / 2.8×** |
| ERCOT T1-FF base 2023, in 2025 | 21.05 GW (26.8 % of prior thermal) | 4.42 GW | **4.8×** |

**And the asymmetry, which is the finding.** The same owner sitting that armed D-2 capped the
ENTRY side at a measured envelope and left the EXIT side with no envelope at all:

| side | discipline | MISO cap |
|---|---|--:|
| **Entry** (`entry_rate_limits`, D-2, ARMED) | `ENTRY_GROWTH_LIMIT_MULTIPLE = 2.0` × measured 10-yr max annual build, per tech | gas_cc 1.723 → **3.45 GW/yr**; gas_ct 0.675 → **1.35 GW/yr** |
| **Exit** (`retirement_rule=pipeline`, D-1, ARMED) | none — no rate cap exists after the R-NEW deletion | **unbounded** |

So a MISO year may retire an unlimited quantity of thermal capacity and replace at most
~4.8 GW/yr of dispatchable thermal. **Exit throughput is uncapped; replacement throughput is
capped at 2× the historical record.** That is the collapse mechanism stated in one line, and
neither half of it was measured against the other before both were armed.

**Read carefully — this does NOT say the exits are wrong.** A forecast year may legitimately
exceed the historical envelope: the coal fleet is genuinely aging out and real retirements do
cluster. What the comparison establishes is narrower and sufficient: the model's single-year
exit volume sits **1.6×–4.8× outside the observed envelope while the entry side is held to
2× its own**, and nothing in the configuration reconciles the two. The *level* of exits is
adjudicated by the revenue lane (BLK-6/BLK-9); the *calendar* is G-31's, and the calendar is
what the reserve-margin trough is made of.

---

## 2. Two instrument defects found while attributing (neither is the collapse)

Reported because they change how the FFR-3A numbers should be read, not because they explain
them. Both are measured, no-LP.

### 2.1 ERCOT's I12 band is on a different basis from the floor the model enforces

`resolve_adequacy_requirement_mw` nets each ISO's demand-response capacity out of the gross
peak before applying the PRM. For ERCOT that netting **is ERCOT's own published construction**
(the CDR's "Firm Peak Load"; 5,520 MW of Load Resources/ERS/load management ÷ 95,419 MW gross
seasonal peak = 5.8 %, Dec-2025 CDR Seasonal Summary — `capacity_market.py:2034`).

The ledger's `reserve_margin` is `accredited_firm_mw / GROSS peak − 1` (`runner.py:2641`,
`peak_demand` = `year_demand.sum(axis=0).max()`, `runner.py:942`). So:

| quantity | ERCOT value |
|---|--:|
| Margin at which the **model's own retirement floor** is satisfied | **+7.15 %** |
| Margin I12 scores ERCOT against (scalar `planning_reserve_margin`) | **+13.80 %** |
| **Basis gap** | **6.65 pp** |

ERCOT is the **only** ISO affected: I12's scalar-floor branch fires only for energy-only ISOs
(`MARKET_DESIGN`), and ERCOT is the only one. Every capacity-market ISO is scored on the
requirement-implied floor — which is the model's own basis. Cross-check: the packet's quoted
MISO band `[10.0 %, 25.0 %]` reproduces exactly as the model-implied 9.95 % + 15 pp, and
CAISO's `[15.0 %, 30.0 %]` as 15.00 % + 15 pp.

**What this changes about FFR-3A's ERCOT headline, stated without overselling it.** Against the
model's own floor the trajectory `9.1 % → 3.8 % → 3.0 % → −1.5 %` breaches in **three** years,
not four — 9.1 % clears +7.15 % — and the deepest excursion is **−8.65 pp**, not −15.3 pp. I12
FAILs on `>= 3` consecutive out-of-band years, so **the FAIL verdict is robust and does not go
away**; what is overstated is the *magnitude*, by 6.65 pp, and the *first year*. The W1-B F4
amendment fixed precisely this basis problem for capacity-market ISOs and deliberately left
ERCOT on the old scalar "byte-identical to the pre-W2-D behaviour" — under rule 14
`[R-ACCURATE]` the model's DR-netted basis is the accurate one and the invariant's generic
scalar is the estimate. **CAISO's collapse is NOT affected by this** and is not a basis
artifact: CAISO is scored on the model's own basis, so −3.1 % against a 15.0 % floor is a real
18.1 pp shortfall within the model.

### 2.2 I7/I12 do not thread `year` into the requirement; the model does

`retirements.py:1136` calls `resolve_adequacy_requirement_mw(config, iso, peak, year)`; the
checkers call it **without** `year` (`check_forecast_invariants.py:465`, `:628`). With `year`
the resolver takes the published-FPR path; without it, the `(1+PRM)×ratio` fallback. Measured
gap on a 100 GW peak:

| ISO | 2026 | 2027 | 2028 | 2029+ |
|---|--:|--:|--:|--:|
| **PJM** | +0.96 % | +1.83 % | **+3.18 %** | 0 |
| all others | 0 | 0 | 0 | 0 |

PJM-only, 2026–2028 only, and in the **lenient** direction — the checker tests a *smaller*
requirement than the model enforces, so PJM's I7 miss (366 MW on ~150 GW) is understated
rather than manufactured. Real defect, wrong size to explain anything in §0. Logged, not
fixed — fixing a scorer after seeing the score is the move rubric §4 forbids.

---

## 3. The MISO control arm

### 3.0 Pre-registration (written and committed BEFORE the arms were solved)

Recorded first so the reading of §3.1 is a test, not a rationalization. Two mechanical
predictions follow from the code alone:

* **P1 — D-1 is close to INERT in MISO's T1-F window.** The pipeline's `pipeline_state` starts
  empty, `decided_year = year − 1`, and `L_coal = 3` / `L_gas_ct = 2`, so nothing decided in
  2026 can execute before 2028. The legacy counter needs 3 consecutive failing years for coal
  and cannot fire before 2028 either. FFR-2B independently measured **I6 = 0.00 % in MISO T1-F
  under BOTH arms** — i.e. zero economic retirements across the window. So MISO's 2026–2027
  adequacy miss cannot be a retirement-rule effect.
* **P2 — therefore any 2026–2027 arm difference is D-2, the entry dampers.**
  `entry_rate_limits` caps MISO dispatchable-thermal entry at ~4.8 GW/yr and
  `entry_commissioning_lag` shifts COD by `ENTRY_COD_LAG_YEARS = 2`, so the treatment cannot
  close a first-year gap the control can. Expect the control's early-year reserve margin to be
  **materially higher**, and the attribution to land on D-2.

If P1/P2 hold, **MISO cannot reproduce the ERCOT pattern**, because the ERCOT pattern requires
the exit half to fire and in MISO's window it does not.
