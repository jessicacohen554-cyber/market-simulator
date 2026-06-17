# Backcast measured-data audit — compliance with the "no pinning to actuals" rule

**Date:** 2026-06-17
**Rule audited:** claude.md Non-Negotiable Rule — *"Measured data is allowed
only as a reproducible physical/market input, never as the answer — no pinning
the backcast to actuals."*
**Subject:** the current ERCOT keeper **run 124**
(`results/calibration/run124_storage_as_keeper`) and the full set of
measured-data overlays still present in the code path.
**Method:** code reads of `data/outages.py`, `data/renewables.py`,
`results/scarcity.py`, `config/scenarios.py`, the `derive_ct_deployment.py` /
`derive_reliability_deployment.py` overlays; plus the keeper's resolved
`run_config.json`. Builds on the prior whole-backcast review
`docs/ercot-backcast-audit-2026-06.md` (run 115b), re-checked against the
current keeper. Diagnosis only — no parameter changed.

---

## The admissibility test

A measured-data input is **allowed** (even in backcast mode) when it is grounded
in physics or market design **and** passes:

> *Could this same quantity be produced for a forward year from forward drivers,
> and would it respond to changed conditions?*

If yes, it is an **input** (like an outage, a fuel price, an emission rate, an AS
reservation). If instead it is a measured **outcome** fed back to drive the
residual to zero — observed generation, observed LMP, or an input rescaled so the
model's *output* lands on the actuals — it is **forbidden** in a keeper, because
it has no forward analogue: the dispatch being validated stops being the dispatch
being forecast.

---

## Headline: the current keeper is compliant

The three mechanisms the 2026-06-15 audit flagged as feeding the answer in are all
**OFF** in run 124 (verified in `run_config.json`):

| Mechanism | Test | run 124 |
|---|---|---|
| `ct_deployment_overlay` — floors each peaker to its **observed CEMS net output** in out-of-merit hours | **FAIL** (measured outcome, no forward analogue) | **OFF** ✓ |
| `reliability_deployment_overlay` — floors pocket CC/coal/ST to **observed CEMS net** in congestion hours | **FAIL** (same) | **OFF** ✓ |
| `ordc_reliability_deployment_mw` — flat non-physical MW offset **tuned to the 2023 price residual** | **FAIL** (residual-fitted adder) | **0.0** ✓ |

These remain in the codebase as **default-off diagnostic probes**, gated to
backcast mode and no-op in forecast (no artifact ⇒ no-op). That placement is
exactly what the rule permits — *exist as labelled probes, never as keepers.* The
risk is governance, not a current violation: runs 115b/118/122/123 **did** enable
them, so the temptation to switch them back on for a headline number is live. They
must not be re-enabled in a keeper or quoted as forecast skill.

---

## Allowed inputs in run 124 (pass the test — keep)

| Input | Why it passes |
|---|---|
| `historic_outage_overlay=True`, `outage_source="historic"` | Unit outage = physical availability event; reproducible window-detection on any year's CAMPD; forward analogue is the statistical/historically-derived maintenance profile. The **canonical allowed** case (the user's own example). |
| `coal_drop_pof=True` | Bookkeeping to avoid double-counting the statistical POF against the historic overlay — not a fit device. |
| `coal_plant_monthly_pricing=True` (F923 delivered fuel) | A real **cost input**; forward analogue is the forecast gas/coal price path. Responds to conditions. |
| Per-plant CEMS emission **rates** (bundle `campd.parquet`) | A physical plant **parameter** (lb/MMBtu), not an outcome; forward analogue is the fuel-class default. |
| `storage_as_commitment=True` (measured up-AS power reservation) | A **market-design commitment** (AS-held power cannot also arbitrage energy); adopted "for accuracy not fit"; forward analogue is the AS co-optimization / reservation logic. Caps the *physical* peak, does not pin energy to actuals. |
| Per-plant CAMPD `Plant_Avg_HR`, CF-P5 min-stable-load floors | Physical plant parameters (heat rate, min load), not outcomes. |

`renewable_cf_adjustment=1.0` and no per-plant/per-year CF override are set — good
(a per-plant-year CF override pinned to realized utilization would **fail** the
test; none is in use).

---

## One live gray-area item: the HSL rescale

`data/renewables.py:268` `_HSL_RESCALE_TWH` is a **module-level hardcode** keyed
`(ERCOT, 2023, wind)=110.0` / `(ERCOT, 2023, solar)=32.0`. It is applied
unconditionally by `hsl_potential_mw()` → `_hsl_cf_profile()` whenever the 2023
ERCOT HSL profile is built — there is **no config flag gating it**. Run 124
includes 2023, so it **is live** in run 124's 2023 renewable potential.

Two parts, with different verdicts:

- **Part that passes:** raising the raw HSL series up to *at least* the EIA-930
  delivered total. HSL is uncurtailed potential and must be ≥ delivered; the raw
  2023 wind series summed *below* delivered (~104 vs 108 TWh), which is physically
  impossible. Reconciling a biased-low input up to a physical floor is a
  legitimate data fix.

- **Part that fails the test (flag):** the targets are deliberately set *above*
  delivered (110 vs 108 wind; 32.0 vs 31.9 solar) **"to offset the dispatch's
  economic re-curtailment, so the *delivered* output lands on the actuals"**
  (comment at `renewables.py:262-264`). That second step tunes an **input** so the
  model's **output** matches a measured actual — the textbook pattern the rule
  forbids. It is a small effect (~1.8% wind, ~0.5% solar) and arguably benign
  because backcast renewable delivery is weather-fixed and near-must-take, but it
  *is* a measured-outcome-driven rescale with no forward analogue (the `+offset`
  is sized to *this model's* curtailment behaviour in *this year*).

**Recommendation (not yet applied — diagnosis only):** split the rescale.
Reconcile HSL up to `max(raw_HSL, EIA-930 delivered)` as the physical floor
(passes), and drop the curtailment-offset top-up; let the LP's endogenous
curtailment land where it lands and report the modeled-vs-reported curtailment gap
as a *diagnostic*, not close it by inflating the potential. If a year's delivered
renewable miss is then large, treat it as a discovered bug (per Rule #11), not a
rescale target.

---

## Verdict

Run 124 **complies** with the new rule on the load-bearing items: the CEMS
deployment floors and the fitted ORDC scarcity offset — the mechanisms that
previously "fed the answer in" — are off, and the remaining measured inputs
(outages, F923 fuel, CEMS rates, the storage-AS reservation) all pass the
forward-analogue test. The standing exposure is twofold:

1. **Governance** — the deployment overlays and the ORDC offset still exist and
   were keeper-enabled as recently as runs 118/122/123. Keep them default-off and
   out of keepers; if used, label them probes and never quote their fit as skill.
2. **The HSL rescale** is the one *live* measured-outcome-driven input in run 124.
   Small, but it is the rule's exact anti-pattern and should be reduced to a
   physical-floor reconciliation.

The strongest single confirmation remains the still-unrun **statistical-mode
backcast** (every overlay off — `forecast-validation-plan.md` Phase 3): it would
convert "the keeper passes the rule" from a config inspection into a measured
overlay-vs-statistical gap.
