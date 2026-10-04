# PRECOMMIT — closeout-PJM-elliott: hourly measured Elliott forced-outage overlay (owner ruling R-64)

Lane `closeout-PJM-w2` continuing on `claude/closeout-pjm-elliott` (cut from `e8570532`). Desk
`session_01ERkBTm23ZAP4CTZnJVD9Ss`. Keeper `2026-10-03-closeout-pjm-nuc-keeper` (bundle
`results/calibration/closeout_pjm_nuc_full_span`). Rubric v3.20. Written **before** any build or solve.

**Ruling R-64** (2026-10-04, owner card, verbatim): *"Admissible — digitise & test (Recommended)"*. PJM's
Winter Storm Elliott Event Analysis (2023) hourly forced-outage profile is admissible as a windowed, measured
backcast outage overlay (rule 13; event window only; backcast-only).

## 1. Data (intake done before this PRECOMMIT)

- **Source.** PJM, *Winter Storm Elliott Event Analysis and Recommendation Report*, 2023-07-17. URL
  `https://www.pjm.com/-/media/library/reports-notices/special-reports/2023/20230717-winter-storm-elliott-event-analysis-and-recommendation-report.ashx`,
  sha256 `8282dc2d…7958875`.
- **Figure.** Figure 30, "Dec. 23 and Dec. 24 Forced Outages" (report p. 50, PDF p. 57): GADS forced outages and
  derates by fuel, as of 2023-03-01, with wind and solar excluded. Bars are at the even hours of 23–25 Dec plus
  24 Dec 07:00. The report has no table behind it, so the bars are read off the losslessly extracted raster.
- **Files.**
  - Raster: `data/raw/pjm-elliott-forced-outages/figure30_gads_forced_outages_by_fuel.png`.
  - Digitiser: `scripts/data/digitise_pjm_elliott_forced_outages.py`.
  - Output: `figure30_digitised.csv`, 37 bars × 6 fuels.
- **Uncertainty.**
  - The scale is fixed by the chart's own 30/40 GW gridlines: 9.6 px per GW, so ±1 px is ±104 MW per bar.
  - The check bar (24 Dec 07:00) reads **46,250 MW** against the labelled **46,124 MW** (+126 MW, +0.27 %).
  - Fuel splits are colour pixel shares; borders and anti-aliasing put about ±0.2 GW on each fuel.
  - Odd hours are linear interpolations, and 25 Dec 23:00 holds the 22:00 value.
  - The figure's Dec 23 00:00 bar (12.6 GW) agrees with the eDART 06:00 daily snapshot (11.9 GW) to 0.7 GW.

## 2. Mechanism (one, windowed, measured)

**Field.** `pjm_elliott_measured_outage_overlay: bool = False`, a PJM, backcast, availability overlay; the CLI
has `--pjm-elliott-outage-overlay / --no-pjm-elliott-outage-overlay`.

**Increment.** For each covered fuel f ∈ {gas, coal, oil, nuclear} and each event hour h (2022 rows 8544–8615,
i.e. 23 Dec 00:00 – 25 Dec 23:00 EPT, hour-beginning):

inc_f(h) = max(0, [M_f(h) − M_f(base)] − [U_f(h) − U_f(base)])

- M is the measured GADS forced outage MW.
- U is the model's own unavailable MW for that fuel (Σ pmax·(1 − availability)) after every other overlay.
- "base" is the figure's own pre-front bars, 23 Dec 00:00–04:00 (variant B/C: same source, no GADS/eDART basis
  mixing). The desk's 20–22 Dec eDART form (variant A) is reported and also clears.

**Application.** inc_f(h) is withdrawn by scaling every covered unit of fuel f in hour h by
μ_f(h) = (A_f(h) − inc_f(h)) / A_f(h), clipped to [0, 1], where A_f(h) is the fuel's available MW. Every
unit's relative availability is preserved, and a zero stays zero.

**Why this counts as measured, not fitted (rules 13 / 17 / 19).**
- It has a window (the 72 published event hours), a driver (measured forced outage) and a forward story: it is a
  backcast-only overlay. The forecast analogue is the correlated-forced-outage class, which stays `.`/I for PJM.
- Zero free parameters; the MW are PJM's.
- Rule 19: it composes after the CAMPD unit windows and measures only the rise those windows do not already
  carry. It cannot stack with `pjm_measured_outage_event_cap`; the two are mutually refused in `__post_init__`.
- It is not a floor, so it adds nothing to C8 forced energy.

## 3. Zero-LP reach on the keeper (`scripts/probes/_closeoutpjm_elliott_hourly_reach.py` → `results/phase0/pjm/_closeoutpjm_elliott_hourly_reach.json`)

| variant | max inc (MW) | hours resid < 0 / < req | Dec 23–24 est. mean | C3a 2022 | C3b 2022 | est. unserved (MWh, upper) |
|---|---|---|---|---|---|---|
| keeper | — | 0 / 0 | $110.91 | −17.2 % | 0.298 | 0 |
| A (desk, eDART 20–22 Dec) | 31,036 | 20 / 28 | $1,200.60 | −7.2 % | 0.181 | 62,146 |
| B (same source, total) | 30,114 | 18 / 26 | $1,113.55 | −8.0 % | 0.172 | 44,129 |
| **C (same source, fuel grain = build)** | 30,145 | 18 / 26 | **$1,113.04** | **−8.0 %** | **0.172** | 44,655 |

Real Dec 23–24 mean: $1,010.37. The estimator prices residual-headroom shortfalls at the PJM ORDC steps the LP
carries ($850 / $300) and below zero at VOLL $2,000. It ignores flex from `PJM_external` imports, so it is an
upper bound on scarcity.

## 4. Bars (fixed here; never re-read)

- **R1.** C3a 2022 is within ±10 % (keeper −16.7 %; prediction −8.0 %).
- **R2.** C3b 2022 is ≤ 0.20 (keeper 0.293; prediction 0.172).
- **R3.** The Dec 23–24 load-weighted mean model price is ≥ $800/MWh (prediction ~$1,113).
- **R4.** 2019–21 and 2023–25 move by no more than noise: every class within 0.05 TWh, C3a within 0.2 pp, C3b
  within 0.005 of the keeper, a pass/fail status change in none of them. The overlay touches no row outside
  2022/8544–8615, so a larger move is HEAD drift, which is disclosed and attributed.
- **R5.** No C1 PASS→FAIL in any year. In 2022 the overlay moves 72 h of thermal energy (predicted |Δ| < 0.5 TWh
  per class). C1 CC_REGULAR 2022 is already a FAIL (+8.96) and may move either way.
- **K1 (kill).** Any change in 2022 availability outside rows 8544–8615, or nonzero slack outside the event
  window that the keeper does not also have. Either is a bug.
- **K2 (kill).** Unserved energy in the window > 100,000 MWh, about 2× the upper-bound estimate. That would mean
  the overlay removed more than measured.
- **Reported, not gated.**
  - C3c 2022: predicted to rise from 2 h toward roughly 20–30 h against the real 92 h.
  - Slack MWh: the model has no emergency-DR or emergency-import representation, while real PJM avoided firm load
    shed through those procedures. This is a disclosed representation boundary.
  - 2022 C1 class deltas.
  - The variant-A arm is not solved.

## 5. Solve plan

- Build at one pin (default OFF, PJM only), with a matrix row, a cell in every shard, cache-key and solve-surface
  registration, and fast-lane tests.
- Seven year-isolated shards at the build commit (rules 32/34/36), recipe = the keeper's `run_config_<Y>.json`
  plus `--pjm-elliott-outage-overlay`.
- All seven legs are solved because HEAD drifted since the keeper's pin 8c3ea461: eGRID reader, EIA-930
  envelopes/demand, `pipeline/solve.py`. The six non-2022 legs therefore measure drift, and are not
  overlay controls.
- Compose, score, and register as a probe on the branch. If R1–R5 pass and K1–K2 hold, request the promotion slot.
