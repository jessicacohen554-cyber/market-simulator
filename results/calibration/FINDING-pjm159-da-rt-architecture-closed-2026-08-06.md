# FINDING (pjm-159, task B): there is NO admissible architecture for the DA/RT clearing-basis mismatch. It is a **measured, closed representation boundary**. And PJM is **not** a λ0 attractor — which strengthens the incumbent

**Session:** pjm-159 (task B — the pjm-158 escalation)
**Date:** 2026-08-06
**Branch:** `claude/pjm-final-assessment-nak29a`
**Owner authorization:** GRANTED 2026-08-06 (*"Do task B and c"*). The pjm-142
frontier was opened for **this question only** and **closes again with this
document**.
**Pre-registration:** `PREREG-pjm159-da-rt-architecture-2026-08-06.md`, committed
at `d4310783` **before any probe ran** (the pjm-143 / pjm-158 precedent).
**Governance:** zero LP solves. No out-of-training year solved, scored or
registered. No `ScenarioConfig` field added. Keeper **UNCHANGED**.

---

## §0 — the verdict in one table

| candidate | kill test | result | verdict |
|---|---|---|---|
| **C-A** two-price LP (add a DA pass) | **K-A1** DA−RT explainable from model-visible state? bar adj R² ≥ 0.25 | **adj R² = 0.038 / 0.047 / 0.054** — 5–7× below the bar, with a deliberately generous 7-block ladder incl. a 264-column hod×month interaction | **DEAD** (measured) — plus **K-A2** the no-MIP mandate, independently |
| **C-B** re-anchor the curve to the model's own dual | **K-B1** λ0-attractor, miso-105 bars | **NEITHER bar fires** (see §2 — this is a result *for* the incumbent) | **DEAD on rule 13's face**, not on K-B1: re-scaling a measured book so the model's output lands somewhere is the forbidden move (PREREG §4 anticipated this) |
| **C-C** measured DA−RT reconciliation wedge | **K-C1** = K-A1's regression, as rule 13's forward test | a state-conditional wedge reaches **0.11 / 0.17 / 0.22 TWh** of the **2.85 / 3.65 / 4.15 TWh** shape leg — **4–5 %** | **DEAD** (measured) |
| **C-D** re-gate the scorer to DA | — | refused ex ante (PREREG §2): the model *is* an RT analogue, and bending a load-bearing rubric criterion to fit one mechanism is worse than fitting a parameter | **REFUSED** |

**⇒ PREREG §4 branch 2. No admissible architecture exists. The DA/RT clearing-basis
mismatch is a MEASURED, CLOSED representation boundary** — documented, with a
falsification bar (§4) any future proposal must clear.

**And a second, unexpected result that cuts the other way:** the λ0-attractor test
the matrix cell had carried as *"pre-identified for PJM and never run"* is now run,
and **PJM passes it cleanly on both bars**. The `da_virtual_bids` PJM cell keeps
its `K` on measured grounds it previously lacked, and rule 25 is vindicated by
measurement rather than by assertion — the same mechanism family is `G` in MISO
*because* MISO is an attractor, and PJM measurably is not.

---

## §1 — K-A1 / K-C1: the DA−RT spread is not a function of anything the model can see

`scripts/probes/_pjm159_dart_predictability.py`;
`results/calibration/_pjm159_dart_predictability.json`.

Both surviving candidates rest on one premise. A second LP pass can differ from
the first **only through state it can see**, and rule 13's forward test asks
whether a quantity *"could be produced for a forward year from forward drivers"*
and *"would respond to changed conditions"*. Either way the DA−RT spread must be
a function of model-visible state. It is not:

| adj R², regressor ladder (model-visible state ONLY) | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| calendar (hour-of-day + month) | 0.0037 | 0.0155 | 0.0106 |
| + weekend | 0.0038 | 0.0161 | 0.0105 |
| + net-load percentile | 0.0044 | 0.0172 | 0.0111 |
| + load level & VRE share | 0.0134 | 0.0216 | 0.0170 |
| + net-load ramp | 0.0140 | 0.0217 | 0.0179 |
| + tightness proxy | **0.0381** | **0.0471** | 0.0274 |
| + hod × month interaction (264 cols) | 0.0299 | 0.0374 | **0.0540** |
| **best** | **0.0381** | **0.0471** | **0.0540** |

**Bar: adj R² ≥ 0.25. Observed 0.038 / 0.047 / 0.054 — K-A1 and K-C1 both FAIL.**

Two things make this robust rather than a thin regression:

- **The ladder is deliberately generous.** The honest way to conclude "no
  admissible driver exists" is to try hard to make the bar pass first. Seven
  nested blocks were tried, ending in the most flexible purely-calendar form
  available (a full hour-of-day × month interaction). In 2023 and 2024 that block
  *lowers* adjusted R² (0.0381→0.0299, 0.0471→0.0374) — the adjustment penalty
  correctly reporting that 264 extra columns do not pay for themselves.
- **Nothing measured is on the right-hand side.** No LMP, no cleared price, no DA
  quantity. A regressor the model cannot produce forward is not an admissible
  driver, so including one would manufacture a pass.

**What the spread actually is.** Mean +0.89 / +0.26 / +0.83 $/MWh against a
standard deviation of **14.5 / 16.5 / 35.1** and a mean absolute value of
**6.65 / 7.97 / 11.70**. So the annual-mean basis that drives pjm-158's LEVEL leg
is a small residue of an enormously volatile hour-by-hour process. That is a
forecast-error and risk-premium process — exactly what a perfect-foresight LP
cannot generate and should not be made to imitate.

**The TWh consequence, on the one decomposition that is not trivially true.** An
OLS fit with an intercept reproduces the annual mean by construction, so a
mean-only wedge closes pjm-158's LEVEL leg definitionally — which says nothing
about identifiability, and a constant tuned to a measured mean has no forward
analogue anyway. The informative leg is pjm-158's **SHAPE** leg, which needs
hour-by-hour predictability:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| SHAPE leg (pjm-158 §4) | 2.845 | 3.648 | 4.145 |
| reachable by a state-conditional wedge (≈ R² × leg) | **0.108** | **0.172** | **0.224** |
| **unreachable** | **2.737** | **3.476** | **3.921** |

**A rule-13-admissible wedge reaches 4–5 % of the leg it exists to close.**

**K-A2 kills C-A a second time, independently.** The repo is no-MIP by mandate
and P2 is archived. The DA−RT spread is generated largely by unit commitment and
risk aversion; a DA pass without commitment is not a day-ahead market, it is a
second copy of the same LP with the same dual. pjm-138 already established that
the reserve-opportunity-cost half of PJM's price gap is structurally unpriceable
here. So C-A fails both on measurement and on mandate.

---

## §2 — K-B1: PJM is **not** a λ0 attractor (the pre-identified test, finally run)

`scripts/probes/_pjm159_lambda0_attractor.py`;
`results/calibration/_pjm159_lambda0_attractor.json`. Reuses pjm-158's loaders
verbatim (`load_curve`, `build_hour_arrays`, `crossing_price`, `gain`,
`actual_da_price`), so the curve identification is the one the LP itself uses —
reproduced, not reimplemented.

### Bar (i) — λ0 reproduction: does NOT fire

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| λ0 mean ($/MWh) | 31.03 | 31.10 | 45.72 |
| actual DA mean | 29.34 | 29.80 | 43.75 |
| **median \|λ0 − DA\|** | **3.90** | **3.78** | **5.33** |
| mean \|λ0 − DA\| | 6.01 | 5.69 | 8.32 |
| hours within $2 | 27.4 % | 28.5 % | 19.2 % |

**Bar was ≤ $2.00 median. Observed $3.78–$5.33 — does not fire.** For contrast,
MISO's λ0 reproduced its cleared price to **$0.09 / $1.80 / $0.17**. PJM's book
does *not* pin the price it cleared at; it is genuinely a depth instrument, which
is exactly the premise difference the matrix cell recorded (+7–11 GW of real DA
depth) and never verified until now.

### Bar (ii) — displacement share: does NOT fire

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| curve stiffness `N` (GW per $/MWh) | 0.391 | 0.442 | 0.335 |
| model stack `S` — **pjm-142 measured (PRIMARY)** | 2.88 | 3.37 | 2.57 |
| **displacement share `N/(S+N)`** | **11.9 %** | **11.6 %** | **11.5 %** |
| same on this probe's revealed `S` (1.54/1.94/1.26) | 20.3 % | 18.6 % | 21.0 % |

**Bar was ≥ 30 %. Observed 11.5–11.9 % (and 18.6–21.0 % on the cross-check) —
does not fire.** MISO's was 31–34 %. PJM's stack is simply much more elastic than
MISO's, so the same-sized book supplies a third as much of the price displacement.

### §2.1 — a correction to this session's own pre-registered estimator, stated plainly

The PREREG said bar (ii) would be judged on a **net-load-conditional** slope,
reasoning that conditioning removes the demand-shift confound and yields a
conservative (smaller) `S` most likely to fire the bar. **That reasoning was wrong
and I did not follow it.** Conditioning on net load removes the demand shift *and*
the movement along the stack together: within a net-load decile the model's
dispatchable quantity is nearly pinned by the load level, so `dQ/dλ` is driven
toward zero mechanically. The conditional estimate lands at **0.085 / 0.496 /
0.424 GW/$** — 6–30× below pjm-142's independent measurement of the same quantity
and an order of magnitude below the revealed slope. It is biased toward zero,
which **inflates** the displacement share (to 82 % / 47 % / 44 %) rather than
conserving it.

Bar (ii) is therefore judged on **pjm-142's directly measured stack slope** —
2.88/3.37/2.57 GW per $1/MWh, hour-resolved at h01–h04 in its own pre-registered
no-LP pre-check, confirming pjm-141's ex-ante T2-quantile prediction
(2.92/3.50/2.66) to within 2–4 %. An independent, already-adjudicated measurement,
in this ISO, on this keeper line. All three estimates are reported in the probe
and in the committed JSON so the correction is auditable rather than asserted.

**Had I kept the pre-registered estimator, bar (ii) would have "fired" in all
three years and I would have reported an attractor finding that is an artifact of
a broken slope.** Recording this because the direction matters: the correction
moves the result *toward* the incumbent, so it is the kind of change that deserves
the most scrutiny, not the least. The falsification route is stated in §4.

### §2.2 — the two readings of the kill rule, neither smuggled

The PREREG wrote *"either bar firing kills C-B"*; the miso-105 **precedent** is a
conjunction (λ0 reproduction **and** ≥ 30 % displacement). Here the distinction is
moot — **neither bar fires**, so C-B survives K-B1 under both readings and the
incumbent's attractor status is NOT confirmed under either. Both are reported in
the committed JSON (`c_b_killed_prereg_rule_either`,
`incumbent_attractor_miso105_conjunction`) so no future reader has to guess which
standard was applied.

### §2.3 — so why is C-B still dead?

Because K-B1 was its *stronger* test, not its only one. C-B means re-deriving the
measured book so that it nets ≈ 0 at the price the model produces. That is
**rescaling a measured input so the model's output lands somewhere** — rule 13's
explicitly forbidden move — and it destroys the mechanism's identification: the
book's net-zero property at the actual DA price is a *measured fact* about what
participants submitted, not a normalization to be reimposed at a different price.
PREREG §4 branch 2 anticipated exactly this (*"C-B (killed by K-B1 **or by rule 13
on its face**)"*), so this is not a deviation.

---

## §3 — what this means for the incumbent, and for PJM's price lane

**The `da_virtual_bids` PJM cell stays `K`, and its evidential basis is now
stronger than pjm-158 left it.** pjm-158 kept `K` on a rule-14 argument (a real
measured input misaligned to our representation) while flagging a material open
defect. This session adds two measured facts:

1. **The misalignment is irreparable, not merely unrepaired.** No admissible
   architecture closes it — so "keep the accurate input and document the
   misalignment" (rule 14's instruction) is not a deferral, it is the terminal
   disposition.
2. **The mechanism is not corrupting the model's price.** The λ0 test PJM had
   never run says the book supplies ~12 % of the price displacement and does not
   pin the clearing price. The rule-1 worry that killed MISO's version does not
   apply here, measured.

**The standing pjm-158 warning is UNCHANGED and re-stated.** The DA−RT basis
(+5.84/+4.62/+6.58 TWh) and the model's own price error (−12.53/−9.55/−5.88) still
oppose each other by coincidence. Improving C3b toward RT still **grows** this
layer's phantom demand toward +5 to +7 TWh — toward the condemned pjm-102 clamp,
not away from it. §1 sharpens *why* that cannot be fixed in passing: the basis is
not a calibration residual with a driver, so there is nothing to co-calibrate.
**Any future PJM price-shape work must expect this mechanism's C1 contribution to
move against it, and must not reach for a wedge to offset it — §1 is the record
that no admissible wedge exists.**

**And the regime hazard, from the pjm-159 assessment §5.** PJM's DA−RT spread
flips sign outside the training window (+0.89/+0.25/+0.82 in-sample vs **+0.10 in
2019** and −0.03/−0.25/−0.27/−1.49 in 2018/2020/2021/2022). A wedge identified
in-sample would have carried the wrong sign in four of five other committed years
— an independent reason C-C would have been unsafe even had K-C1 passed.

---

## §4 — the falsification bar for any future proposal

Recorded so this boundary can be re-opened on evidence rather than on preference.
A future DA/RT proposal must clear **one** of:

1. **A driver that beats the bar.** A model-visible construction reaching
   **adj R² ≥ 0.25** on the hourly DA−RT spread in all three of 2023–2025, on the
   committed canonical series, with no measured price or measured quantity on the
   right-hand side. §1's ladder is the incumbent to beat.
2. **A commitment representation.** If the no-MIP mandate is ever relaxed, C-A
   becomes live again — the DA−RT spread's unexplained variance is exactly the
   commitment-and-risk component a MIP DA pass could carry. That is an owner
   mandate decision, not a calibration lever.
3. **A better `S`, if anyone wants to revisit K-B1.** The definitive stack
   elasticity comes from the model's own offer stack (the `mc` vector /
   `plant_tranche_bands`), which needs a model build this no-LP session did not
   do. If a stack-derived `S` came in **below ~0.9 GW/$** the displacement share
   would cross 30 % and the attractor question would re-open. Both of this
   session's credible estimates (pjm-142's 2.57–3.37 measured, this probe's
   1.26–1.94 revealed) sit far above that, so the margin is wide — but it is a
   margin, not a proof.

A proposal clearing none of these is re-litigating an adjudicated cell (rule 28's
DO-NOT-REDO discipline).

---

## §5 — reproduction

```
scripts/probes/_pjm159_dart_predictability.py   # §1  K-A1 / K-C1
scripts/probes/_pjm159_lambda0_attractor.py     # §2  K-B1
```
Committed outputs: `results/calibration/_pjm159_dart_predictability.json`,
`_pjm159_lambda0_attractor.json`.

Inputs, all committed or in-sample: `data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`;
`data/raw/lmp-data/PJM_{2023,2024,2025}_rt_da_monthly_lmps.csv`;
`data/raw/pjm-da-virtuals/hrl_da_incs_decs_{2023,2024,2025}_*.parquet` (36 files,
fetched this session by `scripts/data/fetch_pjm_da_virtuals.py`, whose default
span **is** 2023–2025 — in-sample, unrestricted, **not** rule-22 intake);
`results/calibration/pjm152_collapse_A/hourly/`.

## §6 — governance

- **Frontier.** Opened by owner authorization for this question only; **closed
  again by this document.** No successor lane is opened and none is implied.
- **Rule 28.** The `da_virtual_bids` PJM cell is updated in this session (duty b)
  with the λ0 result and the closed-boundary verdict. **No new mechanism, so no
  new matrix row** (duty c does not arise) and no `ScenarioConfig` field was added.
- **Rules 12/16.** No bundle, no solve — Phase 1 was not entered, per the
  pre-registered decision rule, because no candidate survived Phase 0.
- **Rule 15.** No run produced, so nothing is owed to either dashboard.
- **Rule 22.** Freeze respected; no out-of-training year solved, scored or
  registered. The 2018–2022 and 2019 spreads quoted in §3 are reads of measured
  committed artifacts with no model output on either side.
- **Keeper UNCHANGED** at `2026-08-04-pjm-152-collapse`; no marker re-keyed; the
  keeper shard's note is not edited (the pjm-158 precedent — matrix + log carry
  the record).

**Next shorthand: pjm-160.**
