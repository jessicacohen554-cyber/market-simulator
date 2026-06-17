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

## The HSL rescale — RESOLVED (2026-06-17)

**Was:** `data/renewables.py` `_HSL_RESCALE_TWH` was a module-level hardcode
`(ERCOT, 2023, wind)=110.0` / `(ERCOT, 2023, solar)=32.0`, applied
unconditionally whenever the 2023 ERCOT HSL profile was built. Its two parts had
different verdicts: raising the raw HSL up to *at least* the EIA-930 delivered
total was a legitimate physical-floor fix (the UMass-derived series sums *below*
delivered, which is impossible for a potential), **but** the targets were
deliberately set *above* delivered "to offset the dispatch's economic
re-curtailment, so the *delivered* output lands on the actuals" — tuning an
**input** so the model's **output** matched a measured actual, the exact
anti-pattern the rule forbids (no forward analogue; the `+offset` was sized to
*this model's* curtailment behaviour).

**Now:** the model-output target is gone. `hsl_potential_mw()` consumes each HSL
parquet as-is, with **one real-data coverage reconciliation**: when a source's
own delivered (its `GEN` column) materially undercounts the EIA-930 system
delivered total (a partial-footprint dataset), the series is scaled UP to the
EIA-930 level *preserving the dataset's own measured curtailment ratio*
(`delivered/HSL`). That reconciles two real datasets — the parquet's hourly shape
+ curtailment ratio, the EIA-930 level — and references nothing about model
output. The model then curtails endogenously and the modeled-vs-reported
curtailment gap is a **diagnostic**, not a fit target (Rule #11). For 2023 this
now yields wind **113.28 TWh** / solar **34.01 TWh** at the measured 4.67% / 6.29%
curtailment ratios, replacing the back-solved 110 / 32.

The reconciliation is a **no-op for full-footprint published data** (whose
delivered already matches EIA-930 within 2%). `build_ercot_hsl.py` now prefers the
authoritative ERCOT **NP4-732/737** published HSL for *any* year (drop the reports
into `np6/`), falling back to the UMass reconstruction for 2023 only when no
published upload exists. **Action for the user:** supplying the published
2023/2024/2025 NP6 HSL retires the reconciliation entirely — 2024/2025 currently
have *no* HSL parquet at all and fall back to EIA-930-delivered-as-CF (no
curtailment modelling), so the published uploads also turn on endogenous
curtailment for those years.

---

## Verdict

Run 124 **complies** with the new rule on the load-bearing items: the CEMS
deployment floors and the fitted ORDC scarcity offset — the mechanisms that
previously "fed the answer in" — are off, and the remaining measured inputs
(outages, F923 fuel, CEMS rates, the storage-AS reservation) all pass the
forward-analogue test. After the 2026-06-17 HSL fix, the remaining standing
exposure is **governance**: the CEMS deployment overlays and the ORDC offset
still exist in code and were keeper-enabled as recently as runs 118/122/123. Keep
them default-off and out of keepers; if used, label them probes and never quote
their fit as skill. (The HSL output-target rescale — previously the one live
measured-outcome-driven input — has been replaced with a real-data coverage
reconciliation; see the section above.)

The strongest single confirmation remains the still-unrun **statistical-mode
backcast** (every overlay off — `forecast-validation-plan.md` Phase 3): it would
convert "the keeper passes the rule" from a config inspection into a measured
overlay-vs-statistical gap.
