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

### 3.1 Both arms, measured

Paired MISO T1-F 2026–2030, `--golden-posture` (MISO resolves **curve-ON** = its shipped arm),
5/5 years each, `error: None`, cold post-epoch, run **sequentially** (rule 12 — MISO solo at
9.3 GB peak). Cache keys verified **distinct before either arm was solved**.

| leg | yrs | wall | peak RSS | curve | cache key | FAIL | WARN |
|---|---|---|---|---|---|---|---|
| MISO **treatment** (D-1+D-2, shipped) | 5/5 | 23.4 m | 9.31 GB | `True` ✓ | `b3d33a1955c7854d` | I7 | I12 |
| MISO ***control*** (pre-decision) | 5/5 | 19.6 m | 9.30 GB | `True` ✓ | `3a0061377cba3d34` | I7 | I12 |

**The invariants the packet asked for, in FFR-3A's table shape:**

| invariant | TREATMENT (D-1+D-2, shipped) | CONTROL (pre-decision) | |
|---|---|---|---|
| **I12** reserve margin | **WARN** — 2 yr out (2026 5.3 %, 2027 7.1 %; band [10.0 %, 25.0 %]) | **WARN** — 1 yr out (2026 5.3 %) | **the 2027 leg is D-2's** |
| **I7** accredited firm | FAIL — 2026 short **6,037 MW**, 2027 short **3,659 MW** | FAIL — 2026 short **6,037 MW** only | 2026 **IDENTICAL**; 2027 is D-2's |
| **I3** unserved/dump | **PASS** | **PASS** | unchanged — no unserved energy in either arm |
| I1–I6, I8–I11, I13, I14 | PASS | PASS | unchanged |
| **rubric FC-2** | **CAVEAT** | **CAVEAT** | **DOES NOT MOVE** |
| determination | HOLD (FC-1, FC-7) | HOLD (FC-1, FC-7) | unchanged |

### 3.2 Answer 1 — MISO does NOT reproduce the ERCOT pattern, and its I12 did NOT flip

Three separations, each measured:

**(a) MISO's reserve margin RECOVERS; ERCOT's declines.** The two trajectories are opposite in
sign, not merely different in degree:

| | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|--:|--:|--:|--:|--:|
| MISO treatment RM | 5.26 % | 7.13 % | **10.83 %** | **13.79 %** | **12.34 %** |
| *vs the model's own floor (9.95 %)* | −4.70 | −2.82 | **+0.88** | **+3.84** | **+2.39** |
| *ERCOT treatment RM (FFR-3A §6.4)* | *9.1 %* | *3.8 %* | *3.0 %* | *−1.5 %* | — |

MISO is below its floor for two years and **above it from 2028 onward**. It never goes
negative, and I3 shows **no unserved energy at all**. There is no collapse in MISO.

**(b) I12 is WARN in BOTH arms — it never FAILs, under either configuration.** I12 FAILs on
`>= 3` consecutive out-of-band years; the treatment has exactly 2. So the consequence D-2 was
signed against — *"MISO's I12 goes WARN→FAIL"* — **does not reproduce even against its own
paired control**. FFR-3A measured this without a control and correctly declined to attribute
it; with the control, the finding is now attributed: **MISO's I12 does not flip because the
mechanism that would flip it never fires** (see (c)), not because some offsetting input hid it.

**(c) The reason is structural: D-1 is PROVABLY INERT in MISO's T1-F window.** Not "small" —
literally zero events, in both arms:

| | treatment | control |
|---|---|---|
| economic retirements | **0 MW, 0 units, every year** | **0 MW, 0 units, every year** |
| R-NEW pipeline events (decided / re_confirmed / entry_capped / executed) | **NONE** | n/a (legacy) |
| reliability-floor retentions | NONE | NONE |
| announced retirements | 633 MW (3 units) | **633 MW (3 units) — identical** |

The retirement pipeline is never entered by a single unit. This is the mechanical consequence
pre-registered in §3.0: `pipeline_state` starts empty, `decided_year = year − 1`, and
`L_coal = 3` / `L_gas_ct = 2`, so nothing decided in 2026 can execute before 2028 — and in fact
nothing was ever decided, because no MISO unit failed the bar. **P1 CONFIRMED.**

**Therefore the ERCOT pattern is not reproducible in MISO's window on this evidence, and no
conclusion about D-1 can be drawn from MISO either way.** MISO is a valid control for D-2 and
an *uninformative* one for D-1. That is a real limit on what the highest-value second
attribution could deliver, and it was not knowable before the run.

### 3.3 Answer 2 — MISO's entire arm delta is D-2, and it is a TIMING effect

**2026 is identical in both arms**, to the megawatt: accredited firm 135,304 MW, RM 5.26 %,
peak 128,549 MW, zero exits, zero additions of any kind (thermal, renewable, storage), and
`fleet_by_fuel_before == fleet_by_fuel_after` — **the fleet does not change at all in the first
solve year**. So MISO's 2026 I7 shortfall of 6,037 MW is a **base-fleet / accreditation
starting condition and is attributable to NEITHER signed decision.** It is present in the
pre-decision configuration exactly as it is in the shipped one.

**2027 is the whole delta, and it is the commissioning lag:**

| 2027 | treatment | control |
|---|--:|--:|
| reserve margin | 7.13 % (−2.82 pp vs floor) | **13.40 % (+3.45 pp)** |
| thermal additions: planned | 55 MW | 55 MW |
| thermal additions: **economic** | **0 MW** | **5,000 MW** |
| thermal additions: **reserve backstop** | **0 MW** | **2,873 MW** |
| I7 | short 3,659 MW | **cleared** |

The control closes the gap in 2027 by building 7,873 MW. The treatment cannot: with
`entry_commissioning_lag` armed, a build decided in 2026–27 commissions
`ENTRY_COD_LAG_YEARS = 2` later. And that is exactly where the treatment's capacity appears —
**2,049 MW of backstop in 2028 and 4,350 MW of economic entry in 2029**, arriving after the
two-year miss rather than during it.

**So D-2 converts a one-year I7 miss into a two-year one by deferring the fix, not by making
the system shorter.** MISO's adequacy problem is a *starting condition* the model closes either
way; the dampers govern how fast. Under rule 1 `[R-STRUCT]` the damped arm is the faithful one
— the control closes its 2027 gap with a 5,000 MW single-year economic thermal build plus a
2,873 MW backstop against a MISO record whose largest-ever single-year gas_cc build is
1.723 GW (§1.4), i.e. the control's fix is not buildable. **The damper is not the defect; it is
what makes the undamped arm's answer visible as unbuildable.**

**Cumulative build, with its censoring caveat stated.** Over the 5-year window the treatment
builds **7,819 MW** of thermal against the control's **13,643 MW** (−43 %), with storage moving
the other way (10,400 vs 8,000 MW). **This window under-counts the treatment by construction**:
a 2-year COD lag means decisions taken in 2029–2030 commission in 2031–2032, outside the
window entirely. The cumulative figures are therefore *not* evidence that the dampers reduce
total build — FFR-2B measured the cumulative backstop as re-phased, not reduced (−0.07 %), and
nothing here contradicts that. Only the *timing* claim is supported by this window.

---

## 4. The answer to the owner's question

**(c) — both, with a measured split. The split is MEMBERSHIP (real) vs CALENDAR (artifact).**

| term | verdict | evidence |
|---|---|---|
| **Which units the screen retires** | **REAL going-forward economics.** The corrected rule identifies the right units better than the rule it replaced. | FFR-2B recall MISO 2/17→13/17, PJM 9/17→13/17; T-R10a/b FAIL→PASS holding 3/3 LOYO |
| **WHEN they leave (one lumped year)** | **GRAIN ARTIFACT.** D = 0 decision + per-fuel constant lag = a translation operator with no spreading term; the only spreading mechanism the model ever had was deleted at the same commit. | §1.2 G1/G2 (all 12 decided in one year, all executed in one year); §1.3 |
| **The DEPTH of the reserve-margin trough** | **THE INTERACTION**, and it is an asymmetry nobody measured before arming both halves: exit throughput uncapped, entry throughput capped at 2× the measured record. | §1.4 (model single-year exits 1.6×–4.8× the historical envelope; MISO entry cap 4.8 GW/yr) |
| **ERCOT's headline −1.5 % specifically** | **Overstated by 6.65 pp** by a basis mismatch — but the I12 FAIL is robust and does not go away. | §2.1 |
| **CAISO's −3.1 %** | **NOT a basis artifact.** Scored on the model's own basis; an 18.1 pp shortfall within the model. | §2.1 |
| **MISO** | **NEITHER.** Its 2026 miss is a base-fleet starting condition present in both arms; its 2027 miss is D-2 deferring the fix. No collapse, no I12 flip, D-1 provably inert. | §3.2, §3.3 |

**Why "artifact" is the right word for the calendar and not a hedge.** A lag and a rate cap are
different operators. The R-NEW redesign replaced a mechanism that had both (`the counter's
delay` + `staged_oversupply_thinning`'s throughput cap) with one that has only the delay, on an
argument — rule 19, "the same physical queue, carried once" — that treats queue latency and
queue throughput as the same quantity. §1.2 shows they are not: with only the latency term,
exit-wave width is invariant at exactly one year no matter how many units fail. The model
therefore has no representation of the constraint that stops a real ISO deactivating 21 GW in a
single year, while it *does* have one — armed, measured, and correct — for the constraint that
stops it building 21 GW in a single year.

---

## 5. What this evidence does NOT separate — stated plainly

The charter asked for an honest "not separated" where the evidence does not reach. Three things
it does not:

1. **The split is not quantified as a fraction of the ERCOT/CAISO trough.** Saying "the calendar
   is an artifact" is not the same as saying "X pp of the −1.5 % is the artifact." Separating
   them requires solving ERCOT with the exit wave *spread* and holding everything else fixed —
   i.e. arming a throughput mechanism. **That is a fix, and the charter forbids shipping one
   here.** What would settle it is stated in §6.
2. **MISO cannot adjudicate D-1 at all.** Zero economic exits in the window means the second
   attribution the owner commissioned returns *no information* about the retirement half — only
   about the entry half. ERCOT remains the **only** ISO where D-1 is attributed against a
   control. A D-1 attribution in a capacity-market ISO still does not exist, and rule 25
   `[R-ISO-SCOPE]` forbids importing ERCOT's.
3. **Nothing here re-measures ERCOT or CAISO.** Their numbers are FFR-3A's, quoted. §2.1's
   6.65 pp correction is computed from the shipped constants and is arithmetic on the band, not
   a re-solve. The re-solve that would confirm it is not in this charter either.

---
## 6. What a G-31 fix lane would need to charter

Written as a specification, not a recommendation to arm anything — the fix is a successor lane
with its own charter and its own owner decision (packet: *"Characterize it; the fix is a
successor lane"*).

1. **The identification already exists and is measured.** The redesign memo named the source —
   *"max observed single-year per-ISO thermal deactivation from the EIA-860 retired sheet"* —
   and §1.4 measures it (MISO 7.57 GW, PJM 5.24, ERCOT 4.42, CAISO 1.48, NEISO 0.45, NYISO
   0.31; medians 3.54 / 1.32 / 0.39 / 0.05 / 0.02 / 0.03). A throughput term would be
   externally identified from source data, not fitted to a residual — rule 13 `[R-MEASURED]`
   admissible and rule 23 `[R-FROZEN-DERIVE]` compliant (re-derives on an EIA-860 vintage
   update, never on a residual). The reader is
   `scratchpad/measure_exit_throughput.py` in this session's record; a lane would move it to a
   `data/` module beside `build_throughput.py`, its exact entry-side analogue.
2. **It must resolve the rule-19 question head-on, not route around it.** The lane's first
   deliverable is an adjudication: are queue *latency* and queue *throughput* one mechanism or
   two? §1.2 is the evidence that they are two. If the owner rules them one, the lane closes and
   G-31 is instead routed to whatever else can spread a wave. **A throughput cap must not be
   armed by a session that has not obtained that ruling** — otherwise it is exactly the
   stacked-floor pattern rule 19 exists to prevent.
3. **The G3 cap-grain defect is separable and cheaper.** The pipeline's admission cap tests the
   **decision** year's requirement against exits that execute 1–3 years later (§1.2, +10.3 % of
   requirement unseen in the synthetic). Threading the execution year into that one call is a
   much smaller change than a new mechanism, needs no new parameter, and is a candidate for
   being fixed *first* so a throughput lane is measured against a correct cap.
4. **It must be scored leave-one-year-out within 2023–2025 before promotion** (rule 22), and the
   T1-F re-measurement must be paired against a control, because §3.2 shows an ISO can be
   structurally incapable of exercising the mechanism under test.
5. **Two ISOs are the right test set, and MISO is not one of them.** ERCOT (the failing I6 case,
   26.8 %) and PJM (12.68 % legacy → 8.55 % pipeline, the largest measured wave). MISO retires
   nothing economically in a T1-F window and cannot exercise an exit-throughput mechanism at
   all.

## 7. Open blockers

**Carried forward unchanged from FFR-3A** (none was in this charter to fix): blocker 0 (the
collapse itself — this document is its attribution, not its resolution), 1 (`data/clean`
prerequisite), 2 (C.4(a) B1 posture source — *signed at Addendum D.1, not yet executed*),
3 (C.4(c) harness pins — *signed UN-PIN at Addendum D.1, not yet executed*), 4 (optional-field
cache-key hazard), 5 (zero-year console line), 6 (pre-existing test failures), 7
(`run_full_horizon` never writes `run_config.json`), 8 (FC-2 row4 SKIPPED).

**Blocker 7 is now measured as universal, not ISO-specific.** FC-7 FAILs on **both** MISO arms
for the identical reason (`run_config.json absent`), exactly as it did on all six FFR-3A legs.
Every T1-F leg this runner produces is unpromotable on provenance **by construction**, so the
determination `HOLD` in §3.1 carries no information about either arm's quality. Left as found,
for the same reason FFR-3A left it: authoring the artifact after seeing the score is what
rubric §4 forbids.

**New from this session:**

9. **`data/clean` regeneration is NOT 50/50 clean on a fresh container.** `ercot-wtx-congestion`
   fails with `ZoneInfoNotFoundError: No time zone found with key ...` because the image ships
   no `tzdata` package. Fixed in-session with `pip install tzdata` (2026.3), after which the
   datatype curates cleanly (7 year files). FFR-3A's *"50 datatypes, 0 failures"* is **not
   reproducible without that package** — this belongs with blocker 1, and the failure is loud
   and ERCOT-only, so it does not silently corrupt a MISO leg. Measured cost of the
   prerequisite here: **≈65 min, 50 datatypes, 1.6 GB, 404+ parquet files** on a 4-core/15 GB
   container, dominated by the CAMPD `emissions` extract at ~27 M rows/year.
10. **The evolution ledgers are NOT in `--out-dir`.** `run_full_horizon` rebases the cache root
    under `--out-dir`, so a leg's per-year `evolution_<year>.json` lives at
    `<out-dir>/<ISO>/<cache_key>/`, not the out-dir root and not `results/<ISO>/<key>/`. Any
    successor reading ledgers by the documented `load_ledgers_for_run(cache_dir)` contract will
    find an empty result and, because the function returns `{}` rather than raising, will read
    it as "no evolution happened." Recorded because that failure mode is silent.
11. **`--golden-posture` reproduces MISO's shipped curve arm correctly** (`capacity_market_
    clearing` resolves `True` on both arms, matching FFR-3A §4.3). No new posture defect found.

## 7b. Mechanism matrix (rule 28)

Two cells were exercised this session; **neither verdict was changed**, because the owner
withheld adjudication and because a 5-year forecast window is not a verdict on a mechanism.
Both notes and both `ev` citations were updated in-session, per duty (b).
`scripts/check_mechanism_matrix.py` passes.

| row | MISO cell | action |
|---|---|---|
| `economic_retirement_screen` | **R — unchanged** (still the shipped-legacy verdict FFR-2B recorded) | note records the G-31 grain characterization and the measured zero-exit/zero-pipeline-event result; **FFR-3C adjudicates nothing here** |
| `entry_dampers` | **O — unchanged** | note records the paired-arm measurement: 2026 identical, 2027 delta is the commissioning lag, I12 WARN in both arms, FC-2 CAVEAT in both |

No new `ScenarioConfig` field was added, so duty (c) does not apply. No run was registered, so
the duty-(b) registration half is moot — the evidence is this document.

## 8. What this session does NOT claim

* **No promotion, no registration.** `frontend/data/forecast/` is untouched; `ff-verdicts.json`
  and `program-status.json` are unchanged; the backcast registry was never touched. Both arms
  are HOLD and stay HOLD. Nothing here is a keeper or a candidate.
* **No default changed.** `retirement_rule` is still `pipeline`; both entry dampers are still
  armed; no band was widened, restated, or reinterpreted; no threshold moved. The control arm
  reaches the pre-decision configuration through **CLI flags only**.
* **No keeper moved.** All six shards re-read at this HEAD match the packet exactly (ERCOT
  `2026-08-02-ercot150b-zonal-anchor`, PJM `2026-08-03-pjm-147b-chp-heat`, CAISO
  `2026-08-03-caiso156-meter-screen-b`, NYISO `2026-08-02-nyiso-113-li-locational`, NEISO
  `2026-08-03-neiso-caiso156-meter-screen`, MISO `2026-08-03-miso-117b-ct-heat`), and
  `git status frontend/` is empty. Forecast-mode gates cannot reach a backcast keeper anyway
  (FFR-3A §2), but the check was run rather than assumed.
* **No holdout year touched.** Both arms are forecast-mode 2026–2030, which the freeze
  explicitly does not restrict. No backcast year was solved, scored, or read.
* **No G-31 fix.** §6 is a charter for a successor lane, not a change. Nothing in `src/` was
  modified by this session at all — the two measurement scripts are session-record scratch, not
  shipped modules.
* **Cross-ISO causation is still not claimed.** ERCOT remains the only ISO where D-1 is
  attributed against a control, and §3.2 explains why MISO could not extend that.
