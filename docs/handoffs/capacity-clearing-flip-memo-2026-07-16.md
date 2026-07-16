# Capacity-market clearing — per-ISO flip memo (RC-2B, 2026-07-16)

**Charter.** F-8 of the flip-gate lane
(`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` §2.3): grade the
§2.1 flip gate per ISO (PJM / MISO / NYISO / NEISO / CAISO), state the honest
failure modes of flipping now vs waiting, inventory the residuals with their
owners, and put the decision to the owner. **Memo only — no LP solved, no code or
parameter changed, nothing registered on any dashboard, no holdout year read or
scored (rule 22).** Inputs: RC-1A (`position-calibration-findings-2026-07-16.md`
— the ⛔ probe measurement), RC-2A (`ercot-retirement-composition-2026-07-16.md`),
RC-0B (`retirement-dof-identification-2026-07-15.md`), RC-1C
(`capacity-price-validation-2026-07-16.md`), RC-1D
(`nyiso-neiso-capacity-pairing-adjudication-2026-07-15.md`), the gap register
(`docs/gap-register-2026-07.md` §3.9/§3.10).

**Verified on `origin/main` (2026-07-16, HEAD `a29e6e5`):**

- `retirement_years_coal == 3` (`scenarios.py:283`) — RC-D1 merged (PR #2335,
  commits `9a3e4eb` adopt + `4cc6887` cite). Cited to the RC-0B §a.3 lag table
  only; per rule 19 the threshold now carries the D+L deactivation total and
  `staged_oversupply_thinning` stays default-off.
- The per-ISO clearing gate and curve-eligibility registry are live
  (`constants.py::CAPACITY_CURVE_ELIGIBLE_BY_ISO`: PJM/NEISO/MISO/CAISO `True`,
  **NYISO the one explicit `False`** — R5a owner sign-off pending). Every
  clearing default remains **OFF** for every ISO; this memo changes nothing.

**Bottom line first (the honest one): HOLD all five ISOs.** No ISO has a
measured-PASS on gate items 3–4 under the configuration that would actually
ship (`retirement_years_coal = 3`), because the only position/skill measurement
that exists was taken at the superseded value (D1 = 1) and the owner deferred
the re-probe. The recommendation is **hold, adopt-and-re-probe**: the single
unblocking step is re-running the RC-1A probe legs (PJM + MISO, probe legs
only — the BEFORE legs are D1-invariant) at D1 = 3 on the HEAD instruments
(§5). MISO is the closest to a flip; PJM is one coupled defect (BLK-10) behind
it; NYISO and NEISO are blocked on things a re-probe cannot fix; CAISO has no
decision to make.

---

## 0. The central caveat: every position/skill number in this memo was measured at D1 = 1

> **RC-D1 moved `retirement_years_coal` 1 → 3 on 2026-07-16, but the RC-1A
> curve-ON probe was NOT re-run (owner decision, RC-0B §d D1 box: "RC-1A
> re-probe SKIPPED", LOYO "deferred by owner"). Every position, recall,
> false-retire, payment, and invariant number quoted from RC-1A §1–§5 in this
> memo is therefore a D1 = 1 measurement of a configuration that no longer
> exists on main.** This memo grades two columns per gate item and never mixes
> them:
>
> - **MEASURED (D1=1)** — RC-1A §3/§5 verbatim. The only empirical evidence.
> - **EXPECTED (D1=3)** — reasoned from RC-1A §4.1's wave mechanism and RC-0B
>   §a; every such statement is labeled *"expected, not measured — re-probe
>   deferred by owner"* and is **never graded PASS**. An expected improvement
>   is a hypothesis, not evidence.

Why the EXPECTED column carries real uncertainty, stated adversarially before
any ISO is graded:

1. **A higher threshold delays the wave; it does not, by itself, thin it.**
   RC-1A §4.1's mechanism is that `apply_economic_retirements` exits the
   *entire* loss-cohort the year its counter hits the threshold. If the
   cohort's loss years run in lockstep (they do under curve-ON at a long
   position: the payment zeroes for everyone in the same year), D1 = 3 moves
   the same-sized wave ~2 years later rather than damping it. The damping
   RC-1A actually *measured* came from the **instrument grain** (MISO seasonal
   vs annual: false-retire 4.03 → 0.874 GW, second wave 6.91 → 3.76 GW), not
   from the threshold. Whether D1 = 3 damps, merely delays, or re-times the
   overshoot into a different year is exactly what the deferred re-probe would
   have measured.
2. **The 2021–2025 window is short, and D1 = 3 eats two of its steps.** Under
   curve-ON the first coal loss year is 2021; at D1 = 1 the first wave landed
   in the 2022 bridge and the coupled loop had 2023–2025 to walk the position
   into the priced region. At D1 = 3 the first wave cannot land before
   ~2024 — so the loop gets one to two in-window steps instead of three to
   four. The plausible failure mode is not a repeat of the measured overshoot
   but a new **in-window undershoot**: cumulative exits land lower, the 2025
   position stays long, and items 3–4 revert *toward* the BEFORE leg's
   never-in-region state. Both overshoot-later and undershoot-in-window are
   live hypotheses; neither is measured.
3. **The D1 adoption's own LOYO was skipped.** Gate item 4 requires any
   mechanism-driven verdict flip to be scored leave-one-year-out within
   2023–2025 before the flip commit. RC-0B §d records that no hindcast LOYO
   was run for D1. The re-probe must carry it (§5), or the flip would ship a
   threshold whose in-sample/held-out behaviour was never split.

---

## 1. §2.1 gate grading, per ISO

Gate items (plan §2.1): **1 Basis** (published accreditation), **2 Instrument**
(per-delivery-year published curve), **3 Position** (in the priced region when
the real market priced, out when it didn't), **4 Skill** (recall/false-retire
strictly improve, additions not degraded, LOYO on mechanism flips),
**5 Plumbing** (per-ISO gate).

### 1.1 PJM

Probe recap (MEASURED, D1=1 — RC-1A §1): coal economic exits 0 → 9.913 GW
(actual 6.885; +44 % overshoot), recall 0 → 76 %, thermal 14.02 GW (actual
11.121), false-retire 4.097 → 7.125 GW raw / 0 → 3.028 GW IS-2020, positions
1.017–1.113 (BEFORE) → 0.977–1.078 (probe), 2024 pays 112 $/kW-yr vs cleared
10.6, 2025 lands 0.977 vs auction 1.007 (miss 0.030 vs band ±0.028, short
side), backstop builds 6.43 GW gas_ct in 2025 (BLK-10). I5/I13 PASS both legs.

| # | Item | MEASURED (D1=1) | EXPECTED (D1=3) — *expected, not measured; re-probe deferred by owner* |
|---|---|---|---|
| 1 | Basis | **PASS** — N-5 R1–R4 closed (UCAP anchor, published-FPR requirement, ELCC-class ledger, basis-consistent payment). D1-invariant. | unchanged (threshold does not touch the basis) |
| 2 | Instrument | **PASS** — 2021/22–2025/26 vintages carry published VRR shapes, workbook-reconciled to ≤0.1 % (RC-1A §0-2); 2026/27 P-2A-validated. D1-invariant. | unchanged |
| 3 | Position | **OPEN** — the loop closes end-to-end (the §2.2 circularity is broken: $0 → exits → position walks into the region) but overshoots: 2024 in-region a year early (pays 112 vs 10.6 cleared), 2025 0.030 past the target from the short side (band ±0.028), driven by the undamped 6.43 GW second wave + the 6.43 GW backstop over-fire (BLK-10). T-R4 FAIL. | Waves shift ~2 yr later; the 2024-early-entry and short-side-2025 misses plausibly resolve, but the loop then has 1–2 in-window steps — the position may instead stay long through 2025 (undershoot; T-R1d could fail from the other side). BLK-10's deficit shrinks only if the wave lands smaller, which the threshold alone does not guarantee (§0-1). **Stays OPEN either way until measured.** |
| 4 | Skill | **OPEN** — recall 0 → 76 % ✓, enumerated additions not degraded ✓ (gas_cc +41 % → −6 %), **but** false-retire strictly degrades (4.1 → 7.1 raw / 0 → 3.0 IS-2020, entirely the coal overshoot) and gas_ct 0 → 8.43 GW is a new miss (backstop, BLK-10). | Later, possibly fewer in-window coal exits: false-retire plausibly improves, recall plausibly drops (the second cohort's exits fall past 2025). Net sign unknown. The D1 LOYO clause is **unsatisfied** (§0-3) — item 4 cannot PASS on expectation regardless. |
| 5 | Plumbing | **PASS** — per-ISO gate end-to-end verified this probe (`{'PJM': True}`, scalar off, no cross-ISO leak). | unchanged |

**PJM: 3 measured-PASS (items 1, 2, 5), 2 OPEN (items 3, 4).** Both OPEN items
were measured only at D1 = 1 and both blockers (wave damping, BLK-10) are
coupled to the value that changed.

### 1.2 MISO

Probe recap (MEASURED, D1=1, seasonal grain — RC-1A §2): coal 0 → 11.809 GW
(actual 10.934; **+8 %**), recall 76 %, false-retire 0.874 GW **band-PASS raw
and IS-2020**, thermal −17 %, 2025 CO₂ error +14 % → +5 %, gas_cc additions
+133 % → −100 % (3.9 GW under), solar −68 % → −36 %, wind unchanged (never sees
the curve — BLK-7), backstop 0.01 GW. Positions 1.128–1.175 (BEFORE) →
1.010–1.038 (probe): long years stay out of the region ✓, but the 2025
shortage year also stays out (pays 24.5 $/kW-yr vs 243.3 cleared at cap).

| # | Item | MEASURED (D1=1) | EXPECTED (D1=3) — *expected, not measured; re-probe deferred by owner* |
|---|---|---|---|
| 1 | Basis | **PASS** — keep-and-verify per plan (EFORd pairing ~consistent). | unchanged |
| 2 | Instrument | **PASS-leaning-OPEN** — the seasonal RBDC grain landed (RC-1C) and the registered probe priced on it; Pass-1 seasonal sum reproduces net-CONE to −0.9 % with the summer-at-cap concentration. Two residuals: (i) the **probe's instrument provenance is ambiguous** (§3, row M-2): RC-1A's own §2 prose says the pre-RBDC years ran hold-first on PY2025-26, but main's vertical-at-CONE pre-RBDC vintages (`constants.py` MISO block, landed with RC-1C merge `ad91468`) are an *ancestor* of the probe-registration commits, and the probe's $0 payments at 2023/2024 positions 1.038/1.010 match the vertical step, not a sloped curve near its zero-cross — the report and the tree disagree about what was priced; (ii) PY2026/27 seasonal parameters when published (RD-3 remainder). | The re-probe on HEAD resolves (i) at zero extra cost — it *is* the era-correct-instrument re-measurement. |
| 3 | Position | **OPEN** — one-sided: long years correctly out, but the 2025 shortage year is also out (1.035, pays 24.5 vs 243 at cap). The residual is the fleet path (+8 % exits still leave 2025 long) plus the demand-side moves a single seasonal vintage cannot carry. | D1 = 3 pushes exits later → the 2025 position is expected *longer*, i.e. the one-sidedness **worsens in-window**, not improves. Stays OPEN. |
| 4 | Skill | **OPEN-leaning-PASS** — recall 0 → 76 % ✓, coal +8 % ✓, false-retire 0.874 GW band-PASS (raw + IS-2020) ✓, CO₂ +5 % ✓, solar improves ✓; wind unchanged (routed to RC-0C, not a curve defect); gas_cc over-corrects to −100 %; the only strict degradation is 0 → 0.874 GW against a baseline that retired nothing at all. | First wave shifts to ~2024; cumulative in-window coal plausibly drops from +8 % toward the band floor (T-R2a band [3, 22] GW likely still holds via the first wave alone). Annual-grain diagnostic (over-retire +37 % at D1=1) shows the dynamics are instrument-sensitive — the threshold interaction is unmeasured. LOYO unsatisfied (§0-3). |
| 5 | Plumbing | **PASS** — `{'MISO': True}` composed with the RC-1C seasonal branch + eligibility gate. | unchanged |

**MISO: 2 measured-PASS (items 1, 5), 1 PASS-leaning-OPEN (item 2), 2 OPEN
(items 3, 4).** MISO is the closest ISO to a flip — its D1=1 retirement record
is near pass-quality — but that is precisely the configuration that no longer
exists, and its item-3 one-sidedness is expected to *worsen* under D1 = 3.

### 1.3 NYISO — curve-INELIGIBLE (code-enforced), R5a memo-only

NYISO cannot flip regardless of this memo:
`CAPACITY_CURVE_ELIGIBLE_BY_ISO["NYISO"] = False` (RC-1C, enforced in the
pricing seam, not prose) — R5a was **adjudicated but not implemented** (RC-1D
§2–3, Option D stands pending owner sign-off).

| # | Item | Grade | Evidence |
|---|---|---|---|
| 1 | Basis | **OPEN** — the requirement pairing is the known broken half: ICAP-stated IRM (24.4 %) against UCAP-counted supply with a ratio-1.0 fallback → position understated ~5–7 %, curve would **over-pay** if enabled. No filed constant exists to intake (NYISO recomputes the translation factor twice per Capability Year from the qualified fleet); the same-year model-derived factor is algebraically degenerate in this repo's call graph (RC-1D §2.3 — `accredited_firm_capacity_mw` cancels out of the position). Owner decision A (lagged model-derived) vs B (NYCA-wide static proxy; needs NYSRC Appendix D Table D.1.1, MANUAL DOWNLOADS) is unresolved. |
| 2 | Instrument | **PASS (transcription), with sparse years** — per-vintage Pass 1B reproduces 2023/24 and 2024/25 cleared spot and shape to 0 % on each year's own ARV (RC-1C refresh §3.3); 2021/22–2022/23 publish no ARV/cap and are honestly non-scoreable (flat anchor, no invented interpolation); 2025/26 locked (rule 22). A faithful instrument does not make NYISO eligible (RC-1C says this verbatim). |
| 3 | Position | **OPEN, unmeasured** — no curve-ON probe exists (RC-1A ran PJM+MISO only, correctly: R5a first). Worse, the position NYISO would be measured at is itself mis-based until item 1 closes — a probe run today would measure the wrong quantity by ~5–7 %. |
| 4 | Skill | **OPEN, unmeasured** — fixed-mode hindcast only: fossil recall −100 %, gas_ct +5494 % (the 4 GW backstop block at the near-zero seed margin — the same I12 de-firm→overshoot signature BLK-10 now names). No probe evidence. |
| 5 | Plumbing | **PASS** — the per-ISO gate and the eligibility registry both exist and work; indeed the plumbing is what enforces NYISO's ineligibility. |

**NYISO: HOLD with named blocker.** The blocker is not the re-probe — it is the
R5a owner decision (A vs B) *then* a first curve-ON probe on the corrected
pairing. Flipping now would put a faithful curve on a mis-measured position and
systematically over-pay.

### 1.4 NEISO — registry-ELIGIBLE, but nothing is measured

Correction to this task's framing: the prompt groups NEISO with NYISO as
"curve-INELIGIBLE (R5a memo-only)". That is not the state on main: **NEISO is
registry-eligible** (`CAPACITY_CURVE_ELIGIBLE_BY_ISO["NEISO"] = True`) because
its pairing audit R5b was **implemented**, not memo-only
(`THERMAL_ACCREDITATION_BASIS_BY_ISO["NEISO"] = "claimed_capability"`, RC-1D §1
— QC has no EFORd term; outage risk is priced ex post via PFP). NEISO's flip
blockers are different, and in one way worse: nothing about its position or
skill has ever been measured.

| # | Item | Grade | Evidence |
|---|---|---|---|
| 1 | Basis | **OPEN-leaning-PASS** — supply side closed by R5b (claimed-capability, cited to Market Rule 1 §III.13.1.2.2.1.1); the **requirement side is still a stand-in**: `PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"] = 0.157` is a NERC reference-margin placeholder flagged `needs-citation`, not ISO-NE's own Net ICR (RC-1D §1.3 explicitly scoped it out). Item 1 requires *both* halves on the ISO's own published basis. |
| 2 | Instrument | **OPEN-leaning-PASS** — shape exact every scored year (cap fraction 1.600 = published; P-2A "best-behaved curve"), and per-delivery-year FCA anchors 2020/21–2027/28 now sit in `MARKET_DESIGN_VINTAGES`; but the per-vintage Pass-1B **re-score has not been run** (the RC-1C refresh regenerated NYISO/MISO only; the committed NEISO numbers still carry the frozen-FCA18-anchor ±11–24 % residual). Forward-story caveat: the FCM sunsets after CCP2027-28 (final FCA held Feb 2024) — the instrument this gate validates has a dated end, and the Capacity Accreditation Reform successor is unresearched. |
| 3 | Position | **OPEN, unmeasured** — **no NEISO capacity hindcast exists at all** (no bundle in `results/hindcast/`; the only NEISO evolution evidence is the 25-yr equilibrium run: 0 MW thermal retired in 25 years, T2.4c). There is no position to grade. |
| 4 | Skill | **OPEN, unmeasured** — same. |
| 5 | Plumbing | **PASS** — generic per-ISO gate; NEISO was the original motivating case (P-2A §7). |
| — | | | |

**NEISO: HOLD with named blockers.** A flip would be evidence-free: before
NEISO can even be graded, it needs (i) the Net ICR requirement citation,
(ii) the per-vintage Pass-1B re-score, and (iii) a first fixed-mode + curve-ON
hindcast pair — a chartered probe session, not a re-run of anything existing.

### 1.5 CAISO — documented no-op

No decision exists. CAISO has **no demand curve** — bilateral RA with the fixed
90 $/kW-yr proxy (CPM soft-offer-cap-cited) in *both* modes;
`capacity_price_per_firm_mw_yr` returns the fixed anchor even with the gate on,
so `capacity_market_clearing` is a **no-op for CAISO** by construction (its
eligibility-registry `True` is moot, as the registry comment says). It remains
the documented low-fidelity member of the registry. Nothing to grade; nothing
to flip. *(Full stop, per the charter.)*

---

## 2. Failure modes: flip now vs wait

The adversarial frame first: **a $0-paying curve at the wrong position and an
always-paying constant are both wrong.** The BEFORE legs pay every fossil class
1.26–4.92× its going-forward cost in every year (BLK-9 — exit arithmetically
impossible; PJM pays "full freight" even in years the real auction cleared near
floor). The D1=1 probe did not merely under-pay: **in the one year its PJM
position entered the priced region (2024) it over-paid the real clearing price
by ~10× (112 vs 10.6 $/kW-yr)** — a curve at the wrong position is not a
conservative error, it is a different wrong answer. The choice is not
"imperfect curve vs safe status quo"; it is which wrongness is structurally
closer to the market, and per rule 1 the curve is — *once its position path is
measured under the shipping configuration.*

**PJM — flip now:**
- *Measured risks (D1=1):* coal overshoot +44 % (false-retire 7.1 raw / 3.0
  IS-2020); 2024 in-region a year early paying 112 vs 10.6; 2025 short-side
  miss (0.977 vs 1.007); the coupled BLK-10 backstop over-fire (6.43 GW gas_ct
  in one step, +1784 %). These are the live risks the task names, and they are
  measured, not hypothetical.
- *§2.2 mass-first-wave risk — what the probe measured:* **I5 (no
  retire-reenter) and I13 (no sawtooth) PASS on every leg** — at this window
  length the coupled system did not cobweb. But the overshoot is plainly
  visible in the position trace (1.078 → 1.006 through the priced region in
  one step), and I13's PASS at 5 years says nothing about a 25-year horizon.
  With D1 = 3 the wave dynamics are **unmeasured** (§0-1: the threshold delays;
  the measured damping came from instrument grain). `staged_oversupply_thinning`
  is now default-off *by rule-19 design* (the threshold carries the queue), so
  if the D1=3 wave is still lumpy there is no rate cap behind it.
- *Waiting cost:* fixed mode retires zero fossil forever (−63 % retirement
  bias), overpays every fossil class, and the position error feeds every
  downstream forecast (the ~1/3 residual PJM curve-position error).

**MISO — flip now:**
- *Measured risks (D1=1, seasonal):* the retirement record is close to
  pass-quality, but the flipped market would **under-price shortage**: 2025
  pays 24.5 where the real PRA cleared 243.3 at cap — a 10× miss in the one
  year that mattered, from the long side. gas_cc entry over-corrects to −100 %
  (3.9 GW *under* actual): the flip trades the fixed mode's over-build for an
  under-build. Wind does not respond at all (BLK-7 — VRE earns zero capacity
  revenue in the entry screen), so the curve moves only half the additions
  problem.
- *Grain/threshold sensitivity, measured:* the same probe on the annual grain
  over-retired +37 % with false-retire FAIL — the coupled dynamics move a lot
  under instrument changes, and D1 = 3 is exactly such a change (unmeasured).
  Plus the instrument-provenance ambiguity (§1.2 item 2) means even the
  seasonal leg's pre-2025 pricing state is not cleanly documented.
- *Waiting cost:* the largest single capacity miss in the program (coal 0 vs
  10.9 GW) stays open in fixed mode, and the 2025 CO₂ error stays +14 % rather
  than +5 %.

**NYISO — flip now:** impossible without reverting a governance gate (the code
returns the fixed anchor). Force-flipping would put a 0 %-transcription-error
curve on a position mis-measured by ~5–7 % in the over-paying direction, on an
ISO whose fixed-mode hindcast already over-builds gas_ct by +5494 %. Waiting
costs nothing until R5a's owner decision lands — the curve cannot be
position-graded before the pairing is right.

**NEISO — flip now:** an evidence-free flip: no hindcast, no probe, no
position, no skill number, a stand-in requirement, and a per-vintage Pass-1B
never re-scored. It would also be the first flip whose instrument (the FCA) has
already held its final auction — the forward anchor policy (hold-last-vintage
past 2027/28) would be doing all the work from year one. Waiting cost: none
that is measured; the equilibrium battery's 0-MW/25-yr pathology is real but a
flip without a probe would swap it for unmeasured dynamics.

**CAISO:** no flip exists; no failure mode either way.

---

## 3. Residuals and where they live

| # | Residual | State / number | Owner / lane |
|---|---|---|---|
| R-1 | **The D1 re-probe gap — the memo's central caveat.** All position/skill evidence is D1=1; `retirement_years_coal=3` shipped without its re-probe or its LOYO. Until the RC-1A probe legs re-run at D1=3, no gate item 3/4 can be measured-PASS anywhere. | PJM items 3–4, MISO items 3–4 all conditioned on it | Flip-gate lane; unblocked by §5's re-probe spec. Owner deferred it — this memo asks to un-defer. |
| R-2 | **BLK-10 — adequacy-backstop / additions over-fire** (gap register §3.9, filed by RC-1A): PJM 2025 rebuilt the full one-pass deficit in one step (6.43 GW gas_ct, +1784 %), the proximate cause of the T-R4 short-side miss; NYISO fixed-mode +5494 % is the same signature. Coupled to the wave: **re-measure after D1, before any sizing rework is chartered** (the register row says this verbatim). | measured (D1=1) | Flip-gate lane: re-measured for free in the §5 re-probe; sizing rework only if the damped wave still over-fires |
| R-3 | **MISO instrument residuals:** (i) probe pre-2025 pricing provenance ambiguous (RC-1A prose "hold-first" vs main's vertical-at-CONE pre-RBDC vintages, which are ancestors of the probe commits and match the probe's $0 rows — §1.2); (ii) PY2026/27 seasonal RBDC parameters when published (RD-3 remainder). Neither blocks a re-probe; (i) is *resolved by* it. | doc/tree discrepancy + intake remainder | (i) §5 re-probe on HEAD; (ii) RC-0A/RD-3 intake when MISO posts |
| R-4 | **ERCOT BLK-6 screen-revenue level gap** (RC-2A §C): CT screen net-rev ≈ **1.9 $/kW-yr vs SOM ≈ 68** → residual **≈ 66 $/kW-yr co-opt-off / ≈ 51 co-opt-on** (co-opt lifts 1.9 → ~17.1); signal is **bimodal** (starved raw duals in first-wave years, 757 → 242 $/kW-yr lookahead pro-forma later — neither physical). Every absolute ERCOT exit call stays conditioned on it. No flip decision exists for ERCOT (energy-only), but this is the lane's biggest out-of-lane dependency. | measured 2026-07-16 | **G-20/G-22** (hard boundary — never absorbed here); the in-year-scarcity structural root is the correlated forced-outage availability charter (RC-2A Part D, stages 1–4, unimplemented) |
| R-5 | **Open DOF-ledger rows (RC-0B §a.4):** `retirement_years_{gas_ct,gas_st,oil,gas_cc,nuclear}` consistent-but-unidentified (hold pending data); GFC ACR reconciliation **PENDING RD-4** with the pre-registered break-even conclusion that only the MISO coal cliff (~$73.6/kW-yr bar) is plausibly reachable — the GFC fix can never close Direction 1 by itself. | ledgered open | RC-0B §b protocol fires mechanically when RD-4 lands; rule 23 (never re-derived off a residual) |
| R-6 | **R5a NYISO pairing** — adjudicated, unimplemented; ratio-1.0 fallback overstates the requirement ~5–7 %. Owner decision: Option A (lagged model-derived translation factor — recommended design target, needs an architecture session) vs Option B (NYCA-wide static proxy — needs NYSRC IRM Appendix D Table D.1.1, on MANUAL DOWNLOADS). | Option D (status quo) stands | Owner call, then a scoped RC-1D follow-up; NYISO curve-ineligible until then |
| R-7 | **NEISO gaps:** requirement-side Net ICR citation (`0.157` stand-in); per-vintage Pass-1B re-score (RC-1C refresh skipped NEISO); **no capacity hindcast exists** — a first NEISO fixed/curve-ON pair needs its own charter before items 3–4 are gradeable at all; FCM-sunset forward-anchor policy. | ungraded | Accreditation-basis lane (requirement citation); flip-gate lane (probe charter — new session, not §5's re-probe) |
| R-8 | **Entry-side non-response:** wind never sees the curve (BLK-7 / §1.4 term c) and sits on the queue-cap chunk (term e); PJM solar stayed 0 even with the price channel (term a insufficient there); MISO solar improved to −36 % purely via price. | measured (D1=1) | **RC-0C / BLK-8 lane** — routed, not tuned; explicitly *not* a flip blocker (additions bands are graded not-degraded, not solved) |
| R-9 | Scorer/invariant hygiene: PJM 2021 base-year placeholder margin (I3/I7), I12 band stale vs N-5 basis, MISO I9 storage ε-degeneracy — all pre-existing on committed sidecars. | cosmetic, none blocks | small scorer-lane cleanup ticket (RC-1A §4.6) |

---

## 4. Owner-decision box, per ISO

Decision vocabulary: **FLIP** (commit per §2.3 F-9, includes the R4 anchor
re-derivation) / **HOLD-blocked** (named blocker outside this lane) /
**HOLD-pending-re-probe** (the §5 measurement unblocks it).

| ISO | Decision | Measured-PASS gate items (D1=1) | What unblocks |
|---|---|---|---|
| **PJM** | **HOLD, pending re-probe** | 1, 2, 5 (3 of 5). Items 3–4 OPEN, measured only at D1=1, both blockers (wave, BLK-10) coupled to the changed value. | §5 re-probe: PJM probe leg at D1=3 on the published vintage shapes; re-grade T-R1/T-R4/T-R5-inv/T-R7; re-measure BLK-10; carry the D1 LOYO. If items 3–4 then measure PASS, flip per F-9. |
| **MISO** | **HOLD, pending re-probe** (closest to flip) | 1, 5 (+ item 2 PASS-leaning-OPEN). Items 3–4 OPEN; item 4 was OPEN-leaning-PASS *at D1=1* — the most flip-adjacent measured state in the program, and exactly the configuration that no longer exists. | §5 re-probe: MISO probe leg at D1=3 on the HEAD instrument (also resolves the R-3(i) provenance ambiguity); re-grade T-R2/T-R5-inv/T-R7. The item-3 one-sidedness (2025 shortage under-priced) is expected to persist or worsen — if it does, the honest verdict may be "flip with the shortage-year residual documented" vs "hold on fleet-path work"; that is a second owner call the re-probe will sharpen with a measured number. |
| **NYISO** | **HOLD, blocked** (not re-probe-unblockable) | 2, 5. Item 1 is the binding blocker (R5a unimplemented, code-ineligible); items 3–4 unmeasured *and* unmeasurable-correctly until item 1 closes. | Owner decision on R5a Option A vs B (RC-1D §3) → implement → first NYISO curve-ON probe → then grade. |
| **NEISO** | **HOLD, blocked** (evidence-free) | 5 only (items 1–2 partially closed: R5b supply basis ✓, shape ✓ — but requirement citation + per-vintage re-score open). Items 3–4 have never been measured. | Net ICR requirement citation; NEISO per-vintage Pass-1B re-score; a chartered first hindcast/probe pair. Only then gradeable. |
| **CAISO** | **No decision exists** (no-op) | n/a — no curve; the gate cannot change CAISO behaviour by construction. | Nothing. A CAISO curve would first require a market-design change in reality, not in the model. |

**Recommendation (honest, per the charter's own bar):** HOLD all five.
**No flip can be measured-justified today** — the only probe evidence was
taken at `retirement_years_coal = 1`, and a recommended flip must cite
measured-PASS gate items under the shipping configuration, which does not yet
have any. The recommended path is **adopt-and-re-probe**: D1 = 3 is already
adopted on its identification (correctly, per rules 1/13/14 — and this memo
does not second-guess the identification); the missing half is the
measurement. Run §5; RC-2B's grading then updates mechanically (the scorecard
columns are already split MEASURED vs EXPECTED for exactly this reason). The
one thing NOT to do is flip on the EXPECTED column — an
expected-but-unmeasured improvement is not a PASS, and shipping it as one
would be precisely the scoring abuse rule 22's LOYO clause and RC-0B §c.5's
dual-reporting discipline exist to prevent.

---

## 5. The unblocking step, specified: RC-1A probe legs re-run at D1 = 3

Scope (one session, rule-12 concurrency, ≤ 2 invocations, years sequential):

1. **Legs:** PJM + MISO `--capacity-market-clearing` **probe legs only** — the
   BEFORE legs are **D1-invariant** (they retire no coal at any threshold;
   RC-1A §4.1 measured this) and reproduce from the committed bundles. 2021 →
   2025 realized, 2020 vintage, 2022 bridged-never-solved (rule 22).
2. **Configuration:** HEAD defaults, nothing else armed — i.e. D1 = 3 as
   shipped, `staged_oversupply_thinning` off (rule 19), per-ISO gate
   `{ISO: True}`, HEAD instruments (PJM published pre-CIFP vintage shapes;
   MISO pre-RBDC vertical-at-CONE + PY2025-26 seasonal RBDC — which also
   settles the R-3(i) provenance question on a cleanly documented tree state).
3. **Score exactly the pre-registered battery, bands never widened:**
   T-R1/T-R2/T-R4/T-R5-inv/T-R7 + raw-and-IS-2020 side-by-side (RC-0B §c.5) +
   Pass-2 adopted-basis restatements + I5/I13 every leg. Re-measure BLK-10
   (backstop MW fired) — the gap-register row requires it before any
   backstop-sizing charter.
4. **LOYO:** score the D1-driven verdict flips leave-one-year-out within
   2023–2025 (the clause RC-0B §d deferred) before any flip commit cites the
   result.
5. **Register** on the forecast-validation dashboard only; findings appended
   to the position-calibration doc; RC-2B's §1 tables re-graded (the MEASURED
   column moves to D1=3; the EXPECTED column retires).

Cost basis: two probe legs ≈ the RC-1A probe wall-clock (its four legs ran in
one session on a 15 GiB machine; RC-2A's staged ERCOT leg was ~1h44m — these
are cheaper). The information value is the entire flip decision.

---

*Produced 2026-07-16 (RC-2B, memo session). No LP solved; no code, default,
parameter, or dashboard touched; no holdout year read or scored (rule 22).
Verified against `origin/main` HEAD `a29e6e5` (D1 = 3 at `scenarios.py:283`,
PR #2335). Successor to RC-1A/RC-2A/RC-1C/RC-1D; input to RC-3A, which must
not start without the owner's sign-off on §4 — and, per this memo's
recommendation, not before §5 runs.*
