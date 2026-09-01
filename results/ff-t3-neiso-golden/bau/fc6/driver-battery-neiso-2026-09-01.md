# Driver battery — NEISO forecast 2026-2050

*Generated 2026-09-01 by `scripts/run_driver_battery.py` (plan §2 Tier 1). Forecast probe — NOT a backcast dashboard run.*

Single-driver directional & elasticity ladders. Each expectation was **pre-registered** (in the ladder table in this script) before the run; a gated FAIL is a root-cause issue, never a threshold to widen (rules 1/11/14). This is measurement, not tuning.

## Run configuration

- **ISO:** NEISO
- **Horizon:** 2026-2050 (sequential years, rule 12)
- **Fleet representation:** legacy equal-width bins (`use_campd_bins=False`) — runtime trade, same as the tornado

## Scoreboard

**0 PASS · 0 FAIL · 0 WARN · 2 SKIP** across 1 ladders.

| Test | Driver | Expectation | Gate | Status | Detail |
|---|---|---|:--:|:--:|---|
| T1.6a | RPS/ACP vs VRE supply (short→long) | REC dual ≤ ACP ceiling | gate | SKIP | LADDER OUT OF SERVICE — pre-registered driver renewable_buildout_pace was consumed by no model code (capx-D21 §5.1, measured) and was deleted under rule 26 [R-DELETE] by capx-T16; a replacement lever is a plan §2 instrument decision pending owner sign-off |
| T1.6b | RPS/ACP vs VRE supply (short→long) | REC dual ↓ as VRE builds toward the target | gate | SKIP | LADDER OUT OF SERVICE — pre-registered driver renewable_buildout_pace was consumed by no model code (capx-D21 §5.1, measured) and was deleted under rule 26 [R-DELETE] by capx-T16; a replacement lever is a plan §2 instrument decision pending owner sign-off |

## Per-ladder rungs

### T1.6 — RPS/ACP vs VRE supply (short→long)

_rps_dual_over_acp is the final-year REC dual divided by the ISO's ACP ceiling; ≤ 1 means the ACP escape column caps the dual as designed, and it should fall as physical VRE covers the target._

| Rung | Status | Overrides | Key metrics |
|---|:--:|---|---|
