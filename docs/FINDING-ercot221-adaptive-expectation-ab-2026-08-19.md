# FINDING — ercot-221 / ADAPTIVE-EXPECTATION STORAGE OFFER (the dynamic conduct family): Phase-0 v1+v2 FAIL recorded, Phase-1 entered on owner instruction, full-span A/B **REJECTED-AS-ARMED on G-SHED** — and the measured cause is the bootstrap starving on the missing count half

> Status: RECORD. The ercot-221 lane ran across TWO sessions: the builder
> session (inside the ercot-220 session's branch, 2026-08-18/19) pinned the
> precommit, ran Phase-0, built the mechanism, solved the control and recorded
> Amendments 1–4, then was interrupted mid-arm; the successor session (branch
> `claude/ercot-221-adaptive-expectation-xwkpk2`, 2026-08-19) completed the
> pre-registered pipeline unchanged. Keeper at start and end:
> **`2026-08-17-ercot215-arm-decontam`** (NOT-YET, {C3a-2023 −40.1 %,
> C3b-2023 0.736}, C3c ledgered CAVEAT ×3) — **keeper UNCHANGED; promotion
> was declined on this session's recommendation** (§5) and remains the
> owner's separate act on this recorded verdict.

## 0. VERDICT

**REJECTED-AS-ARMED**, mechanical under PRECOMMIT-ercot221 §4 (any gate FAIL
⇒ rejected, recorded unrewritten): **G-SHED FAILS** — the armed evening
reservation floor manufactures **one NEW 2024 load-shed hour** (hour 3066,
beside the baseline's 3067) that neither reality nor the keeper has. Every
other pre-registered gate passes (§2). The side-effect motion on the 2023
object is near-nil at full magnitude: probe C3a-2023 −30.38 → **−29.77 %**.

**The measured cause was ex-ante predicted by the precommit's own expectation
bound** ("a single adaptation pass on the model's own path should land
materially short of the ceiling"): the bootstrap **starves**. The keeper's
own 2023 price path carries **7** deep-scarcity days against reality's
**23**, so the trailing expectation tops out at P_hat = **0.37** (floor max
**$1,850**, ≥$1,000 floors in only 160 window-hours: Aug 24 / Sep 120 /
Oct 16) against the measured implied expectation **0.67–0.94**
($3,361–5,000 offer p50). A depth mechanism fed by the model's OWN realized
scarcity cannot reach the 2023 conduct level while the **exhaustion-count
half** of the miss (the 117 missed hours, FINDING-ercot220, closed) is
absent from the model's path. The depth object returns to **Door D** carrying
the count half with it.

## 1. THE TWO-SESSION SHAPE, RECORDED FOR AUDIT

Builder session (merged to main through PR #4116/#4119): precommit pinned
pre-fit (`1039e94`); Phase-0 v1 FAIL recorded + the reduced v2 family
pre-registered BEFORE any v2 fit (`dc517d7`); v2 FAIL recorded + Phase-1
entered on owner instruction with frozen constants half-life 30 d / β 3.0077
(`6e2ea21`); build, default-off, ERCOT-gated, through the ercot-219 stage-3
`p1_storage_discharge_cost` seam as two-pass P1 (`fc3bd02`); D-5 attribution
spec + the §4 gate scorer committed before either arm was read (`c9cfd15`);
CONTROL solved and committed (`18907e5`); Amendment 3 (pure-λ event basis, on
the owner's direct purity question) then Amendment 4 — the λ-only arm
measured **INERT at 0 model spike days** (the model's deep-scarcity
expression lives in its own co-optimization scarcity adder, its λ tops out
~$700), STOPPED and DISCARDED, recorded honestly; event basis = λ + the
model's own decontaminated anchored scarcity-adder mirror (`906be2f`,
`41cc6f1`); the ARMED bundle + gate scorecard (`c407c8d`). The builder
session died before registration/stamp/log.

Successor session: re-verified **G-REPRO in its strongest form from committed
bytes** (control ≡ keeper, 12/12 hourly sidecars sha256-identical, flag-off
byte-identity proven at HEAD); wrote the C6 attestations
(`gen_ercot221_attestation.py`) and the G-DOF ledgers; registered both
members WITH payloads; stamped the matrix cell **R**; wrote this finding and
the calibration-log entry. Its opening dispatch pre-dated the merged record
(it chartered "Phase-0"); under DO-NOT-REDO the adjudicated Phase-0 was NOT
re-run. One honest operational note: the successor session's own redundant
arm re-solve (launched before it saw PR #4119 land the committed armed
bundle) was OOM-killed once by a concurrent NEISO seam-proof replay on a
15 GB box, and was discarded when the committed bundle superseded it; the
solve-based cross-ISO seam proof was dropped on owner pushback — rule-25
isolation rests on the structural ISO gate (`iso == "ERCOT"` conjunct at the
single orchestration site), the flag-off G-REPRO byte-identity, and the build
commit's unit tests (28/28 helper + 13/13 cache-key identity).

## 2. THE GATES, AT FULL MAGNITUDE (`ercot221_gates.json`)

| gate | bar | result | verdict |
|---|---|---|---|
| G-CAP | 0 protocol-cap violations | **0 in 26,280 h** | PASS |
| G-SPUR | ≤ +5/yr vs 9/11/1 | 2023 9→**11** (+2), 2024 11→**10** (−1), 2025 1→**1** | PASS |
| **G-SHED** | no new shed vs 0/1/0 | 2023 0→0; **2024 {3067} → {3066, 3067}**; 2025 0→0 | **FAIL** |
| G-BAT | ±25 % vs EIA-930 BAT at tail hours | 2024 **0.886**, 2025 **1.076** (2023 series not covered) | PASS |
| G-D2 | attribution row present; no new D-4 rows | D-5 row `ercot_storage_adaptive_expectation` present; D-4 rows identical | PASS |
| G-DOF | ledger delta = the two constants; n_residual flat | control 8 entries / 6 residual → arm 9 / 6; delta = the one measured-physical entry carrying (half_life, β) | PASS |
| G-REPRO | control replays keeper before arm read | 12/12 sidecars sha256-identical + determination | PASS |
| LOYO | structurally N/A (2023-identified behavioral constants); G-SAFE declared the cross-year falsifier ex ante | — | as declared |

The failing hour: 2024 hour 3066 (May 8, hour-beginning 18 — inside the
h17–20 floor window) — the floor withheld
storage discharge at a tight hour the keeper clears without shed. This is the
ercot-162 failure mode at single-hour scale: repricing storage manufactured
scarcity that reality did not record. G-SAFE-2024's Phase-0 miss (0.9489 vs
0.95 — the keeper's 3 real 2024 event days keep evening floors ≥ $110 in
~5 % of hours) was the advance warning, and the A/B realized it.

## 3. G-ADA — the mechanism's own audit signature (reported, not gated)

| year | model spike days | P_hat max | floor-hours ≥ $1,000 | floor max |
|---|---:|---:|---:|---:|
| 2023 | 7 | 0.370 | 160 (Aug 24 / Sep 120 / Oct 16) | $1,850 |
| 2024 | 3 | 0.176 | 0 | $878 |
| 2025 | 0 | 0.000 | 0 | $0 |

The dynamic signature is *qualitatively* right — concentrated in Aug–Oct
2023, decaying through 2024, extinct in 2025 with **no year key** (2025's
sidecars are byte-inert; ercot-217 stays closed) — and *quantitatively*
starved: reality's September was priced off August's experience at implied
P ≈ 0.81 (RESEARCH-ercot220b §2); the model's own August supplies at most
P_hat 0.37, and its floors peak at $1,850 where measured conduct sat at
$3,361–5,000 p50.

## 4. SIDE-EFFECTS AT FULL MAGNITUDE (Q-B FINAL / R-A — never a basis, never a gate)

Probe basis (demand-weighted P1 settled vs actual hub RT), control → arm:

| year | C3a | C3b NRMSE | model tail >$200 (actual) |
|---|---|---|---|
| 2023 | −30.38 → **−29.77 %** | 3.4522 → 3.4216 | 67 → **71** (181) |
| 2024 | +7.88 → **+8.64 %** | 2.3439 → 2.3571 | 22 → 22 (53) |
| 2025 | +0.51 → +0.51 % | 0.9389 → 0.9389 | 1 → 1 (31) |

The arm buys ~0.6 pp of a ~30 pp probe-basis miss (official-basis miss
−40.1 %) and pays with a manufactured shed hour and a slightly worse 2024.
The −13.4 % depth ceiling (RESEARCH-ercot220b §1) was never reachable at
P_hat ≤ 0.37; the realized motion is proportional to the starved bootstrap.

## 5. IS THIS A KEEPER? — the recommendation given to the owner, and its reasoning

The owner asked, with the standing structural standard ("if structural
integrity improves but gates regress that may still be a keeper"). The
session's answer: **NO — not recommended, promotion declined.** The standard
rescued ercot-213/215 because those arms bought *measured structural
exactness* (protocol-cap fidelity to the published design; decontamination of
an unpriceable term) — the mechanism was *more right* even where scores
regressed. Here the opposite holds on both halves: (a) the structural claim
itself under-delivers by its own measurement — the adaptive family is the
right *phenomenon* (the §3 signature), but the armed mechanism's expectation
state provably cannot reach the level that forms the 2023 tail, because the
model's own path lacks the exhaustion-count events that trained reality's
expectation; and (b) the one gate it breaks is a **physical outcome**, not a
reporting band — it sheds load in an hour reality served. A mechanism that
is directionally right but starved is not improved structure; it is
scaffolding for a dependency (the count half) that FINDING-ercot220 measured
closed. Both records stand; the owner may still promote by explicit act.

## 6. WHAT THIS ADJUDICATES, AND WHAT IT DOES NOT

- **Adjudicated R (as armed):** the model-path-bootstrapped adaptive
  expectation offer at these constants, this event basis, one adaptation
  pass, evening window. DO-NOT-REDO applies to this cell.
- **Not adjudicated:** (i) an *iterated* fixed point (spikes → floors → more
  spikes) — a NEW card if ever proposed; it is G-SHED-exposed by
  construction and the precommit deliberately pinned one pass (rule 10
  spirit); (ii) the identification instrument's finding that the measured
  evening response is an experience-follower — that stands as evidence about
  the market, independent of the arm; (iii) the count half — closed by
  FINDING-ercot220 at B-2/Option-C/Door-D, unchanged by this result.
- **The joint reading of ercot-220 + ercot-221:** the 2023 miss's two halves
  are now BOTH adjudicated against every admissible in-model route — the
  count half cannot be seen without an online/commitment object (rule-13
  wall, B-2 drafted DO-NOT-SIGN), and the depth half cannot be priced off the
  model's own path *because* the count half is missing. **Door D (wait for
  the 2026 SOM's real anchors, ~mid-2027) is the confirmed floor for the
  2023 price object.**

## 7. DATA TASK (dispatched): 2022 NP3-965 MIS recoverability — NOT RECOVERABLE

Measured live 2026-08-19 against the MIS document list (`IceDocListJsonWS`,
reportTypeId 13052, the committed fetch constants): **885 documents, earliest
publication 2024-03-24**, latest 2026-08-18, **0 publications in the
2022-03..2023-02 window** (the 2022 delivery year). The rolling free window
has consumed the entire 2022 publication span; per the corpus README a
publication month that ages out is unrecoverable from any source this repo
reaches. The measured 2022 storage offer level — the RESEARCH-ercot221prep §4
memory-vs-competition discriminator — therefore cannot be produced; an
owner-side ERCOT archive request is the only conceivable route (named, not
chartered). The 2024-03-24+ span remains re-fetchable (unchanged since the
2026-08-09 check).

## 8. GOVERNANCE

- Q-B FINAL / R-A honoured: §4's numbers are side-effect reporting at full
  magnitude on the probe basis; no official criterion was targeted; the §4
  kill table contains no 2023 price criterion by design.
- Rule 13: the armed path consumes only pass-1 LP duals (Amendment 4 audit:
  the measured RTORDPA overlay excluded); measured conduct entered only the
  pre-registered Phase-0 identification. Rule 23: both constants frozen at
  the v2 fit, ledgered measured-physical with the G-DOF delta = exactly them.
- Rule 22: years {2023, 2024, 2025} only; the 2022 check read the MIS
  *document list* (publication dates), zero 2022 market data.
- Rule 25: ISO-gated structurally; flag-off byte-identity via G-REPRO; the
  solve-based cross-ISO proof dropped on owner instruction (§1).
- Rules 15/16: both members registered WITH payloads, all three years in one
  bundle each; retention cap honoured (roster ≤ 15, holds intact).
- Rule 28(b): the `ercot_storage_adaptive_expectation` ERCOT cell stamped
  **R** in-session; `check_mechanism_matrix.py` clean on this edit.
- Rule 27: every ≥300-line pushed file blob-verified; payload commits over
  `git push`.
- Keeper at session start and end: `2026-08-17-ercot215-arm-decontam`.
- Artifacts: this finding; `results/calibration/ercot221_gates.json` (+ the
  builder session's `ercot221_adaptive_phase0.json`,
  `ercot221_daily_surface_2023.json`); the A/B pair
  `2026-08-19-ercot221-{ctl-headbase,arm-adaptive}` with attestations and
  DOF ledgers; the matrix cell; one calibration-log entry (ercot-221).
