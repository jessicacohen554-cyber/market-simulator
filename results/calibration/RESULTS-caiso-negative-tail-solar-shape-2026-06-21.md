# CAISO negative midday tail — desert-SW solar-shaped import/export (results)

Branch: `claude/caiso-lmp-lever-ab-m56edy`. Flag: `--caiso-import-solar-shape`
(`ScenarioConfig.caiso_import_solar_shape`, default off). Builds on the
gas-coupled-imports lever (`--caiso-import-gas-coupling` +
`--gas-hub-basis-overlay`). Read `NEGRENEW-caiso-findings.md` and
`AUDIT-caiso-structural.md` first.

## The problem

The CAISO backcast printed ~14 hours ≤ $0 midday vs **~755 (DA) / ~868 (RT)**
actual negative-price hours in 2024. The prior negative-renewable-offer work
(`NEGRENEW-caiso-findings.md`) showed the in-state −$20 (REC/PTC) offer is on in
the keeper but **never marginal**: midday the price-setter is an *import*, and
the export sink floored any surplus at +$8/$0.

## Diagnosis (grounded in CAISO's own production/curtailment workbooks)

Using CAISO's public Production-and-Curtailments workbooks
(`data/raw/caiso-curtailment/`, 5-min Production + Curtailments):

- **The tail is offer-driven, not volume-driven.** 2024 *System* (oversupply)
  solar curtailment is only **0.23 TWh** (Local/congestion is 2.96 TWh). CAISO
  prints 868 negative hours on almost no oversupply volume — i.e. negative prices
  come from the **marginal unit bidding negative**, not a giant missing solar
  surplus. A potential-solar add-back is therefore a dead end here.
- The midday price-setter is the desert-SW solar import (`DSW_solar_PV`, Palo
  Verde hub), priced **flat** (~$48, gas-coupled). The real Palo Verde / Mid-C
  hubs collapse **sub-$0** midday in the regional spring solar/hydro glut, so the
  flat offer can never set a negative LMP.

## The lever

`transmission.inject_caiso_import_solar_shape` collapses the **marginal
long-neighbor blocks** — `DSW_solar_PV` (Palo Verde) and `PNW_midC` (Mid-C) —
**and** the export sinks (`export_solar`, `export_curtail`) from their level
toward `-renewable_keep_running_value` (−$20) as CAISO **net load**
(load − utility solar − wind) drops into its annual belly:

    s(t)  = clip((nl_hi − net_load[t]) / (nl_hi − nl_lo), 0, 1)
    mc[block, t] = base(t)·(1 − s(t)) + (−KRV)·s(t)

- **Net-load-gated** → fires spring-midday (deep belly), not summer-midday.
- **Depth is the existing REC/PTC keep-running constant** (−$20) — **no new
  fitted price constant**; applies on top of the gas coupling.
- Import side: the two marginal blocks fill the (path-constrained) import lane and
  push the $28 firm-hydro block out of the margin, so the price-setting import
  bids sub-$0. Export side: a *long* CAISO floors at the negative export price
  instead of +$8 (self-limiting — the sink is idle unless CAISO is long).
- Net-load band defaults `HI=30 / LO=10` percentile. `LO=10` is anchored to the
  observed ~9% negative-price prevalence (not tuned to a fit metric);
  env-overridable (`CAISO_SS_NL_HI/LO`) for sweeps.

## Results — 2024 (in-sample; load-weighted system price)

| metric | BEFORE (gas-coupled) | **AFTER (+solar-shape)** | ACTUAL 2024 DA |
|---|---|---|---|
| mean | 46.0 | **42.0** | 35.8 |
| p50  | 46.8 | **46.8** | — |
| p5   | 29.2 | **1.4**  | — |
| p95  | 63.7 | **63.7** | — |
| ≤$5 hrs | 46 | **922** | 923 |
| neg hrs | ~14 | **407** | 755 |

**Validation vs actual hourly DA LMP** (`data/raw/_validation-source/
actual_lmp_hourly_CAISO.parquet`, 8760-hr overlap):

- **neg(<0): precision 92%, recall 50%** — 407 modeled negatives, ~92 % are real
  negative hours.
- **≤$5: precision 84%, recall 84%** — modeled count 922 ≈ actual 923.
- Hour-of-day (9–15) and month (3–6) of modeled negatives match the actual.
- **Body preserved**: p50 / p95 / on-peak unchanged; gas TWh 72.6 → 71.1.

Net-load band sweep (precision is the anti-overfit guardrail):

| HI/LO | neg (model) | neg prec | neg recall | ≤$5 model | mean |
|---|---|---|---|---|---|
| 10/1  | 208 | 100% | 27% | 413 | 45.0 |
| 25/8  | 399 | 92%  | 49% | 889 | 42.1 |
| **30/10 (default)** | **407** | **92%** | **50%** | **922** | **42.0** |
| 32/10 | 407 | 92%  | 50% | 922 | 42.0 |

Negative count **saturates ~400 at 92 % precision**; wider bands only trade
precision for recall (overfitting), so the knee is the default.

## Honest caveats

1. **In-sample.** The band was set on 2024. The **2025 out-of-sample is
   confounded**: the 2025 model *body* runs high (mean 51.0 vs actual 34.6;
   pre-existing body miscalibration + 9/12-month gas coverage), so the tail
   lever cannot pull a $51 base below zero. It neither confirms nor refutes the
   lever. The anti-overfit case rests on (a) 92 % precision against held-out
   hourly LMP, (b) the prevalence-anchored band, (c) the physical mechanism.
2. **Recall 50 %.** ~350 actual-negative hours sit at $0–$5 in the model (the
   ≤$5 count matches, so the *timing* is right; the *depth* is shy of $0 in the
   shallow-negative hours). Reaching them needs a floor deeper than the
   REC/PTC-grounded −$20 — declined as less defensible.
3. **Body still ~$6 high** (42 vs 35.8) — a separate pre-existing
   body-calibration item, not the tail lever's scope.
4. **Reduced-form.** The regional glut is represented by a net-load gate + a
   single −$20 floor, not measured neighbor hub prices (no-OASIS scope).

## Reproduce

    python scripts/run_calibration_full.py --iso CAISO --year 2024 --commitment \
      --priced-interchange --hydro-backfill-year 2024 --hydro-eia930-monthly \
      --gas-hub-basis-overlay --caiso-import-gas-coupling --caiso-import-solar-shape \
      --out-dir results/calibration/caiso_solarshape_2024
