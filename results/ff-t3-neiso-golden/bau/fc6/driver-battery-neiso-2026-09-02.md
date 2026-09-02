# Driver battery — NEISO forecast 2026-2050

*Generated 2026-09-02 by `scripts/run_driver_battery.py` (plan §2 Tier 1). Forecast probe — NOT a backcast dashboard run.*

Single-driver directional & elasticity ladders. Each expectation was **pre-registered** (in the ladder table in this script) before the run; a gated FAIL is a root-cause issue, never a threshold to widen (rules 1/11/14). This is measurement, not tuning.

## Run configuration

- **ISO:** NEISO
- **Horizon:** 2026-2050 (sequential years, rule 12)
- **Fleet representation:** legacy equal-width bins (`use_campd_bins=False`) — runtime trade, same as the tornado

## Scoreboard

**2 PASS · 0 FAIL · 0 WARN · 0 SKIP** across 1 ladders.

| Test | Driver | Expectation | Gate | Status | Detail |
|---|---|---|:--:|:--:|---|
| T1.6a | RPS/ACP vs VRE supply (short→long) | REC dual ≤ ACP ceiling | gate | PASS | all ≤ 1.0 |
| T1.6b | RPS/ACP vs VRE supply (short→long) | REC dual ↓ as VRE builds toward the target | gate | PASS | ↓ [1.0, 1.0] |

## Per-ladder rungs

### T1.6 — RPS/ACP vs VRE supply (short→long)

_rps_dual_over_acp is the final-year REC dual divided by the ISO's ACP ceiling; ≤ 1 means the ACP escape column caps the dual as designed, and it should fall as physical VRE covers the target._

| Rung | Status | Overrides | Key metrics |
|---|:--:|---|---|
| vre_short | ok | `{'entry_rate_limits': True}` | coal_twh=0.7568, co2_mt_total=197.1768, lw_price=66.5, scarcity_hours=0, retired_thermal_gw=2.015, economic_retired_thermal_gw=0.1603, exogenous_retired_thermal_gw=0.124, reserve_margin_final=0.0853, rps_dual_over_acp=1.0 |
| vre_long | ok | `{'entry_rate_limits': False}` | coal_twh=0.7568, co2_mt_total=193.9864, lw_price=66.224, scarcity_hours=0, retired_thermal_gw=3.015, economic_retired_thermal_gw=0.1603, exogenous_retired_thermal_gw=0.124, reserve_margin_final=0.05527, rps_dual_over_acp=1.0 |
