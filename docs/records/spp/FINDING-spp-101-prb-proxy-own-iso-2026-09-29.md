# FINDING — SPP-101: `coal_prb_proxy_own_iso` is INERT on the SPP keeper (zero LP)

**Lane** SPP-101 · control = keeper `2026-09-28-spp-100-chp-scope` (bundle `spp100_arm_span`) · no solve,
no PRECOMMIT (nothing was solved) · probe `scripts/probes/_spp101_prb_proxy_phase0.py`, numbers
`results/calibration/_spp101_prb_proxy_phase0.json`.

## 1. Why this lever (off-queue, stated reason)

The §5.7 queue is exhausted (SPP-96). The only SPP cell still flagged as a live defect in SPP's own fleet was
`coal_prb_proxy_own_iso` (O): NWPP-41 measured that the ERCOT-pooled PRB delivered-cost proxy "reaches 3–5
non-reporting SPP PRB plants" (rule 25 `[R-ISO-SCOPE]`). The field exists, is zero-DOF and needs no `src/`
edit (`replay_keeper --set`), so it was the cheapest open item to adjudicate.

## 2. What was measured

`run_year(..., fleet_only=True)` on the keeper's own recipe, flag off vs on, marginal-cost array diffed
row for row. The flag was confirmed to reach the config (`coal_prb_proxy_own_iso=True`,
`coal_supply_repricing=True`, `coal_plant_monthly_pricing=True`; 141 COAL_PRB rows, 29 plants).

| year | fleet rows | offer rows moved | pmax / avail max\|Δ\| |
|---|---:|---:|---|
| 2019 | 1153 | **0** | 0 / 0 |
| 2020 | 1146 | **0** | 0 / 0 |
| 2021 | 1128 | **0** | 0 / 0 |
| 2022 | 1128 | **0** | 0 / 0 |
| 2023 | 1113 | **0** | 0 / 0 |
| 2024 | 1129 | **0** | 0 / 0 |
| 2025 | 1184 | **0** | 0 / 0 |

For reference, the two proxies do differ ($/MMBtu, quantity-weighted annual mean):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| ERCOT pool (default) | 1.739 | 1.650 | 1.731 | 1.936 | 1.823 | 1.752 | 1.615 |
| SPP own pool | 1.569 | 1.490 | 1.517 | 1.869 | 1.806 | 1.694 | 1.668 |

## 3. Why it is inert

In the calibration path the order is `apply_coal_supply_pricing` (the proxy) **then**
`apply_plant_monthly_fuel_prices` (`scripts/run_calibration.py` ~L4900), which writes every coal plant-month
from its own EIA-923 print or the nearby pool. On the current keeper that overlay reaches every SPP PRB row,
so the proxy value is overwritten everywhere. NWPP-41's "3–5 plants" was measured on an earlier code state.

## 4. Verdict and what it leaves

- **`coal_prb_proxy_own_iso` O → I for SPP.** No solve is warranted; do not re-test without a change to the
  plant-monthly overlay's coverage.
- Also reported: SPP's own PRB pool is *cheaper* than ERCOT's in 2019–22, so even if the lever had bitten it
  would have lowered coal offers — the wrong direction for the C1 COAL_PRB 2021/22 excess.
- The open validation failures are unchanged. The SPP-89 bucket census (`_spp89_coal_cc_swap.json`) locates
  the 2021/22 CC shortfall in hours where the actual LMP was ≤ $15 (actual CC 7.3 / 4.8 TWh vs model
  2.2 / 0.6 TWh) — CC running committed at low prices. That is the commitment-state object SPP-73/82/83/97
  routed to an owner-gated design lane; no admissible zero-DOF instrument for it remains on the §5.7 queue.
