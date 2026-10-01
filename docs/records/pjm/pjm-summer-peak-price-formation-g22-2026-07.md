# PJM G-22 — summer-peak price formation root-caused to a too-cheap top-of-stack offer surface

**Date:** 2026-07-11. **Branch:** `claude/pjm-summer-peak-pricing-04qesd`.
**Scope:** diagnosis only (rule 1). Keeper stays `2026-07-10-pjm-97-measured-interfaces`.
No keeper file, measured input, or tunable touched; no run registered (the
baseline is a rule-16 same-day throwaway). Holdout years untouched (rule 22).

## Headline

The summer-peak price gap (C3a summer-only, C3b flat-top, C3c 0-hour tail) is
**one root cause: the top of the model's thermal offer stack is too cheap, so
the energy dual is set by a deep sub-$35 body while the real market's
price-setting margin sits at $80–140.** At the top-150 load hours the model
carries **21–24 GW of thermal offered BELOW the actual DA clearing price**
(idle, un-needed because the stack below it is deep and cheap). The measured
PJM offer data shows the real fleet's top-of-curve reaches **p90 $238 / p99
$514** in exactly those hours, while the keeper's peak bands top out at
~$115–130 and never bind. **Lever A (a measured PJM energy-offer surface for
CC_REGULAR + CT_PEAKER) is THE lever;** levers B (DA reserves) and C (seam) are
downstream/secondary and are re-scoped below.

## 1. Same-day baseline (rule-16 throwaway, all 3 years, `results/calibration/pjm97_baseline_20260711`)

Re-solved the pjm-97 keeper config byte-faithful on today's data (the committed
Jul-10 payloads are on drifted `_shared` inputs; every number below A/Bs against
this baseline, never the committed payloads). Idle-supply audit at the top-150
system-load hours (`scripts/probes/_g22_idle_supply_audit.py`):

| year | load GW | model LW price | actual DA LW | model max | actual DA max | net-export GW | idle thermal GW | idle **below actual price** GW |
|---|---|---|---|---|---|---|---|---|
| 2023 | 133.9 | **$31.6** | $76.2 | $36 | $308 | +3.33 | 35.3 | **24.1** |
| 2024 | 142.2 | **$34.6** | $82.8 | $129 | $200 | +1.53 | 31.4 | **21.9** |
| 2025 | 145.7 | **$44.8** | $136.2 | $81 | $503 | +2.57 | 28.9 | **21.2** |

The price-duration curve is flat-topped because ~22 GW of thermal sits offered
below the price that *should* be clearing. Idle decomposition (2024 top-150):

| class | avail GW | disp GW | idle GW | idle-MC p50 | idle-MC p90 |
|---|---|---|---|---|---|
| CT_PEAKER | 20.9 | 13.1 | **9.24** | $42.6 | $115 |
| COAL (all) | 29.3 | 21.6 | **9.00** | $28.7 | $55 |
| ST_GAS | 7.3 | 4.9 | 2.39 | $42.8 | $110 |
| CC_REGULAR | 52.7 | 51.7 | 1.01 | $30.0 | $37 |

CC_REGULAR is ~fully dispatched (1 GW idle) — its **committed/econ body clears,
its peak band never sets price**. The idle that should be pricing the peak is
CT_PEAKER (9 GW, but its offer p90 is only $115 — too low to reach the $200
actual) and COAL (9 GW at ~$29 — cheap and idle: the deep sub-$35 floor).

## 2. The measured answer — PJM's real offer stack (July-2024, top-150 hours)

From `data/raw/pjm-energy-offers/pjm_energy_offers_2024_07.parquet` (PJM
DataMiner2 `energy_market_offers`, ~1,254 units/hour at these hours), cumulative
offered MW by price and top-of-curve distribution:

```
measured offered MW <= $35:  138.5 GW   (load ~139 GW → body clears here)
             <= $83: 159.3   <= $200: 165.7   <= $300: 169.3
top-of-curve offer price, capacity-weighted:  p50 $25  p90 $238  p99 $514
```

The real market clears at **$83 (2024 DA)** not because the body is expensive
(it isn't — 138 GW ≤ $35, same as the model) but because the **last ~1–4 GW is
priced $200–500**. Segmented by unit physics (min-runtime × capacity × ecomin
ratio):

| segment | cap GW | ≤$35 | $35–83 | $83–200 | $200–500 | top p90 |
|---|---|---|---|---|---|---|
| CC-like (mr>2, ratio>0.2) | 74.8 | 59.9 | 8.8 | 3.8 | **2.1** | **$273** |
| fast-start CT-like (mr≤2) | 43.6 | 31.3 | 6.7 | 1.8 | **3.5** | $199 |
| long-run coal/ST-like (mr>16) | 77.7 | 68.0 | 6.9 | 1.8 | 1.0 | $122 |

The scarcity wall is **CC-like top-of-curve (p90 $273) + fast-start CT (3.5 GW
in the $200–500 band)**. The keeper prices CC_REGULAR peak at 5.0×HR and
CT_PEAKER peak at 4.0×HR — both cap out ~$115–130 and never reach the measured
$200–500 wall, so nothing in the model sets a summer-peak price. This is the
ercot-50 / neiso-58 finding exactly: **measured OFFER prices are the missing
offer-curve parameters; clearing prices stay validation-only (rule 13).**

## 3. Levers re-scoped by the evidence

**Lever A — measured PJM energy-offer surface (THE lever).** Build the
neiso-58 analogue for PJM: `scripts/data/derive_pjm_offer_surface.py` (mirror
`derive_neiso_offer_surface.py`) → a condition-binned top-of-curve
heat-rate-multiplier surface for **CC_REGULAR + CT_PEAKER** (the two classes
whose idle is offered above the model price but below the actual), keyed by
within-year net-load percentile, from the fetched raw offers; multiplier
round-trips through the model's own delivered-gas day series + class base-HR.
Wire `ScenarioConfig.pjm_offer_surface_conditional` +
`fleet.build_pjm_offer_surface_conditional_markup` at the existing P1-only
`mc_bid_adjust` seam (`run_calibration.py:2487`, the NEISO branch is the
template). Single-delta off the keeper. Rule 20/21: freeze the surface against
residuals; register a zero-forcing ablation twin.

**Lever B — DA reserve procurement (downstream of A, not standalone).** The DA
Primary reserve requirement is ~3.5 GW (RTO) / ~2.6 GW (MAD)
(`da_reserve_market_results_2024.parquet`). The published ORDC overlay fires
**0 h** because the model's online reserve (~16.6 GW) never approaches 3.6 GW —
the model is never tight *because the deep cheap stack means it never has to
commit the expensive top*. Fix A first (the top gets expensive → the body is
dispatched harder → reserve tightens); only then re-test whether B adds a
scarcity tail. B alone will not bind.

**Lever C — seam (SECONDARY, 2025-only; the charter framing is corrected
here).** The charter says the model "net-exports THROUGH measured scarcity
hours." **The measured system also net-exports at its summer peaks** — PJM is a
net exporter. Measured 930 interchange at the top-150 hours: **+5.2 / +2.3 /
+0.8 GW** (2023/24/25); model **+3.3 / +1.5 / +2.6 GW**. In 2023 the model
exports *less* than measured; in 2024 it's close. The only real gap is **2025**
(model +2.6 vs measured +0.8 → ~1.8 GW over-export in the tightest year, when
measured export collapses under the scarcity the ladder is blind to). So a
scarcity-conditioned export response is a small 2025-only refinement, **not the
primary lever** — do not chase it before A.

## 4. What is ruled OUT (confirmed this session)

- **Fuel-mix / composition is NOT the driver.** The model's fuel mix at the
  peak matches measured 930 within ~1–2 GW/class (2024 top-150: model CC 51.7
  vs 930 gas 66.6 incl. CT/ST, coal 25.4 vs 27.2, nuclear 32.1 vs 31.9). The
  gap is purely price formation, not volume.
- **"Exports through scarcity" as a primary anomaly** — refuted for 2023–2024
  (§3 lever C).
- temp_dependent_derate stays refuted (pjm-95 rule-24); not re-opened.

## 5. Next-session build plan (single delta)

1. `scripts/data/fetch_pjm_energy_offers.py` — all 2023/2024/2025 months (July-2024 +
   May/Jun/Aug/Sep-2024 already fetched this session; the rest were fetching in
   background at handoff — re-run to be safe, raw is gitignored, ~1–2 GB).
2. `scripts/data/curate_energy_offers.py` → clean long tree (optional; the derive can
   read raw directly like the NEISO one).
3. `scripts/data/derive_pjm_offer_surface.py` (NEW, mirror the NEISO derive) →
   `data/raw/_validation-source/pjm_offer_surface_condbinned.json`
   (CC_REGULAR + CT_PEAKER entries; edges 0.80/0.90/0.97).
4. `ScenarioConfig.pjm_offer_surface_conditional` (+ path/pcts/min_bin/cap
   fields) and `fleet.build_pjm_offer_surface_conditional_markup` (reuse
   `_conditional_surface_markup`; groups `("CC_REGULAR","CT_PEAKER")`); wire at
   `run_calibration.py:2487`.
5. Probe: `replay_keeper.py results/calibration/pjm97_measured_interfaces
   --set pjm_offer_surface_conditional=true --out-dir …/pjm99_offer_surface`
   (or a full `run_calibration_full` invocation since the surface needs its
   path field) — score vs the §1 baseline. If it lands: 3-year bundle +
   ablation twin + DOF ledger + verdict + legitimacy diagnostics + dashboard
   registration (`pjm 99 offer-surface`), keeper rec flagged for owner.

## Appendix — reproduction

- Baseline: `python scripts/replay_keeper.py
  results/calibration/pjm97_measured_interfaces --out-dir
  results/calibration/pjm97_baseline_20260711` (12 GB/yr, ~13 min/yr,
  sequential). Throwaway — never registered.
- Idle audit: `python scripts/probes/_g22_idle_supply_audit.py
  results/calibration/pjm97_baseline_20260711 --years 2023 2024 2025 --top 150`.
  Needs `run_calibration.run_year(fleet_only=True)` to return `mc_base` +
  `fuel_prices` (added this session, `scripts/run_calibration.py`) so the audit
  reads the SAME offer prices the LP solved on.
- Measured offer stack: `data/raw/pjm-energy-offers/pjm_energy_offers_2024_07`
  (gitignored; PJM DataMiner2, non-member redistribution restriction — only the
  derived multiplier JSON, never prices, is committable).
- Interchange: `data/raw/eia-930-hourly/PJM hourly.parquet` `Total interchange`.
