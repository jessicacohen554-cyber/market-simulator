# FINDING soco-87 — C3b monthly diagnosis (zero LP)

Owner ruling 2026-09-28 (end of soco-86): **"C3b monthly diagnosis (Recommended)"**.
No solve (rule 32 (a)). Keeper unchanged: `2026-09-28-soco85-gas-daily-shape`, NOT-YET 7/4/0/1/2.
Probe: `scripts/probes/_soco87_c3b_monthly.py` (two `fleet_only` rebuilds per year on the keeper's own
recipe via `replay_keeper.run_year_kwargs`, then re-pricing of the committed `hourly/system_<y>.parquet`).

## 1. The gate, read from the scorer

`calibration_verdict.score_price_shape`: 12 load-weighted monthly model means (zone `pMon` weighted by `dMon`)
vs the bench `rt_lw_mon` (Southern FERC-714 lambda), `_nrmse = RMSE / mean(actual)`, PASS ≤ 0.20.
The probe's reconstruction from `system_<y>.parquet` reproduces the payload's monthly means to 0.1 $/MWh.

## 2. Decomposition of the keeper's miss

NRMSE² = bias² + shape variance. "Bias share" = bias² / MSE.

| Year | NRMSE | Mean bias $/MWh | Bias share | De-biased NRMSE | Months carrying ≥ 60 % of squared error |
|---|---|---|---|---|---|
| 2019 (pass) | 0.178 | +3.91 | 68 % | 0.101 | Dec, Jan, Feb |
| **2020** | **0.222** | +3.51 | 53 % | 0.152 | Apr, Jan, Mar |
| **2021** | **0.260** | −1.66 | 3 % | 0.257 | Oct, Jan, Sep |
| **2022** | **0.389** | −10.52 | 12 % | 0.365 | Jul, Dec, Aug, Jun |
| 2023 (pass) | 0.150 | +0.92 | 4 % | 0.147 | Dec, Apr, Mar, Feb |
| **2024** | **0.277** | −0.68 | 1 % | 0.277 | Jan, Jun |
| 2025 (pass) | 0.174 | +0.07 | 0 % | 0.174 | Jan |

**It is a shape miss, not a level miss.** In 2021, 2022 and 2024 the bias explains ≤ 12 % of the error.
The signature is the same in every year: the model's monthly price is nearly **flat**, while the actual
swings with the gas market. Example, 2022: actual $40 → $118 (Feb → Jul); model $62 → $77, peaking in **January**.

## 3. Driver: the gas price's monthly shape

The keeper sets gas as `annual level × GAS_MONTHLY_SEASONALITY × HH daily shape`. The middle term is a
**generic climatological shape, identical every year**, and always winter-high. The measured Henry Hub
month-to-month shape is not used (`gas_hh_monthly_shape=false`). In 2021 and 2022 that shape runs the
wrong way: HH rose through the year, yet the generic shape prices January as the dearest month.

Other candidate drivers, checked against measured inputs:
- **Load**: dispatched demand is EIA-930 measured, so it cannot drive a monthly price shape miss.
- **Hydro**: monthly budget is EIA-923 measured.
- **Outages**: CAMPD windows are measured. No month-specific pattern shared across the failing years.
- **Marginal class**: gas sets the price in 79–95 % of zone-hours (the probe's matched share), so a gas-shape error
  passes almost 1:1 into the monthly price.

## 4. Counterfactual: arm `gas_hh_monthly_shape` (measured HH monthly shape, same annual level)

Same-marginal-unit re-pricing: in each zone-hour, the unit whose keeper `mc_base` is within $0.50 of the LP
price is taken as price-setter, and the price moves to that unit's armed `mc_base`. First-order only (no
merit-order reshuffle).

| Year | C3b keeper → armed | Status | C3a keeper → armed | Residual after arming |
|---|---|---|---|---|
| 2019 | 0.178 → 0.173 | PASS → PASS | +13.9 → +14.5 % | level offset (bias), Dec/Jan |
| **2020** | **0.222 → 0.191** | **FAIL → PASS** | +15.0 → +15.6 % | Jan–Apr level (bias) |
| **2021** | **0.260 → 0.149** | **FAIL → PASS** | −5.1 → −2.5 % | Nov/Mar spread |
| **2022** | **0.389 → 0.284** | FAIL → FAIL | −15.7 → −12.5 % | **58 % is December (Winter Storm Elliott)**; Jul 21 % |
| 2023 | 0.150 → 0.097 | PASS → PASS | +1.7 → +2.4 % | — |
| **2024** | **0.277 → 0.192** | **FAIL → PASS** | −4.7 → −2.4 % | 50 % is January (cold snap) |
| 2025 | 0.174 → 0.184 | PASS → PASS | −1.2 → −1.7 % | 51 % is January (cold snap) |

C3b improves in all four failing years and clears three. No passing year flips. No C3a status flips
(2019/2020 +0.6 pp worse, 2022 +3.2 pp better, still failing).

**Margins are thin**: 2020 at 0.191, 2024 at 0.192 and 2025 at 0.184 are within ~0.02 of the 0.20 line.
A first-order greedy does not model the coal/gas switching the LP will do, so a solve can land either side.

## 5. Conclusion — (a): a named, admissible, year-consistent lever exists

`gas_hh_monthly_shape` (an existing field, `scenarios.py`; armed on the ERCOT keeper).
- **Admissible (rule 13)**: a measured commodity price. Forward analogue is the futures strip, and years with no HH rows
  fall back to the generic shape. Mean-preserving, so the annual level (and the soco-72 measured basis) is unchanged.
- **Replaces the generic shape; does not stack (rule 19).** `gas_daily_shape` still normalizes within each month on top.
- **Year-consistent**: one boolean across all seven years. **Zero DOF.**
- **Rule 1**: it corrects a known-wrong input (a fixed climatological shape used in place of the measured one),
  so it stands on structure. Its greedy C3b effect is supporting evidence only.

What it does **not** fix:
- **2022 December** (Elliott scarcity week) and the **2024/2025 January** cold snaps. These are daily SE-basis spikes, which the owner ruled
  free-data-only ("Stay free-data only").
- **The 2019/2020 C3a level offset** (+14–15 %). The soco-85 lambda finding (replacement fuel cost) still stands.

Named successor, not tested: `gas_electric_power_monthly_level` (EIA state-average monthly *level*) is **inert for SOCO**.
The `iso-gas-capacity-state-weights.csv` table has no SOCO rows, so arming it would first need a frozen EIA-860 derive of
those rows.

## 6. Retrievability

Nothing was solved; no bundle exists. A build would be seven year-isolated shards (~5–10 min each for SOCO).
