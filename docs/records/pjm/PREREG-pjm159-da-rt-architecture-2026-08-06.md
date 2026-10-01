# PRE-REGISTRATION (pjm-159, task B): is there an ADMISSIBLE architecture for the DA/RT price mismatch, or is it a closed representation boundary?

**Session:** pjm-159 (task B — the pjm-158 escalation)
**Date:** 2026-08-06
**Branch:** `claude/pjm-final-assessment-nak29a`
**Owner authorization:** GRANTED 2026-08-06, owner instruction *"Do task B and c"*,
answering the pjm-158 escalation. This is the explicit authorization the handoff
required before any work inside PJM's owner-declared-closed price-formation
frontier (pjm-142). **The frontier is opened for THIS question only** — the
DA/RT clearing-basis architecture named in `FINDING-pjm158-da-virtual-clearing-2026-08-06.md`
§4/§5.5 — and for nothing else.
**Status at time of writing:** **ZERO measurements run.** No probe in §3 has
executed. The DA-virtual corpus fetch (in-sample 2023–2025, `hrl_da_incs_decs`,
unrestricted per the pjm-158 precedent — *not* rule-22 intake) is running as data
acquisition only. This file is committed and pushed **before any result exists**
(the pjm-143 / pjm-158 precedent), so every bar below is falsifiable.

---

## §1 — the defect, restated exactly

`pjm_da_virtual_bids` clears a **measured Day-Ahead** bid curve
(`hrl_da_incs_decs`) against the LP's single dual, which the scorer gates as
**real-time** (`calibration_verdict.score_price_mean`: *"vs actual RT (fallback
DA) … perfect-foresight dispatch LP prices RT physics, not day-ahead risk"*, with
DA a non-gated diagnostic; PJM's bench carries `rt_lw` in all three years so the
RT branch is taken).

Established by pjm-158, **not** re-litigated here:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| anchor @ actual **DA** (the rule-13 reference) | −0.755 | −1.620 | +0.204 |
| anchor @ actual **RT** (what the model is gated on) | **+5.082** | **+3.001** | **+6.781** |
| **DA−RT basis** | **+5.836** | **+4.621** | **+6.577** |
| — LEVEL leg | +2.991 | +0.973 | +2.432 |
| — SHAPE / dispersion leg | +2.845 | +3.648 | +4.145 |
| measured gain `dNet/dλ` (MW per $/MWh) | −440.5 | −462.8 | −340.3 |

A **perfect** RT price still clears +5.08/+3.00/+6.78 TWh of phantom demand. The
`N_RUNGS` compression is exact (≤0.13 TWh over 8→64), so no representation-exactness
fix exists. The layer is armed, is `K`, and disarming it fails C3c-2025.

**pjm-159 §5 adds one measured fact the architecture question turns on:** PJM's
DA−RT spread **flips sign outside the training window** — +0.89/+0.25/+0.82
in-sample vs **+0.10 in 2019** and −0.03/−0.25/−0.27/−1.49 in
2018/2020/2021/2022. So the in-sample near-cancellation is regime-specific in
*both* terms, not just in the model's price error.

---

## §2 — the candidate architectures, and what would kill each

Four candidates. **C-D is refused ex ante and gets no measurement**; C-A, C-B and
C-C each get a pre-registered kill test.

### C-A — a genuine two-price LP (add a DA pass)

Give the model a DA clearing pass whose dual is a DA-analogue, clear the virtual
curve there, and carry the schedule into the RT pass. This is what the real market
does, and it is the only candidate that fixes the mismatch at its actual root.

- **K-A1 (structural, MEASURED).** A second LP pass can differ from the first
  *only* through state it can see. So the spread it would have to reproduce must
  be a function of model-visible state. Test: regress the measured hourly DA−RT
  spread on model-visible state only — hour-of-day, month, net-load percentile,
  and a reserve-tightness proxy — and report adjusted R².
  **BAR: adjusted R² < 0.25 ⇒ C-A DIES.** Below that threshold the spread is
  predominantly *not* a function of anything a second pass could carry (it is
  commitment lumpiness and forward risk premium), so no admissible second pass
  reproduces it and the "two-price LP" is a mechanism with no identifiable driver
  — what rule 1 forbids building.
- **K-A2 (mandate, RECORDED not measured).** The repo is no-MIP by mandate and P2
  is archived. The DA−RT spread is generated largely by unit commitment and risk
  aversion; a DA pass without commitment is not a day-ahead market, it is a second
  copy of the same LP. pjm-138 already established the reserve-opportunity-cost
  half of PJM's price gap is structurally unpriceable here. **This kill stands
  even if K-A1 passes**, and would route C-A to the owner as a mandate question
  rather than a calibration lever.

### C-B — re-anchor the curve to the model's own dual

Re-derive the curve so it nets ≈ 0 at the price the model actually produces.

- **K-B1 (the miso-105 λ0-attractor test — PRE-IDENTIFIED FOR PJM AND NEVER RUN).**
  The `da_virtual_bids` matrix cell records, as an explicit open item: *"NOTE FOR
  PJM'S LANE (observation, NOT a verdict — rule 25): the λ0-attractor question is
  a property of the family and was never asked in PJM; PJM's premise is genuinely
  different (+7-11 GW of real depth), so it needs PJM's own λ0-gap and N÷(S+N)
  measurement."* This session runs it, on PJM's own corpus. Two statistics, both
  on the miso-105 bars:
  - **(i) λ0 reproduction** — does the curve's own crossing price reproduce the
    price its book actually cleared at? **BAR: median |λ0 − actual DA| ≤ $2/MWh
    ⇒ attractor risk CONFIRMED.**
  - **(ii) displacement share** — curve stiffness ÷ (curve stiffness + model
    stack elasticity), i.e. how much of each hour's price displacement the
    measured curve supplies. **BAR: ≥ 30 % ⇒ the model's price substantially
    BECOMES the book's crossing price ⇒ rule 1 and rule 13 kill.**
  - Either bar firing kills C-B.

  **Pre-registered against my own interest:** K-B1 tests the **armed incumbent**,
  not only candidate C-B. If PJM fires both bars, then pjm-158's `K` disposition
  is called into question on evidence it never gathered, and **I will report that
  plainly even though it cuts against the current keeper** — the cell would move
  toward `G`/`R` on the miso-105 grounds, and the honest consequence (the keeper
  loses C3c-2025) gets stated, not buried. Rule 25 cuts both ways: MISO's `G` does
  not decide PJM, and PJM's `K` does not survive PJM's own failed test.

### C-C — a measured DA−RT reconciliation wedge

Clear the DA curve at `model_dual + wedge`, with the wedge a measured DA−RT
reconciliation. This is rule 14's *"prefer a reconciled version of the real data"*
route for a real input misaligned to our representation.

- **K-C1 (rule 13 forward test, MEASURED).** Rule 13's admissibility test is:
  *could this same quantity be produced for a forward year from forward drivers,
  and would it respond to changed conditions?* A wedge expressible as a function
  of model-visible state passes; a fixed measured hourly series fails (no forward
  analogue, and it does not respond to changed model conditions). **This shares
  K-A1's regression: adjusted R² < 0.25 ⇒ the only available wedge is a measured
  outcome series ⇒ C-C DIES on rule 13.** Note the sign of the risk: a wedge
  fitted to make the layer net ≈ 0 would be a residual-tuned adder, which rule 13
  forbids outright — so C-C is admissible *only* in its state-conditional form,
  and only if the state actually explains the spread.
- **K-C2 (rule 19, RECORDED).** A wedge prices the same phenomenon as the layer
  it corrects. It must REPLACE the current clearing basis, never stack on it. Any
  surviving C-C must be a single mechanism with a single owner.
- **§1's regime evidence is a standing hazard for C-C even if it survives:** a
  wedge identified on 2023–2025, where DA−RT is uniformly positive, would carry
  the wrong sign in four of the five other committed years.

### C-D — re-gate the scorer to DA — **REFUSED EX ANTE, no measurement**

One could gate PJM's C3a/C3b against DA instead of RT, making the layer's anchor
consistent by construction. Refused for two reasons, recorded now so it is not
rediscovered as an option later: (a) pjm-158 established the model **is**
structurally an RT analogue (perfect foresight, no commitment smoothing) — the
gate is right and the mechanism is the misaligned party; (b) changing a load-bearing
rubric criterion to accommodate one mechanism is fitting the *rubric* to the model,
which is strictly worse than fitting a parameter and defeats the purpose of having
a gate. **If a future session wants C-D it needs its own owner decision, as a
rubric amendment, never as a calibration change.**

---

## §3 — the probes (all no-LP, all in-sample 2023–2025)

| probe | measures | feeds |
|---|---|---|
| `_pjm159_dart_predictability.py` | measured hourly DA−RT regressed on model-visible state; adjusted R², per-leg (LEVEL/SHAPE) decomposition, and the TWh a state-conditional wedge would recover vs. the raw measured wedge | **K-A1, K-C1** |
| `_pjm159_lambda0_attractor.py` | PJM's λ0 reproduction vs the price its own book cleared at; curve stiffness; model stack elasticity; displacement share N÷(S+N) | **K-B1** |

Inputs, all committed or in-sample: `data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`;
`data/raw/pjm-da-virtuals/hrl_da_incs_decs_{2023,2024,2025}_*.parquet`;
`frontend/data/backcast/bench/PJM/{2023,2024,2025}.json.gz`;
`results/calibration/pjm152_collapse_A/hourly/`.

---

## §4 — pre-registered decision rule

Stated before any result, including the outcome I consider most likely.

1. **If K-A1 passes (R² ≥ 0.25) and K-B1 does not fire** — a state-conditional
   basis is identifiable and the layer is not an attractor. Then **C-C is the
   surviving candidate**: build it behind a **default-off** `ScenarioConfig` gate,
   add its mechanism-matrix row in the same PR (rule 28c), and run the
   pre-registered A/B (`--year 2023 2024 2025`, one invocation, years sequential;
   rules 12/16), registering both arms (rule 15). The A/B's own gates would be
   pre-registered separately before it solves.
2. **If K-A1 fails (R² < 0.25)** — C-A and C-C both die, on measurement rather
   than on preference. Combined with C-B (killed by K-B1 or by rule 13 on its
   face) and C-D (refused), **no admissible architecture exists**, and the honest
   deliverable is that the DA/RT mismatch is a **measured, closed representation
   boundary**: documented in the matrix cell and the keeper note, with the
   falsification bar any future proposal must clear. **This is a legitimate
   outcome, not a failure to deliver** — it is the pjm-142 / neiso-76 pattern, and
   it is what §1's regime evidence leads me to expect.
3. **If K-B1 fires** — the finding is about the **armed incumbent**, and it is
   reported as such regardless of what happens to C-A/C-C: the cell moves off a
   clean `K`, the keeper's C3c-2025 exposure is stated, and the disposition goes
   to the owner. I will not soften this to protect the keeper.
4. **In every branch**, the frontier closes again when this question is answered.
   A surviving C-C is a *mechanism* inside the frontier's disclosed boundary, not
   a re-opening of PJM's price-formation lane.

**No result may be reached by tuning.** No parameter is fitted to the virtual
layer's net cleared volume, to the price residual, or to any C1 class error. If a
candidate needs a fitted value to work, it is an open root-cause issue, not a
parameter (rule 21).

---

## §5 — what this session will NOT touch

- The **diurnal-amplitude family** and the **overnight gas commitment bridge**
  stay CLOSED/`R` (pjm-142). Not re-opened.
- **Net interchange / pjm-135 M4** stays chartered where it is (pjm-135), and
  pjm-153's item-15b collapse stands. Not re-opened.
- The **CC gas-elasticity object** stays REFUTED (pjm-157, slope ratio 0.959).
  Not re-tested.
- **Question C** stays CLOSED (pjm-158 §1).
- **Rule 22:** no out-of-training year is solved, scored or registered. The 2019
  and 2018–2022 spreads quoted in §1 are reads of measured committed bench
  artifacts with **no model output on either side** — the pjm-157/pjm-158 §1 class
  of read. The holdout freeze is not touched, and its current transient
  NEISO-2022-only lifted state authorizes PJM nothing.
- The **keeper stays `2026-08-04-pjm-152-collapse`** unless and only unless a
  Phase-1 A/B earns a promotion on its own pre-registered gates.

**Next shorthand after this session: pjm-160.**
