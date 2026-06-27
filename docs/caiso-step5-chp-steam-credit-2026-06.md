# CAISO Step 5 — CHP Steam-Credit HR Correction + BTM Overrides

**Branch:** `claude/caiso-rebuild-step-5-iyxoho`
**Date:** 2026-06-27
**Status:** Structural fix — pending calibration solve

## Motivation

The Step 5 diagnostic probe (PR #990, `docs/caiso-lever-c-chp-rederive-2026-06.md`)
reduced CHP must-run floors by 58% but found:

- **CT_CHP: 3.66 TWh vs 0.38 CAMPD** — purely economic over-dispatch, not
  floor-driven. The floor reduction couldn't help because CT_CHP plants were
  dispatching on merit with artificially low (steam-credited) heat rates.
- **CC_CHP band× 1.36** (target ≤1.15) — partial improvement from the floor
  reduction, but residual gap from steam-credited HRs on sub-CEMS plants.

### Root cause: steam-credited heat rates

CHP plants report an EIA-923/CAMPD "facility heat rate" that credits the
useful thermal (steam) output against the fuel input. For CT_CHP plants,
this makes simple-cycle gas turbines (power-only HR 9–11 MMBtu/MWh) appear
as efficient as combined cycles (HR 5–7 MMBtu/MWh). The model then dispatches
them as cheap baseload.

The existing EOR correction (`CAISO_EOR_TOPPING_FACTOR = 1.8`) fixed this for
3 plants (Kern River, Sycamore, Midway Sunset = 807 MW), but 55 more CT_CHP
plants (1803 MW) had the same problem.

## Changes

### A. Generalized CHP steam-credit HR correction (`fleet.py`)

Renamed `_correct_caiso_eor_power_hr` → `_correct_caiso_chp_steam_credit_hr`
and extended to correct ALL CAISO CHP plants with steam-credited heat rates:

**CT_CHP** (all plants with HR < 8.0 MMBtu/MWh):
- Correction: HR × 1.8 (same factor as the original EOR fix)
- Rationale: no simple-cycle GT achieves HR < 8.0 on a power-only basis;
  the sub-8 values are CHP accounting artifacts
- 55 plants affected, 1803 MW → avg HR 6.11 → 11.01 MMBtu/MWh
- Lands them in the simple-cycle peaker band where their power island sits

**CC_CHP** (plants with HR < 6.0 MMBtu/MWh):
- Correction: HR × 1.15, with a floor of 6.3 (the h_class CC bin)
- Rationale: CC steam credit is smaller (steam turbine is part of the power
  cycle; only process-steam extraction inflates efficiency)
- 8 plants affected, 1367 MW → avg HR 5.62 → 6.52 MMBtu/MWh

### B. Oilfield CT_CHP BTM overrides (`thermal_tranches_CAISO.csv`)

Set `chp_btm_pct = 75%` for 18 oilfield/EOR CT_CHP plants (Berry, Cymric,
Coalinga, Taft, Kern River Eastridge, South Belridge, Lost Hills, etc.) and
70% for Valero Refinery. These are industrial steam hosts where grid
electricity is a byproduct — the 50% industrial default understated their
behind-the-meter share.

- 19 plants, 342 MW nameplate
- Grid-facing capacity: 171 → 88 MW (−49%)

### C. Updated tests (`test_fleet.py`)

Renamed `TestCaisoEorPowerHr` → `TestCaisoChpSteamCreditHr` with 8 tests
covering CT_CHP correction, CC_CHP correction with floor, threshold
boundaries, non-CAISO no-op, and non-CHP group passthrough.

## Expected impact

| Lever | Before | After | Mechanism |
|-------|--------|-------|-----------|
| CT_CHP dispatch | 3.66 TWh (9.6× CAMPD) | Target ≤1.5 TWh | HR raised from 5–7 to 9–11 MMBtu/MWh; peaker merit order |
| CT_CHP grid capacity | 171 MW (oilfield subset) | 88 MW | BTM 50% → 75% for oilfield cogens |
| CC_CHP band× | 1.36 | Target ≤1.15 | HR raised from 5.6 → 6.3–6.5 for steam-credited CCs |
| CC_REGULAR | Unaffected | Unaffected | No changes to non-CHP plants |

## Admissibility (CLAUDE.md #1/#11/#12)

The steam-credit correction is a measured-physics input (thermodynamic
identity: power-only HR = facility HR × steam-credit ratio), forward-
derivable from turbine specifications, and responds to changed conditions.
It is NOT a residual fit — no parameter was tuned to the backcast error.
The BTM overrides are based on the physical steam-to-power ratio of oilfield
cogeneration facilities, not on dispatch outcomes.
