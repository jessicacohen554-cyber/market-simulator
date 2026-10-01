# FINDING — caiso-167: the CAISO import price basis is **REFUSED EX ANTE ON REACH**, and the surplus-regime corridor basis is measured for the first time — its **SIGN IS INVERTED**, the model's own wedge is **NEVER NEGATIVE in any of 26,280 hours**, and the one never-adjudicated import-side mechanism (a seam loss surface) moves it by **1.6/0.1/1.4 % of the defect, in the wrong direction**. Lever-queue item 2 is **SPENT — both halves of the corridor/export-path family are now closed**. NO LP, NO SOLVE, NO DERIVE, keeper unchanged (2026-08-04)

**Session** caiso-167 · **Date** 2026-08-04 · **Branch**
`claude/caiso-import-price-basis-8xx8rb` · **Base** `b0017df5`

> **Session numbering.** The prompt opened this lane as "caiso-165". That id was
> already SPENT by the DLAP intake that landed at `76ecfc11` earlier the same
> day, and `caiso-166` is claimed by the in-flight measured-loss-zones prereg
> (`PRECHECK-caiso166-measured-loss-zones-2026-08-04.md`, committed at
> `6c2dbfd5`). This lane is therefore **caiso-167**. Nothing in either of those
> lanes is touched here: this session writes no derive script, does not re-derive
> `CAISO_loss_surface.csv`, and does not read a residual.

**Incumbent CAISO keeper** `2026-08-04-caiso164-zonal-loss-surface`
(CALIBRATED-WITH-CAVEATS, 2 owner-ledgered caveats, 0 FAILs). **Unchanged by
this session.**

**Target** `docs/mechanism-testing-matrix.md` §5.2 lever-queue **item 2**, the
corridor/export-path congestion family — specifically its **one live half**,
"the **import** side's price basis under the surplus regime", after caiso-142/143
closed the export half with nothing unbuilt.

**Matrix cells touched** new row `caiso_seam_loss_surface` CAISO `→ G`
(ex ante, no solve). `zonal_loss_surface` CAISO stays `K` — untouched.

**Method** Phase-0 decomposition off **committed artifacts only**: the keeper
bundle's P1 hourly sidecars, the measured intertie scheduling-point LMP, and
CAISO's committed day-ahead component record. Reproducible in one command:

```
python scripts/probes/caiso167_import_basis_phase0.py
```

Artifact: `results/calibration/_caiso167_import_basis_phase0.json`.

---

## §0 — the one-paragraph result

The model's DSW corridor wedge (`SP15_rest` dual − `WECC_DSW` dual) is
**+7.08 / +9.57 / +7.10** $/MWh in surplus-regime belly hours. The **real**
basis those same hours carry (`TH_SP15_GEN-APND` − `PALOVRDE_ASR-APND`) is
**−1.17 / −3.82 / −1.83** — *negative*, in 62.2/63.8/69.6 % of them. So the
defect is **+8.24 / +13.39 / +8.93** $/MWh, and it is a **sign inversion**, not
a magnitude miss. The model cannot produce the measured sign at all: its wedge
is `> 0` in 45.5/62.4/53.4 % of those hours, exactly `0` in the rest, and
**`< 0` in 0.000 % of all six corridor-years** — the seam is lossless by
construction, so a nonzero dual gap means the corridor is at its *import* bound,
and the export bound is never reached (both export sinks dispatch 0.00 MW in all
26,280 hours, caiso-121). The single never-adjudicated import-side price-basis
mechanism — extending caiso-164's loss surface to the WECC seam links, which
`_caiso_internal` excludes — is **measured to move that wedge by +0.128/+0.017/
+0.127 $/MWh (1.6/0.1/1.4 % of the defect) and in the wrong direction**. It is
**refused ex ante; no solve was spent.** With the export half already closed at
caiso-142/143, **the corridor/export-path family is closed on both halves and
item 2 is spent.**

---

## §1 — the measurement, and why it is not the caiso-121 number

caiso-121 measured the model's belly wedge against the **hub level** and
reported +$4.39/+$13.53/+$8.00, attributing 59–101 % to corridor congestion. It
had no measured comparator for the *basis* — the question "what should
`CA − tie` be in these hours?" was never asked, and was implicitly answered
`≈ 0`. It is not zero; it is negative. Correcting the comparator makes the
model's error **larger** in 2023 and 2025 than caiso-121 stated:

| year | corridor | n | measured basis | measured `< 0` | model wedge | **defect** |
|---|---|---:|---:|---:|---:|---:|
| 2023 | DSW | 942 | **−1.167** | 62.2 % | +7.077 | **+8.244** |
| 2024 | DSW | 1,559 | **−3.824** | 63.8 % | +9.569 | **+13.393** |
| 2025 | DSW | 1,579 | **−1.825** | 69.6 % | +7.100 | **+8.925** |
| 2023 | PNW | 466 | **−0.594** | 51.3 % | +3.348 | **+3.942** |
| 2024 | PNW | 783 | **−3.689** | 60.9 % | +3.411 | **+7.101** |
| 2025 | PNW | 790 | **−0.802** | 59.9 % | +1.534 | **+2.335** |

Regime cut carried verbatim from the prior lanes and **not chosen here**: belly
= Pacific `[09, 16)` (caiso-165 §2), surplus = measured CA hub ≤ $20/MWh
(caiso-120), re-expressed on the day-ahead component record because that is the
series caiso-164 and caiso-165 both decomposed and the model is a day-ahead-shaped
single clearing.

**The result is not an artifact of that cut.** The sign inversion survives
removing the surplus filter and removing the belly window entirely:

| cut | 2024 DSW measured / model | 2025 DSW measured / model |
|---|---|---|
| all hours | **−0.697** / +3.498 | **−0.253** / +3.017 |
| belly | **−1.112** / +8.707 | **−0.742** / +6.594 |
| belly + surplus | **−3.824** / +9.569 | **−1.825** / +7.100 |

The surplus cut *concentrates* the defect; it does not create it.

---

## §2 — rule 19 `[R-ONE-MECH]`: the wedge is **not** the caiso-164 object

`model/interchange/caiso.py::_caiso_internal` excludes every link touching a
`WECC*` node from the caiso-164 one-way loss split, so **the two seam corridors
are lossless in the incumbent keeper**. For a lossless link the dual gap across
it is zero unless the link sits at a bound. The census reads that out directly:

| year | corridor | wedge `> 0` | wedge `≈ 0` | wedge `< 0` | measured basis `< 0` |
|---|---|---:|---:|---:|---:|
| 2023 | DSW | 45.5 % | 54.5 % | **0.000 %** | 62.2 % |
| 2024 | DSW | 62.4 % | 37.6 % | **0.000 %** | 63.8 % |
| 2025 | DSW | 53.4 % | 46.6 % | **0.000 %** | 69.6 % |
| 2023 | PNW | 29.4 % | 70.6 % | **0.000 %** | 51.3 % |
| 2024 | PNW | 28.1 % | 71.9 % | **0.000 %** | 60.9 % |
| 2025 | PNW | 20.3 % | 79.7 % | **0.000 %** | 59.9 % |

So the wedge is **pure corridor/interface rent** — not loss, not the promoted
mechanism — and the model's corridor is **one-sided by construction**: it can
congest inward and it cannot congest outward. In the two-thirds of hours the
real market prices CA *below* the tie, the model prices it at or above.

**Where the CA belly over-price actually sits.** Decomposing the model's
belly-surplus CA level error into its two additive parts (they sum exactly):

| year | model CA − measured CA | = corridor wedge defect | + import-node level defect |
|---|---:|---:|---:|
| 2023 | +7.438 | **+8.244 (110.8 %)** | −0.806 (−10.8 %) |
| 2024 | +17.289 | **+13.393 (77.5 %)** | +3.895 (22.5 %) |
| 2025 | +12.161 | **+8.925 (73.4 %)** | +3.236 (26.6 %) |

This **confirms caiso-121's structural read** — the import node is priced
approximately right and the corridor owns the majority — while correcting its
magnitude. It also bounds the whole family: a corridor mechanism that reproduced
the measured basis *exactly* would still leave the CA belly dual **+$3.9 / +$3.2**
too high in 2024/2025.

---

## §3 — the census of import-side price-basis mechanisms is COMPLETE

| # | mechanism | status before this session |
|---|---|---|
| i | tranche offer = measured tie nodal LMP | **armed** (`caiso_import_hub_prices`) |
| ii | OATT point-to-point wheel | **measured** (`CAISO_IMPORT_DELIVERY_BASIS`; the DSW clean rungs carry `(0,0)` — the WEIM/EDAM transfer basis, caiso-142 §E) |
| iii | CARB border-carbon adder | **REFUTED** (caiso-121: the setter is the EF-0 `DSW_surplus_clean` rung and pays none) |
| iv | tranche depth | **demoted to second order** (caiso-121: at-cap in 0.7/20.8/3.5 % of surplus hours) |
| v | corridor import cap | **measured, armed** (caiso-162 per-year caps) |
| vi | **loss on the seam corridor** | **NEVER ADJUDICATED** ← this session |

Item (vi) is a genuine candidate, and its stated reason for absence is
**factually wrong** (§5). It is nonetheless refused, on reach.

---

## §4 — (vi) REFUSED EX ANTE ON REACH, with the numbers

**The instrument is valid at the seam.** CAISO's `LMP = MCE + MCC + MCL`
identity holds at the intertie APNodes exactly as caiso-164/165 proved it for
the seven internal nodes: over the 1,488 hours in which `PALOVRDE_ASR-APND`,
`MALIN_5_N101` and the CA hubs all print, **`MCE` is one system reference to
`0.00e+00` $/MWh**. The seam basis therefore decomposes exactly:

| corridor | window | cut | n | basis | `dMCC` | `dMCL` | loss share |
|---|---|---|---:|---:|---:|---:|---:|
| DSW | 2023-01-01..03-10 | all | 1,488 | +3.792 | +1.367 | **+2.425** | 63.9 % |
| DSW | 2023-01-01..03-10 | belly | 434 | +4.441 | +2.758 | **+1.683** | 37.9 % |
| PNW | 2023-01-01..03-10 | all | 1,488 | +2.285 | +1.097 | **+1.188** | 52.0 % |
| PNW | 2023-01-01..03-10 | belly | 434 | +4.656 | +3.525 | **+1.130** | 24.3 % |

A **real, unrepresented loss component of +$1.13–2.43/MWh** — comparable to the
internal `NP15−ZP26` loss component (+1.176/+1.102/+1.049) that caiso-164 was
promoted for representing. Applying the **frozen caiso-164 estimator**
(`dev_z,m = Σ MCL_z,t / Σ MCE_t`, zero free parameters) to these nodes gives a
seam `eps` of **0.02514 (DSW)** and **0.01242 (PNW)** — the same order as the
armed internal Path-15 values (0.019–0.026).

**And it still cannot reach the defect.** A receiving-end coefficient `1 − eps`
sets `λ_to = λ_from / (1 − eps)` on an interior link, so the wedge moves by
`λ_from · eps/(1 − eps)`:

| year | corridor | defect | signed reach (measured `eps`) | interior-only | over-generous `|λ|` bound | % of defect |
|---|---|---:|---:|---:|---:|---:|
| 2023 | DSW | +8.244 | **+0.128** | −0.027 | 0.353 | **4.3 %** |
| 2024 | DSW | +13.393 | **+0.017** | −0.002 | 0.446 | **3.3 %** |
| 2025 | DSW | +8.925 | **+0.127** | −0.005 | 0.345 | **3.9 %** |
| 2023 | PNW | +3.942 | −0.034 | −0.052 | 0.131 | **3.3 %** |
| 2024 | PNW | +7.101 | −0.035 | −0.052 | 0.184 | **2.6 %** |
| 2025 | PNW | +2.335 | −0.008 | −0.026 | 0.146 | **6.3 %** |

Three things make this a refusal rather than a close call.

1. **The signed reach is ~1 % and points the WRONG WAY on the DSW leg.** The
   defect is the model's wedge being too *positive*; a positive `eps` on the
   import direction makes the receiving end *dearer*, i.e. more positive still.
   The signed movement of **+0.128/+0.017/+0.127** is 1.6/0.1/1.4 % of
   +8.244/+13.393/+8.925 — and additive to the error, not against it.
2. **The `|λ|` column is deliberately over-generous and still small.** It drops
   the sign cancellation (30–51 % of these hours have a negative import-node
   dual, where the loss would move the wedge the other way) and credits the
   mechanism its full effect even in the 37.6–62.4 % of hours where the
   corridor is at a *bound* and the bound, not the loss, sets the wedge. Even so
   it is **2.6–6.3 %** of the defect.
3. **The refusal is robust to the one thing this session could not measure.**
   The committed intertie components cover winter only (§6), so the *belly-month*
   seam `eps` is unknown. Rather than assume the winter value carries, the bound
   is re-run at a **stress `eps` of 0.13 — larger than the maximum within-month
   pairwise `eps` in ANY committed loss surface in the repo** (CAISO 0.05339,
   MISO 0.09427, PJM 0.12746). Even there the over-generous bound reaches only
   **19.3–39.5 %** of the defect (the lone exception, PNW-2025 at 74.5 %, is a
   ratio against a $2.34 defect, the smallest of the six).

Per the standing discipline — *do not spend a solve on a mechanism you can
already show cannot reach the defect* — **no arm was built, no A/B was solved,
no `ScenarioConfig` field was added, and the keeper is untouched.**

---

## §5 — a code premise CORRECTED (no behaviour change)

`_caiso_internal`'s docstring justified the exclusion as:

> "…fictitious pricing nodes with no location, so they have **no published
> delivery-factor deviation to derive one from**, and inventing one would be a
> fitted scalar (rule 5)."

That is **true of the pooled `WECC_import` node and false of the two per-hub
nodes.** Under `caiso_per_hub_intertie` the keeper gives them an exact location
by pricing them off `PALOVRDE_ASR-APND` and `MALIN_5_N101` — real CAISO APNodes
whose `MCE/MCC/MCL` CAISO publishes, 1,488 hours of which are **already
committed**, and from which §4 derived a deviation with the frozen estimator and
**zero fitted scalars**. The exclusion's *conclusion* survives; its *stated
basis* does not. The docstring is corrected in this PR to record the real reason
(reach, this finding) alongside the one that does still hold for the pooled
node — the same correction pattern caiso-142 §E applied to its own §E claim. No
code path changes; `_caiso_internal` returns exactly what it returned before.

---

## §6 — stated limits, not buried

* **The seam `eps` is measured on winter only.** `PALOVRDE_ASR-APND`,
  `MALIN_5_N101` and `CAPTJACK_5_N003` print in `data/raw` for
  **2023-01-01..2023-03-10 (1,488 h)** and nowhere else; the `PRC_LMP` retention
  boundary (~2023-04-24 and moving, caiso-165) is why. The belly-month seam
  loss component is **not measured**, and §4's third leg is the stress bound
  that makes the refusal independent of it. Closing the gap is a bounded OASIS
  fetch of two APNodes for 2024–2025 through the caiso-165 machinery
  (`fetch_caiso_oasis.py --nodes`) — **not done here, and not required for this
  verdict.**
* **The measured basis is the day-ahead one.** The keeper's own import tranches
  are priced off the same day-ahead intertie series, so comparator and input
  agree; no RT series was used.
* **2023 intertie hub coverage is 6,720 of 8,760 hours** in the committed
  parquet. All 2023 rows above are on that support and are labelled `n`.
* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only, hard-filtered in the probe. CAISO
  holds no `complete` marker, so 2022/2019/≤2021/H1-2026 stayed untouched. No
  marker was written.

---

## §7 — what this closes, and the honest re-point

**Item 2 is SPENT. Both halves of the corridor/export-path family are closed.**

* **Export half** — closed at caiso-142/143 with nothing unbuilt: the
  node-level export constraint is algebraically redundant with the corridor
  group's `limit_dn`, a sound export sink is not LP-representable (non-convex
  soundness set), the netback price is not identifiable without a fitted value,
  and the shared-headroom channel is dead (0 of 26,280 corridor-hours).
* **Import half** — closed here: (i)–(v) already adjudicated, (vi) refused on a
  measured reach bound.

**The corridor wedge is a SYMPTOM, and this finding does not claim otherwise.**
Reproducing a *negative* `CA − tie` basis requires CA to be the cheap end at its
**export** limit. That is the export half — and caiso-142 §C established the
governing asymmetry: an export sink is an **absorption column**, so arming one
can only weakly **RAISE** every zonal `λ`, never lower the CA belly dual toward
the measured −$7.07 / −$0.12. **No interchange mechanism, on either side of the
seam, can lower it.**

**Re-point (a POINTER, not a verdict — this session measured nothing on it).**
The residual belongs to the in-state belly supply/demand state that caiso-121's
own physical stack already named, and which no corridor lever can reach: solar
under-curtailed (the model curtails in 11/43/41 % of hours), storage charging
**+1,967/+2,049/+2,244 MW** over measured, hydro **−1,114/−948/−856**, gas
**−859/−784/−636**. That is queue **item 3**'s territory (the storage lane), not
interchange. Whether the belly dual is being held up by the storage charging
bid is **untested** and is the natural successor question — it is *not* asserted
here.

---

## §8 — DO-NOT-REDO (new, binding; extends caiso-142 §H and caiso-143 §I)

1. **Do not re-propose a WECC seam loss surface** without new evidence that
   changes the reach arithmetic in §4. `caiso_seam_loss_surface` is cell `G`.
   A belly-month seam `eps` measurement is *not* by itself new evidence — §4's
   stress leg already covers every `eps` up to 0.13, above anything in any
   committed surface. New evidence means an `eps` **above 0.13**, or a defect
   restated below ~$2/MWh.
2. **Do not re-propose an import-side price-basis lever generally.** §3's census
   is complete: (i)/(ii)/(v) are armed and measured, (iii)/(iv) are adjudicated
   by caiso-121, (vi) is refused here.
3. **Do not treat the corridor wedge as a price lever.** It is one-sided by
   construction (§2) and a symptom (§7). Do not close it with an adder, a
   haircut, a hurdle rate, or a corridor limit chosen to reproduce the measured
   basis — a limit picked to hit the frequencies or magnitudes in §1 is an
   **outcome pin and stays forbidden** (rule 13 `[R-MEASURED]`, rules 5/21/24).
4. **The caiso-121 comparator is superseded.** Quote the defect as
   **+8.24/+13.39/+8.93** (DSW belly-surplus, model wedge minus *measured
   basis*), not +4.39/+13.53/+8.00 (model wedge minus *hub level*). caiso-121's
   attribution is confirmed; only its magnitude is corrected.
5. **The measured seam loss component is real and is recorded as unrepresented**
   (+$1.13–2.43/MWh, §4). It is a known structural-integrity gap on the seam,
   NOT an open lever, and NOT a caveat against the caiso-164 keeper — whose
   scope was explicitly internal links.
