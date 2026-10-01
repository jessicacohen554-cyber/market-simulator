# PREREG nyiso-214 — the EIA-860 `nameplate − net_summer` gap is read TWICE inside `CC_REGULAR`, and that double reading is the within-class merit allocator

**Session:** nyiso-214, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-1m6c2q`, on `main` at `c5369f27`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — CALIBRATED, grade 7/8, fails 0, C3c the lone
ledgered caveat.

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES TO FIX.** NYISO's keeper reads CALIBRATED with **zero
failing criteria** across 2023–2025. Nothing in this document is selected because a residual
moved (rule 1 `[R-STRUCT]`, rule 23 `[R-FROZEN-DERIVE]`). The rubric failures that exist are on
the **2022 held-out rung**, which rule 22 `[R-HOLDOUT]` forbids identifying anything against;
they are named nowhere below as a target.

**This is a ZERO-LP session by construction.** No solve is planned, no bundle is produced, no
year is spent. Rule 29 `[R-SCREEN]` step 0 is the whole of the work.

---

## 0. The object, and what is already in hand BEFORE this document

The named object handed forward by nyiso-213 is **(B)**: Cricket Valley 57185 runs 4,109.4 GWh
against a 4,861.8 GWh meter in 2025 **at corrected availability**, while `CC_REGULAR` as a class
**over**-runs actual and got further above it with the seam repair. The newest H-class CC in
NYISO under-runs its own meter while its class over-runs — a merit/offer-position question
*inside* `CC_REGULAR`, cleanly separated from capability by nyiso-213.

**Disclosed in full (rule 29 step 0 work already executed this session, on the keeper's own
committed recipe, before this PREREG was written):**

1. **The efficiency hypothesis is REFUTED.** A `fleet_only` rebuild of the keeper's 2025 fleet
   gives 57185 a base heat rate of **7.013 MMBtu/MWh**; its own CAMPD gross heat rate reads
   6.854 / 6.803 / 6.721 in 2023/24/25, a model/measured ratio of **1.023 / 1.031 / 1.043** —
   statistically indistinguishable from every other material `CC_REGULAR` plant (55405
   1.017–1.028, 55375 1.028–1.037, 56196 1.011–1.036, 56234 1.035–1.041, 56940 0.992–0.996).
   **The model does not penalise Cricket Valley on efficiency**, and a per-plant measured
   heat-rate repair is NOT this object's lever. Recorded as a clean negative.
2. **The within-class merit spread is carried by the PEAK-BAND SHARE, not by heat rate.** Base
   heat rates across the eight material (≥ 350 MW) `CC_REGULAR` plants span 6.75–7.38
   (±4 %), while the peak-band share spans **0.0 %–22.6 %**: 57185 **22.6 %**, 57664 16.9 %,
   56940 15.1 %, 56234 9.1 %, 2539 9.0 %, 55375 6.2 %, and **55405 Athens 0.0 %** and
   **56196 Zeltmann 0.0 %**. The peak tranche is priced at `peak = 2.25 × base` (mean
   mc $97.74/MWh at 57185 against $45.1 on its committed tranche), so a plant's peak share is
   what decides where it sits in the class merit order.
3. **Prior sessions' numbers, cited not re-derived:** nyiso-194 §1 measured the band SIZE wrong
   against the plants' own reach (860 gap 22.6 / 28.2 / 16.9 % vs CAMPD reach 5.7 / 5.8 / 0.6 %)
   and found **no measured quantity identifying a HIGHER peak offer** (measured top-band
   incremental HR 1.0–1.5× base against a registered 2.25×). nyiso-198 measured that 203.7 of
   296.4 MW (69 %) of 57185's peak band sits on EIA-860 rows flagged `X`, not `Y`.

**What is NOT in hand and is the subject of this document:** the EIA-860 capability gap at the
two material plants that receive **zero** peak band, and whether the gap that creates the peak
band is the SAME quantity a second armed mechanism is simultaneously reading as ambient derate.

## 1. The structural claim to be tested

`cc_duct_peaking_pct` (`data/fleet/campd_bins.py` L1817–1889) assigns a plant's peak-band share as
`100 × max(0, Σ(nameplate − net_summer)) / Σ nameplate` **if any of the plant's CC rows carries
`Duct Burners == Y`**, and **0.0 otherwise**. Its own docstring defends the asymmetry:

> "non-duct CC plants get 0.0 — they have no duct-firing increment … for non-duct plants that
> same gap is ambient derate, already modeled by `_SUMMER_CLASS_DERATE`."

The claim under test is that this defense **does not survive at a duct-flagged plant**, because
`cc_nameplate_summer_derate` — armed on this keeper, and rebased onto the reconciled capacity by
nyiso-213 — reads the *same* EIA-860 `net_summer` at the *same* plants as ambient derate and
removes it in Jun–Sep. If so, one physical quantity carries two contradictory readings at the
same plant simultaneously (rule 19 `[R-ONE-MECH]`), and which reading a plant gets is decided by
a flag reported on a row grain the quantity is not measured at.

## 2. Predictions — declared BEFORE any of P1–P4 is measured

All four are measured from the **keeper's own active EIA-860 vintage** and the keeper's own
`fleet_only` rebuild. Each states a sign and a magnitude.

### P1 — the double reading exists and is material
Count the NYISO `CC_REGULAR` plants that BOTH (a) receive a nonzero `cc_duct_peaking_pct` peak
band and (b) take a Jun–Sep `cc_nameplate_summer_derate` multiplier `< 1`.

**Declared: ≥ 6 such plants, carrying ≥ 400 MW of peak band between them.**

### P2 — the asymmetry is NOT explained by the physical gap *(the load-bearing prediction)*
For the two material plants that receive **zero** peak band, 55405 Athens and 56196 Zeltmann,
measure their own EIA-860 `100 × (Σ nameplate − Σ net_summer) / Σ nameplate`.

**Declared: ≥ 8.0 % at EACH of 55405 and 56196** — i.e. their gaps are of the same order as the
Y-flagged plants', so the zero band they receive is a property of the FLAG, not of the physics.

**THE OUTCOME THAT HURTS THIS SESSION'S PREFERRED ANSWER, declared as a live possibility:** if
either plant reads **< 4.0 %**, the selection rule is tracking the physical quantity at exactly
the two plants this object names, the docstring's defense holds, and **the framing in §1 is
refuted.** That refutation is then this session's result and no successor is proposed.

**Declared disjoint third outcome:** either plant lands in **[4.0 %, 8.0 %)** — the rule is
partially tracking, the evidence is indeterminate, and the session reports the object
**unresolved** and proposes no lever in either direction.

These three are mutually exclusive and exhaust the real line.

### P3 — reproduction bar, and the VOID condition
At 57185, the share of the plant's total `Σ(nameplate − net_summer)` gap carried by the
`Duct Burners == Y` rows alone.

**Declared: < 40 %** (nyiso-198 measured 31 % on its own vintage; this is a REPRODUCTION of a
prior session's census, disclosed as such and not a discovery).

**VOID:** if it reads **> 50 %**, this session's EIA-860 instrument or active vintage differs
materially from nyiso-198's, **the entire census below is void**, and that discrepancy — not any
claim about the object — becomes the session's reported result.

### P4 — the two mechanisms provably read the same EIA-860 pair
At 57185: (i) `peak_MW / carried_capacity_MW` equals `cc_duct_peaking_pct / 100` to within
**0.2 pp**; and (ii) the Jun–Sep summer multiplier equals `min(1, net_summer / carried_capacity)`
to within **0.001**.

**Declared: BOTH hold.** A miss on either means the two mechanisms are not reading one pair and
§1's rule-19 characterisation is wrong as stated.

## 3. What this session will and will not do

* **Will:** measure P1–P4 at zero LP; report every number at full magnitude; update the NYISO
  matrix shard (rule 28(b)); write a FINDING; and, **only if P2 fires as declared**, open an
  **owner decision card** — because a symmetric membership construction is a NEW
  `ScenarioConfig` field needing its own matrix row (rules 24 / 28(c)) and the choice between
  candidate forms is not this lane's to make.
* **Will NOT:** build, arm, or screen any mechanism; spend any solve; touch `phys_*` or any band
  multiplier (rule 1's carve-out conditions are not met and no price change is proposed);
  re-open `cc_duct_peaking_row_scoped`'s own re-test, whose matrix condition is a three-way
  paired arm on 2025 and explicitly "never alone"; or touch any of the FIVE PENDING OWNER
  RULINGS (nyiso-206 / -207 / -203 §6 / DECISION-CARD-nyiso193 §5 / nyiso-208).
* **Rule 22:** training-tier only. No out-of-training year is solved, scored or registered.
  `final` untouched, the locked-test freeze untouched, 2020/2021 unspent.
* **Markers:** none are this session's to move; no promotion is contemplated, so D-5(b) does not
  attach.

*(Committed and pushed before P1–P4 were measured. nyiso-214, 2026-09-07.)*
