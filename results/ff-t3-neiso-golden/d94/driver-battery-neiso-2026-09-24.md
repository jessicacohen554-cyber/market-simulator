# Driver battery — NEISO forecast 2026-2050

*Generated 2026-09-24 by `scripts/run_driver_battery.py` (plan §2 Tier 1). Forecast probe — NOT a backcast dashboard run.*

Single-driver directional & elasticity ladders. Each expectation was **pre-registered** (in the ladder table in this script) before the run; a gated FAIL is a root-cause issue, never a threshold to widen (rules 1/11/14). This is measurement, not tuning.

## Run configuration

- **ISO:** NEISO
- **Horizon:** 2026-2050 (sequential years, rule 12)
- **Fleet / recipe:** the neiso-t3 GOLDEN recipe (run_full_horizon --golden-posture, per-ISO default bins) + both neiso-t3 pins (ccs_retrofit_vom_adder 8.0, ccs_retrofit_fixed_cost_co2_scaling False), solved by capx D94 shards at 924017c8; assembled by docs/handoffs/d94/battery_golden_rung.py (PRECOMMIT-capx-d94-2026-09-24.md)

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
| vre_short | ok | `{'entry_rate_limits': True}` | coal_twh=0.0, co2_mt_total=151.2747, lw_price=61.123, scarcity_hours=0, retired_thermal_gw=5.741, economic_retired_thermal_gw=2.6476, exogenous_retired_thermal_gw=0.1432, reserve_margin_final=0.06107, rps_dual_over_acp=1.0 |
| vre_long | ok | `{'entry_rate_limits': False}` | coal_twh=0.0, co2_mt_total=159.6764, lw_price=61.298, scarcity_hours=0, retired_thermal_gw=4.788, economic_retired_thermal_gw=2.6941, exogenous_retired_thermal_gw=0.1432, reserve_margin_final=0.05575, rps_dual_over_acp=1.0 |
