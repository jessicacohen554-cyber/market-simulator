# PRECHECK — caiso-164: CAISO zonal marginal-loss surface

**Session** caiso-164 · **Date** 2026-08-04 · **Branch**
`claude/caiso-ns-basis-root-cause-b3f9qo`

**PRE-REGISTERED BEFORE EITHER ARM SOLVED.** Everything below — the §0
diagnosis, the mechanism, the gates, and the rule-14 disposition in §5 — is
pushed to `origin` before a single LP is built. Nothing here may be edited
after a solve; the finding document records what happened against it.

**Mechanism** `ScenarioConfig.caiso_zonal_loss_surface` · matrix row
`zonal_loss_surface` (CAISO cell) · **incumbent keeper**
`2026-08-03-caiso163-asym-path-ratings`

---

## 0. THE DIAGNOSIS THAT PRODUCED THIS ARM (no LP, committed artifacts only)

caiso-163 §5 left an open root-cause question and named ONE untested
hypothesis (reduced N–S topology / zonal aggregation). The handoff was explicit
that the successor must be chosen from a measured decomposition, **not** from
that hypothesis. So §0 ran first, with no solve, from the caiso-163 keeper's
committed `hourly/system_<y>.parquet` sidecars and
`data/raw/lmp-data/CAISO/CAISO_dam_hourly_<y>.csv`
(`scripts/probes/caiso164_ns_basis_decomp.py`,
`scripts/probes/caiso164_zonal_surplus.py`).

### 0.1 CAISO publishes the congestion/loss split directly

A CAISO LMP is `MCE + MCC + MCL`. MCE is the single system reference, identical
at every node, so **any hub-to-hub basis is exactly `dMCC + dMCL`** — no
estimation involved. Measured, mean $/MWh:

| year | pair | total | dMCE | **dMCC** | **dMCL** | cong % | loss % |
|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | NP15−ZP26 | 5.947 | 0.0000 | **4.771** | **1.176** | 80.2 % | 19.8 % |
| 2024 | NP15−ZP26 | 8.576 | 0.0000 | **7.475** | **1.102** | 87.2 % | 12.8 % |
| 2025 | NP15−ZP26 | 5.727 | 0.0000 | **4.677** | **1.049** | 81.7 % | 18.3 % |
| 2023 | NP15−SP15 | 2.337 | 0.0000 | 2.101 | 0.235 | 89.9 % | 10.1 % |
| 2024 | NP15−SP15 | 7.992 | 0.0000 | 7.148 | 0.844 | 89.4 % | 10.6 % |
| 2025 | NP15−SP15 | 6.009 | 0.0000 | 4.991 | 1.018 | 83.1 % | 16.9 % |

**The model's LP is lossless**, so it has *no representation whatsoever* of the
`dMCL` column. That is not a calibration gap — it is a missing physical
mechanism, and the model's current treatment of it is the **estimate** "losses
are zero" (rule 14 `[R-ACCURATE]`).

### 0.2 The congestion majority is a FREQUENCY-and-DIRECTION miss, not magnitude

Scored like-for-like (model price basis vs measured `dMCC`, since the model can
only produce the congestion component):

| year | measured sep % | model sep % | **FREQ ×** | measured \|cond\| | model \|cond\| | **MAG ×** | net × |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 68.87 % | 2.71 % | **0.039** | 7.196 | 2.859 | 0.397 | 0.0156 |
| 2024 | 87.70 % | 4.73 % | **0.054** | 9.014 | 2.299 | 0.255 | 0.0137 |
| 2025 | 93.11 % | 3.24 % | **0.035** | 5.927 | 2.625 | 0.443 | 0.0154 |

**Frequency dominates** (0.035–0.054× vs magnitude 0.26–0.44×). And it is worse
than "too few hours" — it is the **wrong hours in the wrong direction**:

* In the **top decile of measured |dMCC|** (864 / 879 / 876 h, measured mean
  **+34.0 / +43.5 / +30.3 $/MWh**, **100 % / 100 % / 99.9 % of them S→N**), the
  model's NP15 and ZP26 prices separate in **0 hours**. Swept over the whole
  plausible alignment range (lags −3…+3 h) the count never exceeds 30 of ~875.
* The model's rare separations run **99–100 % N→S** — the *opposite* direction
  to the real binding constraint.

### 0.3 The north is roughly right; **the south never gets cheap**

2024, Pacific local hour, $/MWh:

| h | meas NP15 | meas ZP26 | meas Δ | mdl NP15 | mdl ZP26 | mdl Δ |
|---:|---:|---:|---:|---:|---:|---:|
| 09 | 31.54 | 9.77 | **+21.78** | 25.19 | 25.19 | 0.00 |
| 12 | 26.10 | 5.26 | **+20.83** | 19.40 | 19.40 | 0.00 |
| 14 | 28.58 | 7.06 | **+21.52** | 21.58 | 21.58 | 0.00 |

The model's NP15 tracks the measured NP15 to a few $/MWh. The model's **ZP26 is
$14–19/MWh too expensive** midday. The five CAISO zones price as **one
copperplate**: identical minima (−$20.00), identical p01/p05, and identical
sub-$0 hour counts (610 / 610 / 610 in 2024) — while the real market's south
goes sub-$0 in **1,151 h (ZP26) and 1,169 h (SP15)** against the north's 271 h.

### 0.4 Why — and this is the part that is NOT fixable in this lane

The renewable siting is **correct**: ZP26 and SP15_rest carry belly
renewable/load ratios of 2.1–3.5 and are in local surplus in ~2,850 of 2,920
belly hours. But the **southern block as a whole is a net renewable IMPORTER**
in the belly (mean net −3,679 / −2,494 / −834 MW), because `LA_BASIN` carries
77–83 TWh of load against a 0.11–0.12 belly ren/load ratio and absorbs the
entire ZP26 + SP15_rest surplus through a 12,008 MW one-way link that never
binds. No surplus reaches Path 15, so Path 15 never binds S→N with a positive
dual, so the N–S basis cannot form.

Reproducing that requires the **intra-SP15** corridor (desert/Kern generation →
LA basin) to congest — i.e. CAISO nodal / intra-zonal congestion data.
**That is NOT in `data/raw`.** Per the handoff, the correct outcome for it is
to **FILE a data blocker with the measurement that establishes it**, not to
approximate it with a fitted proxy. The finding document files it.

### 0.5 What this arm therefore is, and what it is NOT

**IS:** the one component of the measured basis that is (a) measured and
published, (b) already in `data/raw`, (c) has a frozen, twice-adjudicated
derive pattern (MISO miso-76, PJM pjm-136), (d) carries **zero free
parameters**, and (e) the model has **no representation of at all**.

**IS NOT:** a fix for the congestion majority. Bounded ex ante at the measured
`dMCL`: **≤ 1.18 / 1.10 / 1.05 $/MWh** of the 5.95 / 8.58 / 5.73 $/MWh
NP15−ZP26 gap — i.e. **≤ 20 % / 13 % / 18 %**. It may not be reported as
closing the north–south basis, and it is **not a C3a arm** (C3a-2025 is an
owner-ledgered caveat on the caiso-141 A2 non-public pumped-storage data wall).

---

## 1. THE NO-TUNING CLAUSE

**Zero free parameters. Nothing in this arm is swept, blended, interpolated
against a residual, or chosen after seeing a price.**

* The surface is `dev_z,m = Σ MCL_z,t / Σ MCE_t` over the month — the **same
  estimator, unchanged**, as the frozen `derive_miso_loss_surface.py` and
  `derive_pjm_loss_surface.py`. It is not re-specified for CAISO.
* Its inputs are CAISO's own published DAM component record, already committed
  at `data/raw/lmp-data/CAISO/CAISO_dam_hourly_<y>.csv`. No new intake, and no
  out-of-window year is read (rule 22 — the holdout spend freeze is ACTIVE;
  `YEARS = (2023, 2024, 2025)` is hard-coded in the derive).
* Rule 25 `[R-ISO-SCOPE]`: every number is CAISO's own, written to CAISO's own
  `CAISO_loss_surface.csv`. **No value crosses from the MISO or PJM analogues**
  — the only thing shared with them is the estimator's algebra, and per rule
  28(d) their verdicts do **not** fill CAISO's cell (which enters as `U`).
* Rule 23 `[R-FROZEN-DERIVE]`: the derive re-runs only when its source data
  updates, never because a residual moved.
* The `1e-3 $/MWh` loss-pair flow tiebreaker is the rule-9 `[R-EPSILON]`
  numerical device (identical role and value to the storage ε and to PJM's
  `PJM_LOSS_LINK_TIEBREAK_EPS`), **not** a hurdle rate and not a fitted level.
* **The DOF ledger must not move.** It stands at **11 entries / 9 residual**
  and the attestation FAILS if it changes.

**Admissibility (rule 13 `[R-MEASURED]`).** The test is: could this quantity be
produced for a forward year from forward drivers, and would it respond to
changed conditions? Yes — the surface is a physical network property that
regenerates from the same published feed every year, and the derive already
emits pooled `year = 0` rows as the forecast-mode forward analogue. It is an
*input*, not an *outcome*: no unit is pinned to observed generation, no offset
is tuned to the price or volume residual, and no input is rescaled so the
model's output lands on the actuals. This is the same admissibility class
already adjudicated for MISO and PJM.

---

## 2. PRE-SOLVE STRUCTURAL AND LIVENESS CHECK — RUN AND PASSED BEFORE SOLVING

`scripts/probes/caiso164_wiring_probe.py`, exit 0. The caiso-162 lesson applied
ex ante for the second session running: **a `run_config.json` recording a flag
as armed is not evidence the LP saw it**, and **liveness is verified on a
physical observable, never on prices** (caiso-162/163 standing lesson).

| check | result |
|---|---|
| **W1** call site fires on the calibration lane | links **6 → 8** in all three years |
| **W2** flag is the gate (off-arm topology still splittable) | True, all years |
| **W3** builder REFUSES an unsplit topology | True (raises; a signed lossy link would create energy) |
| **W3** loss array nonzero and oriented **S→N** | Path 15 S→N ε = **0.01936 / 0.02516 / 0.02645**; N→S ε = **None** (clamped) |
| **W4** caiso-163 ratings survive the split | `NP15_ZP26` cap 3265 / rev 5400, **2 links, signs [−1, +1]**; `ZP26_SP15_rest` cap 4000 / rev 3000, same — all years |
| **W5** WECC seam untouched | identical link set, **zero** lossy seam links |

Lossy directions found (2024): `ZP26→NP15` 0.02516, `ZP26→SP15_rest` 0.00712,
`SP15_rest→ZP26` 0.00084. **The lossy direction is S→N — the same direction the
measured congestion binds in.** That is a property of CAISO's own measured
surface, not a choice: `dev_NP15` (−0.0179) is the least negative.

**Derive acceptance, also pre-solve** (`--acceptance`, the miso-76 B1 band
`[0.5×, 1.5×]` applied to CAISO's own quantities): **6/6 pair-years in band**,
ratios **1.04–1.06×**. MCE identity holds exactly (0.00e+00) in all three
years.

There is **no zero-delta control year** — the surface is nonzero in every year
— so, as in caiso-163, the free zero-delta control is replaced by the
structural assertion above. That is what licenses arm A as a clean control.

---

## 3. THE A/B

Both arms at the **same HEAD**, via `scripts/replay_keeper.py --set
caiso_zonal_loss_surface=<bool> --out-dir <arm>` — the sanctioned recipe
channel, guaranteeing a structurally single-field delta. The committed keeper is
**not** a same-HEAD baseline (main moves fast). Rule 16: `--year 2023 2024 2025`,
**one invocation and one bundle per arm**, years sequential (rule 12), the two
arms concurrent, **in-session** (never a CI runner).

| | |
|---|---|
| treatment | `caiso164_zonal_loss_surface` — flag **on** |
| control | `caiso164_control_lossless` — flag **off**, same HEAD |

Run-id collision guard: the shorthand slugs from the first four significant
words of `model_changes_note`, so the two notes are written to differ at word
one (`caiso164 zonal loss surface …` vs `control flagoff lossless baseline …`).

---

## 4. THE GATES — declared here, scored in the finding

**Liveness (must pass or the arm is INERT and may not be promoted):**

* **L1** the control's internal CAISO links carry **zero** loss (the mechanism
  is genuinely absent there) — asserted structurally, not on price.
* **L2** the treatment's Path-15 S→N flow is charged a **positive** loss
  fraction in every month, and the realised NP15/ZP26 duals separate in the
  S→N direction (NP15 dearer) in materially more hours than the control's
  237 / 414 / 284.
* **L3** **the caiso-163 ratings still bind exactly**: zero treatment hours
  over any published directional cap, all paths, all years. A loss split that
  loosened Path 15 would be a regression, not a feature.

**Structural (the quantity under test):**

* **S1** mean model NP15 − ZP26 moves **toward** the measured +5.95 / +8.58 /
  +5.73, i.e. becomes less negative than the control's −0.077 / −0.109 /
  −0.084.
* **S2** the movement is **bounded by the measured `dMCL`**: the treatment −
  control change in mean NP15 − ZP26 must not exceed **1.18 / 1.10 / 1.05
  $/MWh**. Overshooting the measured loss component would mean the mechanism is
  doing something other than representing losses.
* **S3** hours with NP15 ≠ ZP26 rise (a loss wedge separates zones in every
  hour flow runs S→N, not only in congested hours).
* **S4** mean NP15 − SP15_rest also moves toward its measured +2.34 / +7.99 /
  +6.01.

**Guards (protective — a flip is a stop-the-line, not a trade):**

* **G1** no criterion flips PASS → FAIL (C1, C2, C3a, C3b, C3c, C4, and
  protective C6/C7/C8). C3a-2025 is expected to stay at **+12.0 %**; this is
  not a C3a arm.
* **G2** determination stays **CALIBRATED-WITH-CAVEATS**, 2 ledgered / 0 FAILs,
  **no new caveat slot spent**.
* **G3** config drift against **both** the incumbent and the same-HEAD control
  is **exactly one field**, `caiso_zonal_loss_surface`, with zero schema drift,
  computed with a present/absent-aware diff (never `dict.get`).
* **G4** DOF ledger unchanged at **11 / 9**.
* **G5** `mode == "backcast"` in both arms.
* **G6** the inherited owner-decision default flips (`retirement_rule =
  pipeline` D-1; `entry_rate_limits` + `entry_commissioning_lag` D-2;
  `net_cone_forward_escalation = reindex_gross` D-3a) are **merged owner
  decisions, not this session's choices and not tuning**. Both admissibility
  conditions are DISCLOSED and ASSERTED as `gen_caiso163_attestation.py` does:
  they are forecast-gated capacity-evolution machinery **unreachable at
  `mode="backcast"`**, and they are **identical across both arms**.

**Rule 22.** CAISO holds **no** `complete` marker → no `calibration-complete`
re-key (D-5(b) is for `complete` ISOs only) and no marker is written. The
**holdout spend freeze is ACTIVE and outranks every marker**: 2023/2024/2025
only, nothing outside it solved, scored or registered. LOYO reduces to the
no-held-out-degradation check — this session fits nothing and moves no free
parameter, so the requirement is that all three years show the same structural
direction and no criterion flips in any year.

---

## 5. THE RULE-14 DISPOSITION — STATED BEFORE THE RESULT

This is pre-committed so it cannot be chosen after seeing the sign, exactly as
caiso-163 §5 did.

**If the measured loss surface makes the backcast residual WORSE, it stays in.**

Rule 14 `[R-ACCURATE]` is explicit: swapping a hand estimate ("losses are
zero") for real data and getting a worse fit is a **signal that something else
in the model is miscalibrated and the estimate was silently compensating for
it** — a discovered bug, not a reason to revert. Rule 1 `[R-STRUCT]` says a
structurally-correct mechanism stays in even if the fit worsens, and that a run
is a keeper because it is the most structurally faithful, not because it has
the lowest MAE. Marginal transmission losses are a real, published, physical
property of CAISO's network; a lossless LP is a known simplification, not a
modelling choice to defend.

So, pre-committed:

1. **Gates L1–L3 pass and G1–G6 hold → the mechanism is KEPT**, whatever S1–S4
   do and whatever happens to load-weighted λ or MAE.
2. **Any of L1/L2/L3 fails → the mechanism is INERT or broken → NOT promoted**,
   the CAISO cell is written `I` or `R` with the evidence, and no residual
   argument rescues it.
3. **Any of G1–G6 fails → stop-the-line.** The arm is not promoted and the
   failure is investigated as a defect, not traded against a better basis.
4. **S1–S4 are reported as MEASUREMENTS, not as pass/fail promotion criteria.**
   S2's ceiling is the one that can *fail* the arm: a movement **larger** than
   the measured `dMCL` means the mechanism is not representing losses and must
   be investigated before promotion.
5. Promotion is in scope under the owner's standing rule — "if structural
   integrity improves but gates regress that may still be a keeper" — and is a
   separate governance act with its own adversarial attestation, modelled on
   `scripts/gen_caiso163_attestation.py`.

**No compensating adder, haircut or offset will be added to make the numbers
look better** (rules 1 / 13), and the ~80–87 % congestion gap will **not** be
claimed as closed.

---

## 6. Artifacts

| | |
|---|---|
| §0 decomposition probe | `scripts/probes/caiso164_ns_basis_decomp.py` |
| §0 surplus probe | `scripts/probes/caiso164_zonal_surplus.py` |
| pre-solve wiring probe | `scripts/probes/caiso164_wiring_probe.py` |
| derive | `scripts/data/derive_caiso_loss_surface.py` |
| surface | `data/raw/iso-specific-transmission/CAISO_loss_surface.csv` |
| LP mechanism | `interchange/caiso.py::apply_caiso_zonal_loss_links` + `build_caiso_link_loss` |
| treatment bundle | `results/calibration/caiso164_zonal_loss_surface` |
| control bundle | `results/calibration/caiso164_control_lossless` |
