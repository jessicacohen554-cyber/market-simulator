# FF-0C — Economic-retirement decision-rule redesign (memo, 2026-07-17)

**Charter.** FF-0C of the Forecast Finalization Program
(`docs/forecast-development-plan-2026-07.md` §1.2-1, §4, §6 Wave 0; §7 binds):
redesign the economic-retirement decision rule to kill the per-fuel threshold
inversion that RC-1A-D1 measured
(`docs/handoffs/position-calibration-d1-findings-2026-07-16.md` §6/§7 — the
blocker this memo solves). **Memo only — no code, no solve, no tuning, no
parameter or default changed, nothing registered on any dashboard.** Rules
1/13/14/21/23 govern: every candidate is graded on its forward story,
identification source, and freedom from residual fitting; nothing is proposed
because it would move a hindcast number. This memo gates FF-1A (implementation
+ re-probe + LOYO), which must not start without owner sign-off on §6.

**Inputs read.** The D1=3 findings (RC-1A-D1), the DOF-identification memo
(`docs/handoffs/retirement-dof-identification-2026-07-15.md` — the §a.3 lag
identification that MUST survive this redesign), the flip memo
(`docs/handoffs/capacity-clearing-flip-memo-2026-07-16.md`),
`model/capacity.py::apply_economic_retirements` (+ `_apply_reliability_floor`,
`_apply_staged_thinning_cap`), `scenarios.py:355-433` (the
`retirement_years_*` / `staged_oversupply_thinning` fields and their
citations), and the flip-gate plan's §3 T-R battery. Field-practice survey per
plan §4: EPA IPM v6, ReEDS, GenX, PLEXOS LT, Aurora (§2, with sources).

---

## 0. Bottom line first

**The consecutive-loss counter with per-fuel thresholds conflates two
different physical quantities — the owner's DECISION to exit and the measured
announcement→deactivation EXECUTION lag — into one integer, and uses that
integer as a cross-fuel race handicap.** Because loss onset is synchronized
across fossil classes (the dominant loss driver is system-wide), the fuel
with the smallest integer always exits first regardless of relative
economics, and the only cross-fuel economic comparison in the mechanism (the
reliability floor's cheapest-firm-adequacy retention) is structurally
prevented from choosing between fuels whose integers differ. No commercial
capacity-expansion model surveyed uses per-fuel decision thresholds; all four
make the decision uniformly economic and let fuel differences enter through
data (§2).

**Recommendation (owner box §6, Option B): split decision from execution.**
A uniform economic decision (one failing annual screen, the degenerate
flat-expectation form of the NPV screen), joint cross-fuel competition at
decision time (the existing cheapest-firm-adequacy machinery, now applied to
one shared eligible set), annual re-confirmation while pending (a soft latch
— no new parameter), and deactivation after the per-fuel EXECUTION lag
`L_f` identified by the RC-0B §a.3 lag table — the same table that
identified coal = 3, so the adopted identification survives intact (coal's
loss→gone total stays 3 years; timing unchanged for a persistent-loss coal
cohort). Zero newly *tuned* parameters; one honest open DOF (the decision
persistence, unobservable per RC-0B) is ledgered, not fitted.

**What this memo does NOT claim:** the redesign removes the *structural*
race. It cannot make a mis-leveled revenue signal retire the right fleet —
if the screen says gas_st is genuinely under water while real gas_st
survived, that is the revenue-side lane (BLK-6/BLK-9, GFC/RD-4), and the new
T-R10 no-inversion guard (§4) is the pre-registered instrument that
adjudicates which half of the MISO inversion the redesign actually closes.
Expected improvements are EXPECTED, never graded PASS (RC-2B discipline);
FF-1A measures.

---

## 1. (a) Diagnosis — the mechanism, precisely

The screen (`capacity.py:1183-1601`) increments a per-unit counter each year
`net_revenue < going_forward_cost`, resets it to zero on any profitable
year, and retires the unit — effective immediately, whole cohort at once —
when the counter reaches `retirement_years_<fuel>`. Five interacting defects
produce the measured D1=3 failures:

**1. Synchronized loss onset.** The loss signal's dominant terms are
system-wide, not unit-specific: under curve-ON at a long position the
capacity payment zeroes *for every fossil class in the same year*, and fuel-
price regimes move whole classes together. Measured: in the MISO D1=3 probe
the 2023 floor log shows gas_ct (24.0 GW), gas_st (5.3 GW), and oil (0.33
GW) all at `loss_years=2` — onset 2021 for every class — while coal's
counter, also running from 2021, had not yet reached its higher threshold
(D1 findings §1). Onset is common; only the thresholds differ.

**2. The threshold is a race handicap, not a lag.** With synchronized onset
at year `y0`, fuel `f` becomes exit-eligible at `y0 + N_f`. The cross-fuel
exit ORDER is therefore ascending `N_f` — a function of the config integers
alone, independent of loss depth, retention cost, or any economics. A
per-fuel value intended as execution-physics DATA (the measured
announcement→deactivation pipeline, RC-0B §a.1) operates as an
order-determining DECISION input. Raising coal 1→3 with gas_st at 2 did not
delay coal relative to reality; it demoted coal to second place in a race
gas_st now wins: 8.643 GW of gas_st — a fuel that retired **zero** in
reality — exits 2023, one year before coal is even eligible.

**3. The eligibility partition blocks the only economic cross-fuel choice.**
The reliability floor's cheapest-firm-adequacy retention is the one place
the mechanism compares units across fuels on economics ($/firm-MW-yr, CO2
tie-break). But it operates strictly *within the currently-eligible set*.
Per-fuel thresholds partition eligibility in time, so in MISO-2023 the floor
could only choose among {gas_st, gas_ct, oil} — "retain gas_st, release
coal" was not an expressible outcome, because coal was absent from the
eligible set (counter < 3). The economically correct composition existed in
the machinery and was unreachable by construction.

**4. The consecutive-AND is a persistence filter with geometric attrition —
a category error against the identified quantity.** RC-0B §a.1 identifies
`N ≈ D + L` where `L` is the announcement→deactivation lag — a delay that
runs AFTER the owner has decided. The counter instead demands `N`
*consecutive* loss years BEFORE any exit — a condition on the persistence of
the decision signal. Those are different mathematical objects: a delay
shifts *when* a decided exit lands; a persistence filter changes *which*
units ever exit. For any loss process that is not persistent, the
probability of an unbroken `N`-streak decays geometrically in `N`. Measured:
PJM's cap-weighted coal screen margin oscillates 77.0 → 113.3 → 24.1 → 142.1
$/kW-yr around the 58.5 bar, so at N=3 the streak never forms and the coal
wave is ELIMINATED (recall 76% → 0%, all LOYO folds) — against a reality
that retired 6.885 GW of PJM coal in-window. Implementing the identified
3-year *execution* lag as a 3-year *persistence requirement* deleted real
exits instead of delaying them.

**5. Position feedback makes the race winner-take-most.** The first-eligible
fuel's exits shorten the capacity position, the payment recovers, and later
fuels' counters reset (PJM: a profitable step zeroes the streak) or their
waves shrink (MISO coal 11.809 → 3.558 GW once gas_st moved first). The
counter's reset-on-any-good-year is the coupling channel: a fuel's own
delayed exit is cancelled by the price recovery another fuel's exit caused.

Summary statement of the inversion: **per-fuel consecutive-loss thresholds
convert an execution-lag input into (i) a persistence filter on the decision
and (ii) a cross-fuel priority ordering, while (iii) time-partitioning the
eligible set so the floor's economic retention can never overrule that
ordering.** Any fix must remove all three couplings, not re-tune the
integers — there is no assignment of per-fuel `N_f` that is simultaneously
lag-faithful and order-neutral, because order = ascending `N_f` is
structural (defect 2).

---

## 2. Field practice (plan §4 mandatory survey) — adopted / rejected

| Practice | What it does for retirement | Adopted | Rejected |
|---|---|---|---|
| **EPA IPM v6** (Platform v6 documentation, ch. 2 & 4) | Retirement is an *option inside the horizon-NPV LP*: the objective minimizes discounted NPV of all costs over the planning horizon; an existing unit retires when going-forward value no longer covers going-forward cost. A retired unit ceases FOM+VOM but keeps annualized payments on sunk retrofit capital; at end-of-lifespan each unit faces an explicit retire-or-pay-life-extension choice (ch. 4 §4.2.8). Firmly-committed (enforcement-action) retirements are hard constraints, separate from the economic option (ch. 4 §4.2.4). **No per-fuel decision thresholds anywhere** — fuel enters via FOM, life-extension capex, lifespans. | Uniform NPV going-forward decision; committed exits as a separate constrained channel (= our confirmed registry); fuel differences as cost DATA only; sunk costs never in the decision. | Full intertemporal foresight and horizon co-optimization — architecturally incompatible with the one-pass myopic year loop (CLAUDE.md rule 10) and a program-scale rewrite; perfect foresight also overstates merchant exit discipline. |
| **ReEDS** (NREL model documentation, 2019/2020 editions) | *No endogenous economic retirement*: age-based lifetimes plus, for coal, an exogenous capacity-factor threshold that ramps 6% (2022) → 50% (2040); NREL's own documentation labels this a construct "to estimate realistic coal retirement behavior" **because** endogenous retirement is absent. | The honesty: an exogenous proxy schedule is a stand-in, not a mechanism — and staggered (phased) exit realism matters. | The CF-threshold rule itself: a tuned trajectory with no forward story and no market driver — exactly the fitted-schedule shape rules 1/13 forbid. Also rejected as a cautionary precedent for ANY per-fuel special-cased rule. |
| **GenX** (GenX.jl documentation; MIT Energy Initiative 2017 report) | Retirement is a *decision variable* co-optimized with builds in one LP/MILP: net installed capacity = existing − retired + built, each carrying FOM; a unit's capacity retires exactly when its FOM exceeds its equilibrium market value. Uniform economics, no counters, no per-fuel thresholds. | Retirement and entry priced on the same signal in the same competition (our screen already shares the capacity-payment basis with the entry screen — keep that symmetry). | Single-LP co-optimization of build/retire/dispatch (same rule-10 architecture reason); continuous retirement of capacity slices where our unit grain is discrete is not the binding issue. |
| **PLEXOS LT Plan** (Energy Exemplar LT Plan documentation) | Capacity expansion = optimal builds AND retirements minimizing horizon NPV; expansion/retirement decisions are integer variables; supports "planned" vs "economic" retirement as distinct categories. | The planned/economic channel separation (= our announced/confirmed vs economic split, already built); integer (whole-unit) exit decisions at our unit grain. | MIP machinery and multi-decade foresight (rule 10; solver stack is HiGHS LP by design). |
| **Aurora** (Energy Exemplar; NWPCC 2021 Power Plan model writeup) | Iterative long-term logic: computes each existing resource's real levelized NPV of market value vs its going-forward (avoidable) cost, retires the *lowest-value* resources, re-simulates, and repeats until the marginal unit is viable — worst-first, partial, equilibrium-seeking. | **Worst-first ordering by margin depth** as the exit-composition principle (the field's answer to "which units go when many are under water"), realized across our sequential annual loop rather than within-year. | Within-year convergence iteration (rule 10 explicitly forbids it; the annual evolution loop already provides the outer iteration at annual grain). |
| **Monitoring Analytics / PJM Manual 18 avoidable-cost** | The real-world decision bar: avoidable (going-forward) cost vs net revenue — the construction our screen already mirrors (attainable pro-forma margin vs FOM-based GFC). | Already adopted; the RD-4 ACR reconciliation (RC-0B §b) remains the bar's identification lane and is untouched here. | — |

**Survey conclusion.** The field's common denominator: *the exit decision is
uniform and economic — a going-forward NPV/avoidable-cost comparison — and
fuel differences enter exclusively through data (costs, lifespans, lags).
None of the surveyed models uses per-fuel decision thresholds, and none uses
consecutive-loss counters.* Persistence/lumpiness is handled by foresight
(IPM/GenX/PLEXOS) or by iteration with worst-first ordering (Aurora); in a
myopic annual loop the admissible analogues are (a) the decision/execution
lag split and (b) worst-first depth ordering — which is exactly where the
candidate set below lands.

---

## 3. (b) Candidate rules, graded vs rules 13 / 21 / 23

Grading key per candidate: **Forward story** (rule 13: regenerates from
forward drivers, responds to changed conditions), **Identification** (rule
21: what pins each parameter; unidentifiable values are open DOFs, never
tuned), **No residual fitting** (rules 1/13/23: nothing chosen because it
moves a hindcast number), and **which §1 defects it removes**.

### 3.1 (i) NPV-of-going-forward-window screen + per-fuel EXECUTION lag

Decide exit when the NPV of expected going-forward net revenue over a
forward window `H` falls below the NPV of going-forward cost; execute the
exit `L_f` years after the decision, `L_f` from the RC-0B §a.3 lag table
(decision vs deactivation split). The IPM/PLEXOS/Aurora shape.

- **Forward story: strong.** The decision is pure economics; the lag is
  measured execution physics (RTO deactivation review, decommissioning,
  fuel-contract wind-down) that regenerates for any forecast year and any
  fuel.
- **Identification.** `L_f`: IDENTIFIED — §a.3 medians (coal 3 cap-wtd/
  ≥300 MW; gas_ct 2; gas_st 1; oil 1; gas_cc 1 (n small); nuclear
  unidentifiable → hold 3, §a.5; ccs → inherit gas_cc). Re-derives only on
  EIA-860 vintage update (rule 23). **The adopted coal identification
  survives**: coal's loss→gone total remains 3 years. `H` and the revenue-
  expectation model: NOT identifiable, and in this myopic model largely
  vacuous — the loop has no future price path, so the only honest
  expectation is flat persistence of the current-year signal, under which
  the NPV sign equals the single-year sign for every `H`. The window
  degenerates; introducing `H` as a field would be an unidentified knob
  with no operative content (rule 24 violation waiting to happen).
- **Residual fitting: none** — all live values come from the lag table.
- **Defects removed: 2 (partially), 4.** The persistence filter is gone
  (decision fires on the economics, not a streak). But with synchronized
  onset the *execution* order is still ascending `L_f` — gas_st (L=1)
  deactivates before coal (L=3) — so the race survives at the execution
  stage unless combined with cross-fuel competition at decision time
  (§3.3/§3.6). Not sufficient alone.

**Grade: adopt the degenerate (flat-expectation) form — the decision/
execution split — as the backbone; do not introduce `H`.**

### 3.2 (ii) Uniform identified decision threshold + per-fuel notice lag

Keep a consecutive-loss counter but make its threshold `N_dec` UNIFORM
across fuels, then execute after `L_f`.

- **Forward story: adequate** (same split as (i) plus a persistence
  requirement on the decision).
- **Identification: fails on the new parameter.** `N_dec` is exactly the
  `D` (loss-years-until-decision) component RC-0B §a.1 proves unobservable
  from any on-disk source. There is no data that pins `N_dec = 2` vs `1`;
  choosing the value that makes PJM/MISO score is textbook residual fitting
  (rule 13). And any `N_dec > 1` re-imports defect 4 (PJM's oscillating
  margin defeats a uniform streak too — its 4-step trace never carries 2
  consecutive losses either).
- **Defects removed: 2, 3** (uniform threshold ⇒ common eligibility year ⇒
  the floor can compare across fuels); **defect 4 retained** for
  `N_dec ≥ 2`.

**Grade: subsumed by (i)** — (ii) at the only identification-defensible
point (`N_dec = 1`, the parsimonious flat-expectation reading) IS (i)'s
degenerate form. Fold together; ledger the persistence question as the open
`D` DOF rather than a field.

### 3.3 (iii) Margin-depth cohort thinning (worst-first partial waves)

When more capacity is exit-eligible than the system can lose, exit
worst-first by margin depth — `(GFC − net_revenue)/pmax` in $/kW-yr, or
equivalently the floor's existing $/firm-MW-yr retention metric — as
partial waves, rather than the whole cohort at once. Aurora's worst-first
principle at annual grain; generalizes `_apply_staged_thinning_cap` from a
per-fuel heat-rate-ordered budget to a JOINT cross-fuel economically-ordered
selection.

- **Forward story: strong** — "deepest losses exit first" is the market
  mechanism itself; regenerates trivially.
- **Identification.** The ordering metric introduces NO parameter (computed
  from quantities the screen already has). A throughput/rate cap, if any,
  would need its own identification (max observed single-year per-ISO
  thermal deactivation from the EIA-860 retired sheet — measurable) — but
  **rule 19 says don't arm one**: the execution-lag pipeline of (i) already
  carries the deactivation queue (the RC-0B §a.6 double-count warning,
  restated: threshold-carries-D+L was why `staged_oversupply_thinning`
  stays off; the lag pipeline inherits that role).
- **Residual fitting: none.**
- **Defects removed: 3, 5 (partially)** — the exit composition becomes
  economic; but without (i) the per-fuel eligibility gates still decide WHO
  is in the comparison set, so (iii) alone cannot fix the inversion (coal
  was not in the 2023 eligible set at any ordering).

**Grade: adopt as the composition/ordering component, joint across fuels,
no rate cap.**

### 3.4 (iv) Hysteresis band

Retire below `bar − h`, retain above `bar + h`, hold state in between —
targets defect 4 (PJM's oscillation) by making the distressed state sticky.

- **Forward story: plausible** (real exit decisions are sticky).
- **Identification: fails.** Nothing on disk pins `h`; the only visible
  anchor is the amplitude of the PJM margin oscillation — i.e., the
  residual itself. A tuned `h` is a fitted answer key (rules 13/21/23),
  and a "neutral" `h` is dead code (rule 26).
- **Note:** the recommended rule delivers hysteresis's operative effect
  with zero parameters: a pending decision is re-confirmed against the SAME
  bar each year (soft latch, §3.6), so one good year no longer erases the
  distress history unless the unit actually clears the bar — asymmetry
  without a band.

**Grade: REJECT as a parameterized band; its intent is absorbed
parameter-free by the pipeline latch.**

### 3.5 Literature-derived candidates not in the charter list

- **ReEDS-style CF-threshold schedule — REJECT** (§2): exogenous tuned
  trajectory, no market driver, no forward story; ReEDS documents it as a
  proxy for the mechanism we are building.
- **Full endogenous horizon co-optimization (IPM/GenX/PLEXOS) — REJECT
  machinery, adopt principle** (§2): rule 10 (one-pass evolution) and the
  LP-only stack are load-bearing architecture; the uniform-economics
  principle survives the port, the foresight does not.
- **Aurora-style within-year iteration — REJECT** (rule 10); the annual
  loop is the iteration, and (iii) is its worst-first step.
- **Pipeline seeding from pre-window announcements — DEFER to owner
  (§6 Option B2).** The hindcast cold-start problem: real exits landing
  2021-2025 were often *decided* before 2021 (RC-0B §c.2: 60% of PJM's and
  94% of MISO's real coal exits carried an as-of-2020 EIA-860 date), so a
  window that initializes all counters/pipelines empty structurally cannot
  recall them on time — no in-window decision rule fixes a pre-window
  decision. Seeding the pipeline state at init from vintage-≤V announced
  dates uses the announcement as a measured *revelation of the decision
  event* (the unobservable `D` made observable), not as an execution
  instrument — the exit still requires the economic screen's annual
  re-confirmation and executes on the pipeline's own `L_f` clock, so the
  measured 43-75% announcement non-execution rate (§c.3) is carried by the
  re-confirmation, not ignored. Forward analogue (rule 13): at any forecast
  start, currently-announced exits are known and would seed identically;
  reversal-by-instrument stays the registry's job. This is admissible under
  RC-0B §c.4 R1 (the schedule is "admissible information but not an
  execution instrument" — seeding the decision state is precisely the
  information use). It is also a real scope extension of R1's grading
  intent, so it ships only as a separately-gated flag with its own A/B leg,
  and the owner rules on it explicitly.

### 3.6 The composite recommendation — R-NEW (decision/execution pipeline)

One rule assembled from the graded components; **no new tuned parameter**:

1. **Uniform decision.** A unit whose attainable margin fails the GFC bar
   at one annual screen (the identical `net_revenue < going_forward_cost`
   comparison, unchanged basis) becomes DECIDED — it enters the exit
   pipeline with `decided_year` stamped. No per-fuel decision threshold
   exists. (§3.1 degenerate form; open DOF `D` ledgered, §5.)
2. **Joint competition at pipeline entry.** All newly-failing units across
   ALL fuels compete in the same year: pipeline admission is capped by the
   existing accredited adequacy requirement (post-pipeline firm capacity ≥
   `peak × (1 + PRM_iso)`, evaluated on the schedule of pending exits), and
   retention picks cheapest-firm-adequacy first — the EXISTING floor
   machinery and metric, now operating on one shared eligible set instead
   of a fuel-partitioned one. Ordering within admission is worst-first
   margin depth (§3.3). Removes defects 2 and 3.
3. **Soft latch while pending.** A pipelined unit is re-screened annually;
   it leaves the pipeline ONLY if its margin clears the same bar
   (`net_revenue ≥ going_forward_cost`) at a later screen. No band, no new
   parameter. This matches the measured schedule behavior (§a.3/§c.3:
   stated dates execute as-stated or are reversed — the reversal mode
   exists and is common, so a hard irrevocable latch would over-retire;
   economic recovery and policy rescue are the two real reversal channels,
   and the second is already the registry's). Removes defect 4's
   reset-on-any-blip while keeping a genuine recovery exit. Weakens
   defect 5 to its economically-correct residue: a price recovery cancels a
   pending exit only if it actually restores that unit's viability.
4. **Execution after the identified lag.** A unit still pipelined at
   `decided_year + L_f` deactivates then, with `L_f` = the §a.3 per-fuel
   medians (coal 3, gas_ct 2, gas_st 1, oil 1, gas_cc 1, nuclear held 3,
   ccs = gas_cc). It dispatches normally until then (announced-but-
   operating, as real units do). Coal's persistent-loss timing is
   byte-equivalent to the adopted D1=3 counter (decided end of loss year
   `y`, gone start of `y + 3` — exactly the counter's `y..y+2` streak →
   absent `y+3`), so the RC-D1 identification and its timing survive; the
   unidentified gas_st/oil/gas_cc totals move 2/2/3 → identified 1/1/1
   (a rule-14 measured-over-estimate swap, LOYO-scored per §4).
5. **Reliability floor at execution, unchanged.** The existing
   `_apply_reliability_floor` remains the final backstop when exits
   realize (double protection is consistent: entry-cap plans the pipeline
   on schedule information; the floor guards realized-year adequacy).
6. **Ledger attribution.** Pipeline events are recorded (decided /
   re-confirmed / reversed / executed, with years) so recall/false-retire
   scoring and the D-2-style attribution can see the decision and the
   execution separately — a recorder extension FF-1A owns.

**Retired mechanisms (rule 19/26).** The per-fuel `retirement_years_*`
DECISION thresholds are superseded (fields re-semanticized to execution
lags or replaced by `retirement_execution_lag_*`; FF-1A keeps the legacy
counter reachable behind a `retirement_rule` gate for byte-identity of
untouched configs, per its charter). `staged_oversupply_thinning` /
`staged_thinning_max_gw_per_year` are fully superseded by the lag pipeline
(the same physical queue, now carried once); recommend deletion at the flip
commit — deleted, not zeroed (rule 26).

**Honest limits, stated in advance.** (a) If the screen's revenue level says
a fuel is under water when reality kept it whole, R-NEW will still exit some
of it — the redesign fixes ORDER and COMPOSITION races, not signal level;
T-R10 adjudicates, and any surviving gas_st-type false-retire routes to the
revenue lane (BLK-6/BLK-9, RD-4), never to a fuel-specific patch. (b) PJM's
in-window coal recall may not recover under ANY admissible in-window rule:
the probe margins say model-PJM coal was profitable in most steps, and the
real exits were largely pre-window decisions (§3.5 seeding, Option B2) at a
bar RD-4 may yet raise (the §b.3 PJM coal break-even is ~92 $/kW-yr vs the
current 58.5; the oscillating 24-142 trace straddles 92, not 58.5). Both
causes are outside this rule's scope and are named so FF-1A's measurement
is read correctly.

---

## 4. (c) Pre-registered acceptance — T-R battery unchanged + T-R10 + LOYO

**The existing battery is unchanged and imported by reference:** T-R1, T-R2,
T-R3, T-R4, T-R5(-inv), T-R7 (and T-R8/T-R9 where already chartered) exactly
as pre-registered in `forecast-retirement-calibration-plan-2026-07.md` §3.
**No band is widened, restated, or re-derived.** Raw AND IS-2020 reported
side-by-side everywhere (RC-0B §c.5).

**NEW — T-R10, the no-inversion guard** (registered here, before any FF-1A
solve, from the D1 probes that PRECEDE the redesign — pre-registration in
the rule-22 sense):

- *Definitions.* Per probe leg (ISO × window): `A_f` = actual
  economic-channel thermal exits by fuel (RD-5-fixed
  `capacity_actuals_*.csv`, ≥300 MW unit grain — the recall population's
  existing grain, no new number; channel ownership per RC-0B §c.4 R1: all
  fossil exits belong to the economic screen). `first_mover` = the fuel of
  the earliest model economic-channel exit event (minimum calendar year;
  ties broken by largest MW in that year).
- **T-R10a (gate):** FAIL iff `A_{first_mover} = 0` — no fuel with zero
  real exits in the window may be the first-moving economic exit.
- **T-R10b (gate, composition corollary):** FAIL iff any fuel with
  `A_f = 0` accumulates > 1 GW of model economic-channel exits in the
  window. Rationale line: the 1 GW line is anchored between the two
  already-measured exemplars that motivated this memo — the MISO D1=1
  false-retire PASS (0.874 GW) and the D1=3 gas_st FAIL (8.643 GW) — both
  measured before the redesign existed, consistent with the T-R2
  half-to-2× band philosophy. It is registered now and never moves.
- *Scope:* every FF-1A leg and every subsequent probe/keeper the flip
  decision cites; reported per ISO-window in raw and IS-2020 modes.

**LOYO (rule 22).** Scorer-side leave-one-year-out folds within 2023-2025,
the D1-findings §6 method: every T-R verdict flip attributable to the
redesign (vs the committed D1=3 probes as BEFORE legs) must hold in ≥ 2/3
folds; a regression robust across folds BLOCKS, and is a finding — never a
band to widen. In-sample gain with held-out degradation is overfitting, not
skill.

**Discipline clauses.** The D1=3 probe legs are the BEFORE legs (already
committed; never re-solved). 2022 stays bridged-never-solved; no holdout
year is touched (rule 22 / plan §2.3). Expected outcomes in this memo
(e.g., "the latch should restore MISO coal's wave") are hypotheses; FF-1A's
MEASURED columns are the only PASS evidence (RC-2B §0 discipline).

---

## 5. (d) Identification plan — every parameter, its source, and the open DOFs

| Parameter (proposed) | Value | Identification source | Status |
|---|--:|---|---|
| `retirement_execution_lag_coal` | 3 | RC-0B §a.3 lag table: cap-weighted & ≥300 MW median announcement→deactivation, left-censored ⇒ conservative floor. Same identification as the adopted D1=3 — survives intact. | **IDENTIFIED** (re-derives only on EIA-860 vintage update, rule 23) |
| `retirement_execution_lag_gas_ct` | 2 | §a.3 median 2 (n=161 units / 2.9 GW) | **IDENTIFIED** |
| `retirement_execution_lag_gas_st` | 1 | §a.3 median 1 (n=53 / 8.1 GW) — replaces the consistent-but-unidentified 2 | **IDENTIFIED** (rule 14: measured over estimate; LOYO-scored) |
| `retirement_execution_lag_oil` | 1 | §a.3 median 1 (n=242 / 2.4 GW) | **IDENTIFIED** |
| `retirement_execution_lag_gas_cc` | 1 | §a.3 median 1 — small sample (n=26 / 1.2 GW), flagged | **IDENTIFIED-WEAK** (owner may hold at gas_ct's 2 only by rejecting the measurement explicitly; recommendation: adopt 1, rule 14) |
| `retirement_execution_lag_nuclear` | 3 | §a.5: n≈2 (IP3, Palisades, both off-sheet), suggests L ≥ 3-4 but is not identification | **OPEN DOF** (hold current 3; T-R7 guards the channel regardless) |
| `retirement_execution_lag_gas_cc_ccs` | =gas_cc | no CCS retirement exists anywhere (§a.4) | **OPEN DOF** (inherit) |
| Decision persistence `D` | 0 extra years (decide at first failing screen) | UNOBSERVABLE (RC-0B §a.1: needs unit P&L histories that exist in no on-disk source). Chosen by parsimony + the flat-expectation NPV reading (§3.1), NOT by data. | **OPEN DOF, ledgered.** Never tunable against a residual (rule 13); future identification requires an owner-authorized new data source (e.g., FERC Form 1 / earnings-call intake), filed as a possible RD row — not assumed. |
| Soft-latch reversal bar | = the existing GFC bar (no new value) | §a.3 slippage ≈ 0 + §c.3: announced exits execute as-stated or reverse outright (43-75% of MW by fuel) — a reversal channel must exist and symmetric re-use of the identified bar adds no DOF | **NO NEW PARAMETER** |
| Depth-ordering metric | shortfall $/kW-yr (or the floor's $/firm-MW-yr) | computed from existing screen quantities | **NO NEW PARAMETER** |
| Pipeline entry adequacy cap | existing `PLANNING_RESERVE_MARGIN_BY_ISO` + `accredited_firm_capacity_mw` | reused, unchanged | **NO NEW PARAMETER** |
| Throughput/rate cap | *not armed* | would double-count the queue the lag pipeline carries (rule 19; RC-0B §a.6) | **ABSENT** (staged thinning superseded → deletion at flip, rule 26) |
| Option B2 seed set (if adopted) | vintage-≤V announced dates | EIA-860 vintage history (the §c.2 derivation), V = the run's information cutoff | **IDENTIFIED-IF-ADOPTED** (separately gated; own A/B leg) |
| GFC bar / FOM multipliers | unchanged | existing citations; RD-4 ACR reconciliation pending (RC-0B §b protocol untouched) | out of scope here |

**DOF-ledger summary:** the redesign carries exactly two open DOFs (`D` and
nuclear/ccs lags — all held, none tuned) and RETIRES seven fitted-adjacent
integers (the per-fuel decision thresholds and the staged-thinning pair) in
exchange for five identified lags. Net DOF count and identification quality
both improve; every remaining free choice is ledgered with its
non-identifiability stated.

---

## 6. Owner-decision box

**D1 — the decision rule** *(gates FF-1A; nothing lands without this call)*:

- **Option A — status quo** (per-fuel consecutive-loss counters, D1=3 as
  shipped). Honest only as a holding pattern: the inversion is measured,
  LOYO-robust, and blocks every capacity-market flip (D1 findings §7-1,
  RC-2B). Re-opens nothing; leaves plan §1.2-1 open indefinitely.
- **Option B — R-NEW (§3.6), RECOMMENDED**: uniform decision + joint
  entry competition + soft latch + identified per-fuel execution lags +
  floor unchanged. *Re-opens:* FF-1A must re-measure the full battery (PJM
  + MISO curve-ON probe legs at HEAD + the ERCOT composition leg — T-R3's
  reproduction values become BEFORE legs to re-establish since gas_st/oil/
  gas_cc totals shorten); BLK-10 re-measured for free; the evolution-ledger
  reason vocabulary gains pipeline events (recorder change, FF-1A);
  `scenarios.py` field re-semantics ripple into run_config comparisons
  (old/new configs are not field-compatible — the gate keeps byte-identity
  for legacy mode); the flip memo's §5 spec is superseded by FF-1A's
  measurement plan.
- **Option B2 — B + pre-window pipeline seeding** (§3.5), as a separately
  gated flag with its own A/B leg. *Re-opens:* the hindcast information-set
  discipline gains a new admissible input class (announcement-as-decision-
  revelation); IS-2020 scoring definitions need one clarifying sentence
  (seeded exits grade as economic-channel recalls, not announced-channel);
  the RC-0B §c.4 R1 ruling gets an owner-signed amendment. Without B2, PJM
  in-window coal recall likely stays near 0 for the §3.6 "honest limits"
  reasons — measured, that is a finding about the window, not the rule.
- **Option C — (iii) alone on the existing counters** (minimal diff: joint
  depth-ordered thinning, thresholds untouched). Fixes composition among
  the co-eligible only; the MISO 2023 set still excludes coal, PJM's
  elimination untouched. Not recommended; listed for completeness.
- **Option D — hysteresis band**: REJECTED (§3.4, unidentifiable `h`).

**D2 — staged thinning disposal** (only if B/B2): delete
`staged_oversupply_thinning` + `staged_thinning_max_gw_per_year` at the
flip commit (rule 26) or keep gated-off one more wave. Recommendation:
delete at flip; the pipeline carries the queue (rule 19).

**D3 — the weak-sample lags**: adopt measured gas_cc = 1 (recommended,
rule 14) or hold 2 pending a larger sample — an explicit measurement
rejection either way, recorded in the ledger.

**Recommendation: B, with B2 presented but not bundled** — B is fully
identified and self-contained; B2 changes what the hindcast is allowed to
know and deserves its own yes/no. D2 delete-at-flip; D3 adopt-measured.

---

## 7. Sources (field survey, §2)

- EPA, *Documentation for EPA's Power Sector Modeling Platform v6 — Summer
  2021 Reference Case*: [Ch. 2 Modeling Framework](https://www.epa.gov/system/files/documents/2023-02/Chapter%202%20-%20Modeling%20Framework.pdf),
  [Ch. 4 Generating Resources](https://www.epa.gov/system/files/documents/2021-09/chapter-4-generating-resources.pdf)
  (§4.2.4 committed-retirement constraints + economic-retirement options;
  §4.2.8 life-extension retire-or-invest), [documentation hub](https://www.epa.gov/power-sector-modeling/documentation-epas-power-sector-modeling-platform-v6),
  [Post-IRA 2022 Reference Case](https://www.epa.gov/power-sector-modeling/documentation-post-ira-2022-reference-case).
- NREL, *Regional Energy Deployment System (ReEDS) Model Documentation*:
  [2019 edition (fy19osti/72023)](https://docs.nrel.gov/docs/fy19osti/72023.pdf),
  [2020 edition (fy21osti/78195)](https://docs.nrel.gov/docs/fy21osti/78195.pdf),
  [OSTI record](https://www.osti.gov/biblio/1788425) (coal CF-threshold
  retirement construct; "does not include endogenous economic retirements").
- GenX: [Model introduction](https://genxproject.github.io/GenX.jl/stable/Model_Concept_Overview/model_introduction/),
  [GenX.jl repository](https://github.com/GenXProject/GenX.jl), MIT Energy
  Initiative, [*Enhanced Decision Support for a Changing Electricity
  Landscape* (2017)](https://energy.mit.edu/wp-content/uploads/2017/10/Enhanced-Decision-Support-for-a-Changing-Electricity-Landscape.pdf)
  (retirement as co-optimized decision variables).
- Energy Exemplar, [PLEXOS LT Plan documentation](https://portal.energyexemplar.com/unified-help/plexos-desktop/Main.LTPLan.html)
  (NPV-minimizing integer build/retire; planned vs economic retirement).
- Energy Exemplar, [Aurora](https://www.energyexemplar.com/aurora); NW Power
  & Conservation Council, [2021 Power Plan AURORA model writeup](https://www.nwcouncil.org/2021powerplan_aurora-model/)
  (iterative NPV market-value vs avoidable-cost retirement, MIP LT
  expansion); [Idaho Power AURORA overview](https://docs.idahopower.com/pdfs/AboutUs/PlanningForFuture/irp/AURORA_Overview.pdf).
- In-repo: RC-0B, RC-1A-D1, RC-2B memos as cited inline;
  `model/capacity.py::apply_economic_retirements`; Monitoring Analytics /
  PJM Manual 18 avoidable-cost framing per RC-0B §b (RD-4 pending).

---

*Produced 2026-07-17 (FF-0C memo session). No LP solved; no code, default,
parameter, or dashboard touched; no holdout year read or scored (rule 22).
Gates FF-1A: implementation requires owner sign-off on §6 (D1-D3). The
RC-0B §a.3 lag identification is preserved verbatim as the execution-lag
table; the coal = 3 total and its citation survive unchanged.*
