# W4 — Bake NYISO Upgraded TTC into iso_configs.py Topology

**Gap ID:** B4 (LOW)  
**Model tier:** Sonnet  
**Estimated diff:** ~5 lines in `config/iso_configs.py`

## Problem

The calibration path (`scripts/run_calibration.py`, lines 1733–1810) applies year-varying TTC overrides via `_apply_iso_year_ttc()` and `_apply_iso_monthly_ttc()`. For NYISO, these capture the Central-East AC Transmission upgrade that raised the Central-East interface TTC in later years.

The forecast path (`runner.py`) uses the static topology from `iso_configs.py` and never applies year-varying TTC overrides. A NYISO forecast always uses the original (pre-upgrade) Central-East TTC, regardless of the simulated year. For forecast years 2026+, the upgrade is already complete, so the forecast should use the upgraded value as the static default.

## What to Do

1. **In `src/market_sim/config/iso_configs.py`**, find the NYISO interface definitions and update the Central-East TTC to the post-upgrade value. The upgrade is complete as of the forecast base year (2026), so the upgraded value is the correct static default.

2. **Identify the correct value.** Check `_apply_iso_year_ttc` in the calibration script (line 1733) for the final-year TTC value for the Central-East interface. The post-upgrade value should be used as the new static default in `iso_configs.py`.

3. **Optionally**, add a comment citing the upgrade and effective year.

## What NOT to Do

- Do NOT add year-varying TTC logic to runner.py — the forecast starts at 2026 where the upgrade is already in service; a static update to the topology is sufficient.
- Do NOT change the calibration script's year-varying TTC functions — they are needed for pre-upgrade backcast years.
- Do NOT change other ISOs' TTC values.

## Acceptance Criteria

1. The NYISO Central-East interface TTC in `iso_configs.py` reflects the post-upgrade value.
2. A NYISO forecast for 2026+ uses the upgraded TTC without any runtime override.
3. Existing NYISO tests pass unchanged.
