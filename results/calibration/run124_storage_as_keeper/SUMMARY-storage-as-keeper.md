# run124 — storage AS-commitment keeper (2026-06-17)

**run124 = run121 + `--storage-as-commitment`.** The AS-aware storage design,
finalized as a clean 3-year keeper. CT deployment OFF, `battery_dispatch_adder=10`
retained, storage vintage COD ramp on, merit-ramp CC, cc-duct. Adopted for
ACCURACY, not fit. Full narrative in `docs/calibration-log.md`
(2026-06-17 entry) and `docs/calibration-best-so-far.md`.

## Scores (vs run121 — identical, by design)
- **Volume (0.5% universal gate):** 5 fails @0.5%, 7 @0.33% — same set
  (CT_PEAKER 2023/24, CC_REGULAR 2024/25, COAL_PRB 2024).
- **cf_emd [7c]:** 18/18 PASS, several marginally better (CC_CHP, CT_PEAKER
  2024, ST_GAS); no regressions.
- **CO2:** 8/9 PASS (2024 coal −7.0% cheap-gas residual, unchanged; totals ±5%).

## Accuracy gain (the reason it's a keeper)
| year | storage discharge model→ (EIA-930) | peak GW (run121→run124) |
|---|---|---|
| 2024 | 0.781 → **0.728** (0.722) | 5.93 → **4.59** |
| 2023* | 0.525 → 0.51 (no measured bench) | 2.95 → 2.56 |
| 2025 | 3.799 → 3.788 (5.45, under-runs regardless) | 9.36 → 9.28 |

*2023 storage-AS is an ESTIMATE (intensity transfer from 2024 × EIA-860 COD
fleet ratio; `build_ercot_storage_as_2023_estimate.py`). 2024/25 are measured.
12 unphysical 2024 >4.6 GW full-fleet dump hours eliminated.

## The tuning finding (Task 3)
The measured AS reservation **complements, does not replace**, the adder:

| 2024 | discharge (0.722) | charge (0.870) | peak GW | CT_PEAKER cf_emd r |
|---|---|---|---|---|
| run121 (adder10, no AS) | 0.781 | 0.918 | 5.93 | 0.466 |
| **run124 (adder10 + AS)** | **0.728** | **0.857** | **4.59** | 0.470 |
| adder0 + AS (REJECTED) | 2.724 | 3.205 | 5.91 | 0.445 (FAIL) |

The adder bounds storage **energy** (throughput/degradation cost); the AS
reservation caps the **peak** (measured physical commitment). adder=0 lets the LP
over-cycle in the low-AS hours (storage 3.8× benchmark). adder=10 stays as a
defensible degradation VOM.

## Market-integrity (Task 1) & physical (Task 2)
- No double-counting: `as_revenue_enabled` OFF in P1 backcast (only feeds capacity
  screens); ORDC `ordc_as_plan_mw` netting OFF; reservation touches only the
  storage power cap. Reg-Down/Non-Spin excluded; per-restype reconciles with
  NP3-911 (+40 MW 2025, −600 MW 2024 conservative).
- RTE 0.850 (exact target); 0 simultaneous charge/discharge hours; reserved AS =
  measured series exactly (peak 4596 / mean 2045 MW); 0 deliverability violations.
- Reserves **power, not SOC** — first-order-correct for the energy backcast; SOC
  reservation is a forecast-only AS-deliverability refinement.

## Jacobian (Task 4)
`jacobian_2024.csv` — own-class (diagonal) responses dominate and are correctly
signed; every cross-class response is smaller than the moved band; net ΣΔ ≈ 0.
Sensitivities stable, no class over-levered. Storage-AS left thermal offer-curve
sensitivities unchanged.

## Reproduce
```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
    --storage-daily-cycling --battery-adder 10 --storage-as-commitment \
    --offer-curve-delta-json inputs/calibration/offer_curve_deltas_cc_merit_ramp.json \
    --coal-lignite-sigmoid --lignite-floor 0.675 --lignite-ceil 1.00 \
    --prb-floor 0.73 --prb-follower-floor 0.63 \
    --curve-mid 0.35 --btm-backfill-year 2024 --cc-duct-peaking \
    --wefor-residual 0.06 --wefor-relief-groups ST_GAS,ST_CHP
```
