# PREREG miso-118 — the four `CC_CHP` plant-level heat-rate outliers: basis artifact, or per-plant input error?

Session miso-118, 2026-08-03, branch `claude/miso-118-backcast-calibration-f0ngwe`,
off `origin/main` at `10c23ab`. **Written and pushed BEFORE the probe runs.**

**Phase 0 is NO-LP.** No solve is authorized by this pre-registration. Its only
output is a verdict on *what the four plants' gaps are*, and — only on the REAL
branch — a charter for a successor. The keeper
(`2026-08-03-miso-117b-ct-heat`, bundle `results/calibration/miso117_ctheatrate_B`)
is **not** touched.

---

## 1. The object

miso-116 §3, closing out the withdrawn `CC_CHP` heat-rate finding, reported a
residual it explicitly did **not** act on:

> 4 of 14 matched plants (52.7 % of matched capacity) still sit below 0.85×
> CAMPD — 10745, 55089, 55259, 55088, all on the measured artifact. A per-plant
> item under rule 14 `[R-ACCURATE]`, not a class-level mispricing.

Published ratios (miso-116 probe part E, 2023, `model_hr / campd_gross_hr`):

| plant | name | model cap (MW) | model HR | CAMPD-CC gross HR | ratio |
|---|---|---:|---:|---:|---:|
| 10745 | Midland Cogeneration Venture | 1,479 | 8.82 | 10.90 | 0.810 |
| 55089 | Taft Cogeneration Facility | 739 | 8.01 | 12.27 | 0.653 |
| 55259 | Whiting Clean Energy | 513 | 9.39 | 11.70 | 0.802 |
| 55088 | Dearborn Industrial Generation | 350 | 8.35 | 10.22 | 0.817 |

All four carry `flag == "ok"` in
`data/raw/_processed-legacy/chp_power_only_heat_rates_MISO.csv` and are
therefore **already repriced** by the armed `measured_chp_heat_rates`
mechanism; 55088 additionally carries a `CT_CHP` row on the same plant-level
rate.

**Materiality, recorded ex ante.** `CC_CHP` is **3.03 / 3.02 / 2.46 %** of MISO
load in the keeper's own P1 (`19.41 / 19.45 / 16.33 TWh` against
`640.99 / 644.63 / 663.81 TWh`), i.e. **above** the rule 20 `[R-FORCED-BUDGET]`
2 % materiality floor in all three years. The class is gate-relevant; the four
plants are 3,081 of 5,852 matched MW.

## 2. The question, stated so it can be answered wrong

**Is each plant's sub-0.85 ratio a MEASUREMENT-BASIS artifact of the comparator
(as miso-116's own class-level result turned out to be), or a real error in the
per-plant input the model loads?**

This is the miso-116 trap restated at plant grain: that session's two withdrawn
findings both came from a comparator whose two sides were not the same
quantity. The comparator used here is the same one, so it inherits the same
hazard and must be decomposed before any charter.

## 3. The three quantities, and why they need not agree

* **Model rate** — `(PLHTIAN + CHPCHTI) / PLNGENAN`: eGRID **total** plant fuel
  over eGRID **net** generation. Whole-plant fuel, whole-plant net electricity.
* **miso-116 comparator** — CAMPD `heatInput / grossLoad` summed over the
  plant's `unit_family == "CC"` CEMS units: **CEMS-reported** fuel over
  **CEMS-reported gross** electricity.
* **Basis-matched comparable (this session)** —
  `HR_match = CEMS_total_heat_input / net923`: metered fuel over the same NET
  denominator the model divides by.

Three ways they can diverge without the model being wrong: (a) gross > net, so
the comparator's denominator is systematically the larger one; (b) the CEMS
gross-load channel can miss electric output eGRID counts (steam turbines with
no fuel of their own, sub-Part-75 units) — the defect
`FINDING-miso98-chp-sector-ab-2026-07.md` §6.1 names as the reason the CEMS
route was abandoned for CHP; (c) the `family == "CC"` filter can truncate
numerator and denominator asymmetrically at a mixed facility.

## 4. Hypotheses and their tests (all no-LP)

| id | hypothesis | test | branch if true |
|---|---|---|---|
| **H-A** | CEMS gross-load coverage deficit | `G = CEMS_grossLoad_CC / PLNGENAN`. `G < 1.0` is **physically impossible** for a matched population (gross ≥ net always) and proves the comparator's denominator is short | BASIS |
| **H-B** | `family == "CC"` truncation | heat input and gross load by family per plant; share outside `"CC"` | BASIS |
| **H-C** | eGRID-vintage staleness (one 2023 rate applied to 2024/2025) | per-year `CEMS_total_heat / CEMS_gross`; year-on-year move vs the model's frozen rate | REAL (re-derive ask, not a solve) |
| **H-D** | mis-key / wrong rate loaded | loaded `gen.heat_rate` vs artifact `heat_rate`, per plant, per year | REAL |
| **H-E** | one plant rate over a mixed facility (55088 CC_CHP + CT_CHP) | CAMPD family-split measured rates at the plant | REAL |

**Decomposition identity, pre-registered as the completeness check.** With
`cems_vs_egrid_total ≈ 1`, miso-116's ratio must satisfy

```
ratio  =  model_hr / (CEMS_heat_CC / CEMS_gross_CC)
       ≈  (CEMS_heat_CC / CEMS_heat_total)  ×  (CEMS_gross_CC / PLNGENAN)
```

If the right-hand side reproduces the published ratio to **≤ 0.005 absolute**,
the gap is fully accounted for by measured basis terms and there is **no
unexplained residual** left for a model defect to occupy.

## 5. Decision rule (fixed before measurement)

Per plant `p`, over 2023 / 2024 / 2025:

* **BASIS-ARTIFACT** — `R_basis(p) = model_hr / HR_match ∈ [0.90, 1.10]` in
  **≥ 2 of 3** years, **and** H-A or H-B fires (`G < 1.0`, or ≥ 10 % of the
  plant's CEMS heat input or gross load outside family `"CC"`).
  → the model input is correct on its own basis; **NO CHARTER, NO SOLVE.**
* **REAL INPUT ERROR** — `R_basis(p)` outside `[0.85, 1.15]` in **≥ 2 of 3**
  years. → charter a successor naming the specific defect (H-C / H-D / H-E),
  with its own pre-registration; **still no solve in this session.**
* **INDETERMINATE** — anything else, or a fired kill. → report, no charter.

The verdict is **per plant**; a mixed outcome is reported as a mixed outcome
and never averaged into one headline.

## 6. Kills (a fired kill stops the verdict, it does not bend it)

* **K1 — reproduction.** The probe must reproduce miso-116 part E on miso-116's
  own basis before any correction is applied: the same 14 matched plants, the
  same 5,852 MW, the same four plant codes, the 52.7 % capacity share, and the
  four 2023 ratios to **± 0.005**. Failure ⇒ STOP, report the discrepancy, no
  verdict.
* **K2 — flag fidelity (miso-116 §7).** The model side is built from the
  CURRENT keeper's `run_config.json` (`miso117_ctheatrate_B`), read from the
  file. Assert `measured_chp_heat_rates` and `measured_ct_heat_rates` are both
  `True` **as read**, not as hardcoded. A default-config fleet is the exact
  error that produced miso-115 §4.
* **K3 — net-basis identity.** The derive claims `net923 / PLNGENAN = 1.000000`
  on MISO thermal plants. Verified per plant here. If it fails for a plant,
  `HR_match` is not comparable to the model rate and that plant is
  **INDETERMINATE**, not judged.
* **K4 — CEMS completeness.** `cems_vs_egrid_total` must be within
  `1.00 ± 0.02` for the plant. Outside it the CEMS side is itself incomplete
  (sub-Part-75 units) and the plant is reported, not judged.
* **K5 — materiality.** `CC_CHP` ≥ 2 % of MISO load. Measured 3.03 / 3.02 /
  2.46 % (§1). Recorded ex ante; does not gate the verdict, gates whether the
  object is worth a successor.

## 7. Predictions (stated so they can fail)

1. **H-A fires on at least three of the four plants**, with `G < 1.0` —
   i.e. CEMS gross load below eGRID net generation.
2. **The decomposition identity closes to ≤ 0.005** on all four plants.
3. **`R_basis` lands in `[0.90, 1.10]`** on all four → verdict BASIS-ARTIFACT,
   no charter.
4. **55088's `CT_CHP` row is the one genuinely open sub-item** — the plant-level
   rate applied across two prime-mover classes — and it survives §5 as a
   reported note rather than a charter, because 55088's `CT_CHP` capacity
   (165 MW) is far below any class materiality line.
5. **H-C does not fire**: per-year measured rates move < 10 % year-on-year at
   all four plants.

Predictions 1–3 and 5 are the ones that would make this a null result. If
prediction 3 fails on any plant, that plant is a real defect and the session
owes a charter.

## 8. Contamination declared

**Not blind.** The session read `FINDING-miso116`, `FINDING-miso117`, the MISO
calibration log and the matrix before writing this, and the handoff itself
names the basis-artifact hypothesis. Worse than that, and stated plainly: an
arithmetic sanity check on the committed artifact was run **before** this
document was written — dividing plant 10745's eGRID total heat input
(86,087,081 MMBtu) by miso-116's published CAMPD-CC rate (10.90) gives an
implied CEMS gross of ≈ 7.90 M MWh against eGRID net of 9.76 M MWh, which
already points at H-A. So prediction 1 is **not** an independent forecast for
plant 10745; it is an extrapolation from one plant to the other three.

What that check cannot pre-determine, and what this document fixes in advance:
the decision **thresholds** (§5), the **completeness identity** (§4), the
**kills** (§6), and the per-plant verdicts for 55089 / 55259 / 55088 — of which
55089's published ratio (0.653) is far enough from the other three that the
same explanation is not obviously available to it.

## 9. Rule duties this session will discharge

* **Rule 15** — Phase 0 produces no run; if it stays no-LP there is nothing to
  register, and that is stated rather than assumed.
* **Rule 16** — the 2023–2025 span is measured in one pass; no single-year
  claim.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 ONLY. MISO holds no
  `calibration-complete` marker; no holdout year is solved, scored **or read**.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no derive script is re-run. A defect found
  in the artifact is documented; it is not patched against a residual.
* **Rule 24 / 26 `[R-REGISTRY]`** — every crosswalk is the repo's own
  (`states_for_iso`, `unit_family`, `_hour_index_8760`,
  `measured_chp_heat_rates`, `pooled_factor_map`). No hand map.
* **Rule 28 duty (b)** — the `measured_chp_heat_rates` MISO cell is annotated
  in this session with this session's evidence, whatever the verdict.
