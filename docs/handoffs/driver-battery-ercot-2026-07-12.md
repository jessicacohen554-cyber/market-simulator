# Driver battery — ERCOT forecast 2026-2030

*Generated 2026-07-12 by `scripts/run_driver_battery.py` (plan §2 Tier 1). Forecast probe — NOT a backcast dashboard run.*

Single-driver directional & elasticity ladders. Each expectation was **pre-registered** (in the ladder table in this script) before the run; a gated FAIL is a root-cause issue, never a threshold to widen (rules 1/11/14). This is measurement, not tuning.

## Run configuration

- **ISO:** ERCOT
- **Horizon:** 2026-2030 (sequential years, rule 12)
- **Fleet representation:** legacy equal-width bins (`use_campd_bins=False`) — runtime trade, same as the tornado

## Scoreboard

**1 PASS · 0 FAIL · 0 WARN · 0 SKIP** across 1 ladders.

| Test | Driver | Expectation | Gate | Status | Detail |
|---|---|---|:--:|:--:|---|
| T1.9a | storage ELCC saturation (seed GW) | storage capacity value per MW monotone ↓ | rpt | PASS | ↓ [0.279, 0.2, 0.024] |

## Per-ladder rungs

### T1.9 — storage ELCC saturation (seed GW)

_ELCC(4h) x saturation derate x portfolio dilution must fall as the fleet saturates the peak. Metric = the model's own marginal storage accreditation at the final fleet (from the evolution ledger's storage_power_mw — CR-3.1); in energy-only ERCOT the $ capacity price is 0 by design, so the accreditation fraction is the saturating observable. Report-only._

| Rung | Status | Overrides | Key metrics |
|---|:--:|---|---|
| seed_5gw | ok | `{'_storage_seed_gw': 5}` | coal_twh=335.8514, co2_mt_total=862.0042, lw_price=20.63, scarcity_hours=0, retired_thermal_gw=0.0, reserve_margin_final=0.01821 |
| seed_15gw | ok | `{'_storage_seed_gw': 15}` | coal_twh=335.0934, co2_mt_total=861.4082, lw_price=20.626, scarcity_hours=0, retired_thermal_gw=0.0, reserve_margin_final=0.04838 |
| seed_25gw | ok | `{'_storage_seed_gw': 25}` | coal_twh=243.6385, co2_mt_total=804.4821, lw_price=26.762, scarcity_hours=130, retired_thermal_gw=4.681, reserve_margin_final=0.12352 |
