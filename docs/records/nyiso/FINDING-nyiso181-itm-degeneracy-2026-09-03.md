# FINDING — nyiso-181: the un-dispatched in-the-money `ST_GAS` object is an artifact of the offer reconstruction

**Session:** nyiso-181, NYISO backcast-calibration track, 2026-09-03.
**Keeper at entry and exit:** `2026-09-02-nyiso-177-vintage-matched`
(`results/calibration/nyiso177_vintage_B1p`) — determination **NOT-YET**, target grade 5, fail
set **{C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}**. **Unchanged.** No keeper, no
determination, no gate, no score and no parameter moved.
**Pre-registration:** `results/calibration/PREREG-nyiso181-itm-degeneracy.md`, committed with its
probes **before either ran** (`0d508cdb`).

---

## 1. Headline

The object three NYISO sessions have been chasing — **3.84 / 9.09 / 3.99 TWh a year of `ST_GAS`
that the model's own offer puts in the money and that it does not run** (nyiso-179 §6.1),
re-posed by nyiso-180 §7 as *"a sustained ~1,000 MW LEVEL gap in 59–90 % of hours"* — **is
substantially an artifact of the instrument that measured it.**

Measured on the LP's **own installed offer** (the `mc` column PR #4650 added to `unit_hourly`,
regenerated here for the first time), the same object is **0.073 / 0.061 / 0.070 TWh a year**,
`R_aggregate` **0.992 / 0.991 / 0.992**, and the un-run in-the-money capacity averages
**8.4 / 7.0 / 8.0 MW** — **52× / 149× / 57× smaller** than published, and two orders of magnitude
below the ~1,000 MW the object was framed as.

The cause is exact and carries no threshold: nyiso-179's `build_year()` reconstructs the offer
**outside the solve** and omits **two armed, keeper-registered terms**. Restoring them reproduces
the LP's installed `mc` to **`max|d| = 0`** on every one of 88 units × 8,760 hours, in all three
years (§4).

**Pre-declared in PREREG §2 G-D and reached by a different route than expected:** the signature is
**an artifact of the ITM statistic, not a dispatch defect**, and the honest deliverable is
**retiring the statistic — not a lever.** No lever was opened, no parameter touched, no
`ScenarioConfig` field added.

---

## 2. What was run

| step | what | cost |
|---|---|---|
| control replay | `--replay-bundle nyiso177_vintage_B1p`, `--year` from the bundle's own `meta.json` (2023/2024/2025), one invocation, years sequential | ~15 min |
| I1 | `nyiso181_replay_identity.py` — is the replay the keeper? | zero solve |
| the parallel lane's gates | `nyiso180_unit_dispatch_adjudication.py`, **unmodified** | zero solve |
| G-D / G-P / G-S / G-L | `nyiso181_itm_degeneracy.py` | zero solve |
| root cause | `nyiso181_offer_reconstruction_repair.py` (**post-hoc**, §4) | zero solve |

The replay is a **bit-identical control**, so per rule 15 and the nyiso-180 precedent it is an
**instrument, not a run, and is NOT registered on the dashboard**. No non-control solve was run,
so rule 15 registers nothing — which is the correct outcome, not a gap.

---

## 3. The reconciliation, and it is itself a result

The brief directed this session to reconcile with the parallel nyiso-180 lane (PR #4650) before
proposing anything. **That lane delivered the instrument and a complete pre-registered probe, but
never the adjudication.** Disclosed in PREREG §0 (E5–E7) before any gate existed:

* `results/calibration/*/hourly/unit_hourly_*.parquet` is **gitignored** (`.gitignore:541,543`);
* the keeper bundle carries **no `unit_hourly`, any year**, and its probe hard-exits on a bundle
  predating the `mc`/`red_cost` columns;
* **no `_nyiso180_unit_dispatch.json` exists in any commit on any branch** — the only committed
  nyiso-180 outputs are `_nyiso180_st_gas_undispatch.json` and `_nyiso180_ramp_report.json`.

So every prediction in `PREREG-nyiso180-per-generator-dispatch.md` §2 — P-a, P-b, P-c, P-d and the
§2.4 STOP — **stood unmeasured**, which is that document's own S2 stop condition
("the adjudication is handed forward **unmade**") having fired **silently**. This session executes
that pre-registration **verbatim and unmodified**, which is the strongest evidential form
available here: gates fixed before their data existed, run by a session that did not write them.

Two further of that lane's own conditions are settled here for the first time:

* Its PREREG §1 said *"if a year's frame exceeds 5 MB the layer is reported and NOT committed"*.
  Measured: **16.4 / 17.4 / 17.4 MB** per year — **3.3× over its own threshold**. The frame stays
  gitignored and uncommitted, consistent with that condition.
* Its rule-28 duty to re-stamp `unit_network_layer_sidecar` in the NYISO shard was not discharged;
  the cell still read `nyiso-116`. **Stamped in this session** (§10).

---

## 4. THE ROOT CAUSE — exact, and with zero free parameters

**POST-HOC.** This is a root-cause diagnosis of a discrepancy the pre-registered instrument
surfaced, in the nyiso-180 §6 discipline: the gate records were written first and **no bar was
moved.** It rests on an identity, not a threshold.

`nyiso179_st_gas_offer_position.build_year()` builds the offer as

```
mc = assemble_mc(fa, fuel, 0.0, 0.0, so2=(fa.so2_rate, 0.0))
```

and omits two terms the keeper arms and the runner installs:

1. **The measured RGGI allowance price.** NYISO carries a state carbon program and the keeper arms
   `state_carbon_pricing=True`, so `runner.py` charges `resolve_carbon_price(config, year)` —
   **\$13.49 / \$20.71 / \$22.09 per tCO₂** in 2023 / 2024 / 2025. The reconstruction hardcodes
   `0.0`. (nyiso-179 §G1's own text records the premise: *"carbon/nox/so2 all 0 so mc = hr ×
   delivered fuel + vom exactly"*. `nox_price` and `so2_price` **are** 0 on this keeper; the
   carbon term is not.)
2. **`apply_gas_offer_margin`** — the mc-side half of `gas_offer_net_revenue_margin=True`
   (zonal anchor \$2.03–3.90/MMBtu across the five NYISO zones), which `runner.py:2494` applies
   **after** `assemble_mc`. The reconstruction never calls it.

### 4.1 The identity closes exactly

| year | reconstruction | median (recon − LP) \$/MWh | max abs delta | bin-hours differing > \$0.01 |
|---|---|---|---|---|
| 2023 | `assemble_mc` alone (nyiso-179) | **−9.5736** | 1,458.99 | 1.0000 |
| 2023 | + RGGI carbon | −2.0529 | 1,466.81 | 0.8739 |
| 2023 | **+ RGGI + offer margin** | **−0.0000** | **2.7e-05** | **0.0000** |
| 2024 | `assemble_mc` alone | **−15.3879** | 686.58 | 1.0000 |
| 2024 | + RGGI carbon | −3.7059 | 698.27 | 0.8750 |
| 2024 | **+ RGGI + offer margin** | **+0.0000** | **1.5e-05** | **0.0000** |
| 2025 | `assemble_mc` alone | **−11.9775** | 2,914.03 | 0.9998 |
| 2025 | + RGGI carbon | +0.0000 | 2,926.64 | 0.8729 |
| 2025 | **+ RGGI + offer margin** | **−0.0000** | **3.0e-05** | **0.0000** |

The residual at full repair is float32 rounding on the `mc` column. **Neither term alone
suffices**, and the order does not matter: both are required, and together they are sufficient.

### 4.2 The capacity basis was never the problem

`pmax × availability` as nyiso-179 reconstructs it matches the LP's own `cap_mw` at
**max |d| = 1.7e-05 MW** in all three years, and the class envelope reproduces **to the decimal**
(3,420.5 / 3,242.6 / 3,702.4 MW). The parallel lane's P-c was aimed at this and it is clean.

### 4.3 What the omission does to the statistic

Under-stating the offer by \$9.57 / \$15.39 / \$11.98 (median) puts capacity in the money that the
LP's own offer puts out of it:

| year | ITM bin-hour share, published basis | repaired basis | **spurious** share | spurious capacity | median TRUE `mc − price` on it |
|---|---|---|---|---|---|
| 2023 | 0.3692 | 0.1318 | **0.2376** | 804.3 MW | **+\$4.76** |
| 2024 | 0.6182 | 0.1575 | **0.4622** | 1,433.1 MW | **+\$7.87** |
| 2025 | 0.4846 | 0.2877 | **0.2043** | 743.5 MW | **+\$5.88** |

**The "in-the-money capacity that does not run" is, to that extent, capacity that was never in the
money** — and it sits \$4.76–\$7.87/MWh above its zone's clearing price on the LP's own offer.
1,433 MW of it in 2024 is the bulk of the ~1,000 MW the object was framed as.

### 4.4 Instrument validation — the recomputation IS nyiso-179's statistic

Running nyiso-179's own `median_R` on its own (defective) basis reproduces its published numbers:

| year | this session, published basis | nyiso-179 published | Δ |
|---|---|---|---|
| 2023 | 0.7751 | 0.7751 | **0.0000** |
| 2024 | 0.4482 | 0.4481 | **0.0001** |
| 2025 | 0.8205 | 0.8159 | 0.0046 |

so the comparison is like-for-like and not a different statistic. **The 2025 gap of 0.0046 is
itself explained**: this recomputation takes the numerator from the LP's own per-unit frame rather
than `class_hourly`, so it does not carry the dual-fuel oil undercount nyiso-180 §5 measured —
which is largest in 2025 (0.154 TWh) and negligible in 2023 (0.021).

---

## 5. A SECOND, INDEPENDENT DEFECT — the statistic is not a ratio of a thing to itself

Repairing the offer does **not** rehabilitate `R`. On the repaired basis it exceeds 1:

| year | median `R`, repaired | aggregate `R`, repaired | mean ITM capacity | mean class dispatch |
|---|---|---|---|---|
| 2023 | **1.409** | **1.396** | 982.8 MW | 1,372.1 MW |
| 2024 | **2.421** | **1.577** | 711.9 MW | 1,122.4 MW |
| 2025 | **1.747** | **1.408** | 824.4 MW | 1,160.8 MW |

The reason is structural and independent of the offer: nyiso-179's `R = mo / itm` divides the
class's **total** hourly dispatch — over **every** bin, including out-of-the-money bins held on by
the reliability floor and the commitment bridge — by the capacity of the **in-the-money bins
only**. Numerator and denominator range over **different populations**, so `R` cannot be read as
*"the share of in-the-money capacity that runs"* at **any** offer basis. Repaired, it is greater
than 1; defective, it was less than 1; neither reading is the quantity its name claims.

**The well-formed statistic is the matched-population one** — dispatch of the in-the-money bins
over capacity of those same bins, which the parallel lane's probe computes:

| year | `R_aggregate` (matched) | ITM capacity | ITM dispatch | **un-run** |
|---|---|---|---|---|
| 2023 | **0.9925** | 9.720 TWh | 9.646 TWh | **0.073 TWh** (8.4 MW mean) |
| 2024 | **0.9913** | 7.016 TWh | 6.955 TWh | **0.061 TWh** (7.0 MW mean) |
| 2025 | **0.9918** | 8.522 TWh | 8.452 TWh | **0.070 TWh** (8.0 MW mean) |

---

## 6. The gates, as measured — **VERDICTS WITHHELD, S1 FIRED**

### 6.1 Instrument checks (PREREG §2 G-I)

* **I1 — the replay is the keeper. PASS.** Hourly zonal prices differ in **0 of 52,560** cells and
  `class_hourly` in **0 of 122,640**, all three years, max abs delta **0.0**. The nyiso-180 §8
  bit-identity result is independently reproduced.
* **I2 — the identity closes. PASS.** The parallel lane's §2.4 STOP population is **0 unit-hours**,
  **0.0 MW at stake**, all three years, against a < 0.1 % bar.
* **I3 — `price` is the dual. FAIL in 2023 and 2025.** Median `mc − price` over interior
  unit-hours is **exactly 0.0** in all three years, but the mean is **−0.0714 / +0.0141 / −0.1266**
  against a ±\$0.05 bar.

**PREREG §4 S1 therefore fired: the verdict words for G-D and G-P are WITHHELD.** The probe's JSON
emits a mechanical `verdicts` block; an `adjudication_status` block was **added after the gates
ran** to say so, so that no later reader mistakes it for this session's adjudication. That
addition is additive only — the `years` block is **byte-identical** before and after, and **no bar
moved** (the nyiso-180 §8.1 discipline: repair the instrument, never the threshold).

**Reported honestly against my own bar, and it does not rescue it:** the substance I3 screens for
— a post-solve price transform or an injection-side delivery factor — is independently and
**exactly** refuted by §4.1, since the reconstruction reproduces the LP's `mc` to `max|d| = 0`
against the LP's own array, and a transform would displace the **median**, which is exactly zero.
**I3's mean leg is a poorly-chosen statistic** — a mean over a heavy-tailed residual
(`p95_abs` \$1.77 / \$1.95 / \$2.39 on 4,533 / 4,480 / 3,220 interior unit-hours) — and that is a
defect in **my** instrument, disclosed here rather than argued around. The bar was mine and I
adopted it from the parallel lane's P-b; I do not get to reinterpret it after seeing the result.

### 6.2 G-D / G-P / G-S / G-L — measured, unadjudicated

| year | `Dshare` ladder (0.01 / 0.10 / **1.00** / 5.00) | `Pshare` | `U_strict` | `U_strict` share |
|---|---|---|---|---|
| 2023 | 0.9424 / 0.9444 / **0.9770** / 0.9836 | **0.9599** | 0.0017 TWh (0.19 MW) | 0.026 |
| 2024 | 0.8354 / 0.8448 / **0.9745** / 0.9943 | **0.8909** | 0.0016 TWh (0.18 MW) | 0.026 |
| 2025 | 0.7024 / 0.7111 / **0.9430** / 0.9810 | **0.7639** | 0.0040 TWh (0.45 MW) | 0.057 |

Had they been adjudicated they would have read `DEGENERACY-CARRIES` and `PLATEAU` on the
pre-registered \$1.00 rung — **but note what the object had already become**: the residual they
partition averages 7–8 MW, so what they describe is 97 % of a quantity two orders of magnitude
below the object as posed. **The degeneracy carrier the brief ranked first is therefore neither
confirmed nor needed**: it would explain a gap that §4 shows was mostly never there. The MW
genuinely held off a bound by a non-energy row is **0.0017 / 0.0016 / 0.0040 TWh a year** —
0.18–0.45 MW on average.

### 6.3 The parallel lane's predictions, executed for the first time

| prediction | bar | result | outcome |
|---|---|---|---|
| **P-a / P-b** — `price` is the dual, no injection-side factor | median ≤ \$0.01, \|mean\| ≤ \$0.05 | median **0.0000** all years; mean −0.0714 / +0.0141 / −0.1266 | **median leg PASS, mean leg FAIL** (2023, 2025) — see §6.1 |
| **P-c** — capacity basis is not the carrier | upper-bound share < 10 %, `max(mw − cap) ≤ 1e-3` | share **1e-6 / 1e-6 / 2e-6**; `max(mw − cap)` **3.1e-05** | **PASS**, all years |
| **P-d** — ≥ 70 % of un-run MW at a **lower** bound, reserve headroom dominant | ≥ 0.70 | **0.058 / 0.165 / 0.298** | **FALSIFIED**, all three years, by a wide margin |
| **§2.4 STOP** — identity does not close | < 0.1 % | **0 unit-hours** | does not fire |

**P-d was that lane's own ranked prior, offered "so it can be wrong", and it is wrong.** The un-run
in-the-money MW sits **interior** — 0.942 / 0.835 / 0.702 — not at a lower bound. That is the
degeneracy signature, and it is consistent with §6.2.

**P-c passes on its own terms yet did not detect the defect §4 found**, because it tests only
whether the LP's `mw` exceeds the LP's own `cap_mw` — within one frame, a near-tautology. It was
aimed at the **capacity** basis, and the defect is in the **offer** basis. Naming that blind spot
is part of this deliverable: a basis test must compare the reconstruction to the LP, not the LP to
itself.

### 6.4 G-R — the reserve rows. **ONE-SIDED BY CONSTRUCTION; INCONCLUSIVE.**

Mean held reserve 11,764 / 11,752 / 11,750 MW against mean un-run in-the-money 8.4 / 7.0 / 8.0 MW;
Pearson r **+0.010 / +0.025 / −0.007**. Neither leg of `RESERVE-IMPLICATED` is met, so the gate
reads **INCONCLUSIVE**. **This is NOT an exoneration** — declared one-sided in PREREG §2 G-R
before it ran, because `Ω` is a sum over rows whose per-row duals are not persisted. Carrier 2 is
neither implicated nor cleared.

`Ω` itself is essentially zero across the class: p50 **0.0**, p95 **3e-06 / 3e-06 / 4e-06**,
non-zero in **0.68 % / 1.12 % / 1.01 %** of unit-hours. Whatever the non-energy rows charge this
class, it is small.

---

## 7. What this does and does not touch in the inherited record

**Directly affected — the same defective `build_year()` `mc` is the input:**

* **nyiso-179 G1's `NOT-OFFER-GOVERNED` verdict** and its 3.84 / 9.09 / 3.99 TWh object.
  **Superseded by §4–§5.**
* **nyiso-180 §7's re-posed object** — *"a sustained ~1,000 MW LEVEL gap in 59–90 % of hours"*.
  **The gap is 7–8 MW on the LP's own offer.** nyiso-180 §7's *reasoning* stands entirely — the
  reduced-cost correction to the optimality premise is right, and §6.2 confirms the population is
  interior — but the quantity it was applied to was inflated by the instrument.
* **nyiso-179's G3 peak exoneration, its G4 between-year decomposition, and the
  62.4 % / 24.6 % / 13.0 % split of the 2025 top-decile deficit** all read `st["mc"]` from the same
  `build_year()`. **They are not re-measured here** and no claim is made about which way they
  move — only that their instrument carried the defect and they need re-deriving before being
  cited again. **Handed forward.**

**NOT affected:**

* **The keeper, its determination, target grade, fail set and every scored metric.** The replay was
  bit-identical (I1); `metrics.json` is untouched.
* **The lane wall.** C3a-2025 −11.2 % is a scored price metric from the keeper's own
  `metrics.json`, independent of any probe, and stays **owner-court**
  (`DECISION-CARD-nyiso148-2025-level-remainder` Q1). What §4 unsettles is the *decomposition* that
  sized the offer-position component at a quarter — not the wall. **No `ST_GAS` offer lever was
  opened.**
* **Every DO-NOT-REDO cell.** The loss surface, the post-solve transform, the capacity/label-basis
  mismatch and `ramp_envelopes`-as-dominant-carrier are untouched and stay closed. nyiso-180 §3's
  structural refutations (a) and (b) are independently **re-confirmed** by §4.1: the reconstruction
  matches the LP exactly with no delivery factor and no price transform anywhere in the identity.
* **`class_band_hourly`**, the nyiso-180 sidecar. Not used here (the object is per-unit) and not
  disturbed.

---

## 8. Honest expected value — what is NOT delivered

* **No lever, and none was available.** Pre-declared in PREREG §3 in every branch. The result is a
  retired statistic, not a mechanism.
* **The C1-2023 `ST_GAS` +3.86 TWh gate is not moved, and nothing here moves it.** This session
  removes a *false explanation* for it; it does not supply a true one. The class is still
  +3.86 TWh over in 2023 and that object is untouched.
* **`Ω` is not decomposed into per-row terms.** The parallel lane's §3 limit is inherited verbatim.
  §6.4 bounds `Ω` as tiny but attributes none of it. The reserve rows are neither implicated nor
  exonerated.
* **My own I3 failed and I did not adjudicate my headline gates.** G-D and G-P are reported as
  measured with their verdict words withheld. The root-cause result in §4–§5 does **not** rest on
  them — it rests on an exact identity — but the session's *pre-registered* question ends
  unadjudicated, and that is a real cost of a bar I chose badly.
* **§4 is post-hoc.** It was not pre-registered, it was found by chasing a discrepancy the gates
  surfaced, and it is labelled as such throughout. Its strength is that it is an identity with no
  threshold, reproducible by anyone from the committed artifacts plus one replay.
* **nyiso-179's remaining conclusions are flagged, not re-derived.** §7 names them; re-measuring
  them is the successor's work, not a claim made here.
* **The `unit_hourly` frame stays uncommitted** at 16–17 MB/yr, so every result here needs the
  ~15-minute control replay to reproduce. That is a real reproducibility cost and it is named, not
  hidden.

---

## 9. Governance

* **Rule 1 `[R-STRUCT]`** — no residual consulted in choosing what to measure; nothing adopted or
  rejected on whether it moved a fit. The correction makes the *instrument* faithful, not the score.
* **Rule 13 `[R-MEASURED]`** — nothing pinned to actuals. Every gated quantity is a model-internal
  LP output on the keeper's own recipe.
* **Rule 14 `[R-ACCURATE]`** — this rule is the whole finding: a reconstruction that omitted two
  armed terms was silently compensating, and the accurate offer is kept even though it dissolves
  three sessions' object.
* **Rule 15** — the control replay is bit-identical (I1) and is an instrument, not a run; nothing
  registered, correctly.
* **Rule 16 `[R-ALLYEARS]`** — one invocation, all three years from the bundle's own `meta.json`,
  sequential (rule 12).
* **Rule 19 `[R-ONE-MECH]`** — nothing added, so nothing to reconcile. §4 is this rule read
  backwards: two armed mechanisms were **missing** from a measurement, not stacked in a model.
* **Rules 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** — **zero parameters touched, zero swept, nothing
  re-derived.**
* **Rule 22 `[R-HOLDOUT]`** — every year is 2023 / 2024 / 2025. NYISO is absent from both `complete`
  and `final`; **no marker was requested**; the holdout spend freeze is untouched.
* **Rule 24 `[R-REGISTRY]`** — **no new tunable**, no env-var knob, no gate flag.
* **Rule 25 `[R-ISO-SCOPE]`** — NYISO only; only the NYISO matrix shard edited.
* **Rule 27 `[R-PUSH]`** — **no existing source file was modified.** All three probes are new files;
  the parallel lane's probe was run **unmodified**. `src/market_sim/` is untouched.
* **Rule 28 `[R-MECH-MATRIX]`** — §10.

## 10. Matrix (rule 28 b)

NYISO shard only. **No verdict moves.**

* **`unit_network_layer_sidecar` stays `K`**, re-stamped with this session's evidence — the
  PR #4650 `mc`/`red_cost` columns are exercised for the first time, the sidecar is validated
  against the LP to `max|d| = 0`, and its 16–17 MB/yr size is recorded against the parallel lane's
  own 5 MB commit threshold. (The cell still read `nyiso-116`; that lane's stamp was not made.)
* **`energy_reserve_coopt` stays `K`**, annotated with G-R's one-sided **INCONCLUSIVE** reading and
  the `Ω` bound — explicitly **not** an exoneration.
* `ramp_envelopes`, `offer_curve_by_group` and `dual_fuel_switching` are **not** re-opened and
  their cells are not rewritten.

## 11. Handed forward

1. **RETIRE `R = mo / itm`.** It is defective twice over — a reconstructed offer missing two armed
   terms (§4), and numerator/denominator over different bin populations (§5). **Do not cite
   0.767 / 0.522 / 0.740, the 3.84 / 9.09 / 3.99 TWh object, or the "~1,000 MW sustained level
   gap" again.** The well-formed replacement is the matched-population ratio, **0.992 / 0.991 /
   0.992**, un-run **0.073 / 0.061 / 0.070 TWh**.
2. **REPAIR `nyiso179_st_gas_offer_position.build_year()` before reusing it.** It is cited as a
   reusable instrument in the standing brief ("reuse it; do not re-derive it"). As it stands it
   under-states the NYISO gas offer by \$9.6–15.4/MWh. The repair is two lines — pass
   `resolve_carbon_price(cfg_y, year)` and call `apply_gas_offer_margin` — and
   `nyiso181_offer_reconstruction_repair.py` carries the exact form plus the closure proof.
   **This session did not edit that probe**, because doing so would silently rewrite the basis of
   the published nyiso-179 record; the repair belongs in a session that re-derives the numbers
   that depend on it.
3. **RE-DERIVE nyiso-179's G3, G4 and the 62.4 / 24.6 / 13.0 decomposition** on the repaired offer
   (§7). The 2025-deficit split in particular is load-bearing in the lever queue and in the
   standing brief, and its instrument carried the defect.
4. **A general audit is warranted, and is NOT NYISO's alone.** The defect class is *a probe
   reconstructing the LP's offer outside the solve and omitting a term the runner installs*.
   `unit_hourly.mc` now makes the check exact and cheap for any ISO: reconstruct, compare, require
   `max|d| = 0`. **CAISO and NEISO also carry state carbon programs**, so the RGGI/CARB limb is not
   NYISO-specific. Rule 25 kept this session inside NYISO; the cross-ISO sweep needs its own
   session.
5. **The C1-2023 `ST_GAS` object is open and unexplained**, with one live explanation fewer.
6. **UNCHANGED and not opened:** C3c (SUPPORTING, not lone); C3a-2025 (owner-court); the
   measured-availability family, the merit guard, an `ST_GAS` duty curve, `gas_st_startup_cost`,
   `gas_st_committed_hr_mult`; `ramp_envelopes` as dominant carrier; the missing rung.
