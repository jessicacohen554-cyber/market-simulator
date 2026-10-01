# ADDENDUM caiso-281 — Gate E: does the CAISO-specific marginal-HR bias survive on the DA basis?

**Charter:** `docs/PRECOMMIT-caiso281-is-the-marginal-hr-bias-a-measured-input-defect-2026-09-13.md`
**Prior addendum:** `docs/ADDENDUM-caiso281-the-diurnal-coincidence-leg-2026-09-13.md` (Gate D).
**Date:** 2026-09-13 · **LP budget: still ZERO** · keeper unchanged · nothing promoted.

## Why this leg, and why it is not "acting on the owner item"

The charter's Gate A2/B measured that the model's **physical** CC heat rate is right — the model's
lowest CC band sits within +0.13/+0.24 MMBtu/MWh of the same plants' CAMPD-measured high-load heat
rate, and the measured offer surface's own `base_hr` (7.442) independently agrees. So the
+1.024 sits in the **offer ladder above base**, which is a measured surface.

That surface's `_provenance.source` is **`PUB_DAM_GRP` — CAISO OASIS Public Bid Data, i.e.
DAY-AHEAD bids.** C3a gates on **`rt_lw`**, a real-time benchmark. A DA-bid-derived marginal-cost
input scored against an RT price is a **basis** question about the test, which is exactly what
handoff §5 flags as the standing owner item.

Handoff §5 says **do not act on it unilaterally**, and this leg does not: switching a benchmark is
acting; **measuring whether the basis explains the bias is the evidence the owner's ruling needs.**
No benchmark is changed, no scorer is touched, no verdict is recomputed.

## Gate E — the rule, fixed before the number

Reuse `scripts/probes/_caiso277_crossiso_hr.py`'s construction **unchanged** —
`dHR(month) = (price_model_lw − price_actual_lw) / gas`, with `gas` =
`data.fuel.plant_prices.iso_monthly_gas_prices` applied to **both** sides — and swap only the
actual series: `avgLMP.rt_lw_mon` → `avgLMP.da_lw_mon`. CAISO only (rule 25 `[R-ISO-SCOPE]`).

**G-REPRO (hard stop):** the RT leg must reproduce caiso-277's CAISO common-window figure
**mean dHR = +0.534** over 2023–2025 (36 ISO-months) to within **±0.05**. If it does not, the
construction is not caiso-277's and **Gate E is abandoned, not adjusted.**

**Metric:** mean `dHR_DA` and its one-sample *t* vs 0 over the same 36 months.

* **E-BASIS-EXPLAINS:** `|mean dHR_DA| ≤ 0.15` **and** `|t| < 2.0` → the CAISO-specific bias is a
  **DA-vs-RT basis artifact of the test**, not a defect of marginal-cost formation. This is
  evidence for the owner's §5 ruling; it changes nothing on its own.
* **E-KILL:** `mean dHR_DA ≥ +0.35` **and** `|t| ≥ 2.0` → the bias survives the basis change, so
  the basis does **not** explain it and the DA reading is not a rescue.
* Otherwise **INDETERMINATE**, reported as such.

2022 is **reported separately and is not in the gate** — it is outside caiso-277's common window,
and pooling it would let the single most extreme year in the record drive a 36-month statistic.

## The standing counter-evidence, recorded before the number so it cannot be dropped

caiso-277 measured the bias as present across **2023–2025 — the very trade years the offer surface
was fitted on.** An in-sample bias is evidence **against** a vintage explanation of 2022 (register
item N-CA-2), and it must be reported whichever way Gate E lands. Handoff §5's own numbers already
say DA is **not** a uniform rescue: 2023 over-corrects to −9.39 %. Gate E asks only whether the
*heat-rate* bias — a different statistic from the percentage gap, because it divides by gas —
vanishes on the DA basis.
