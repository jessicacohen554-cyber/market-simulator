# W1 — Wire Hydro Monthly Energy Budget into Forecast Path

**Gap ID:** A1 (CRITICAL)  
**Model tier:** Opus  
**Estimated diff:** ~80 lines in `runner.py`, possible extraction to shared module

## Problem

The calibration path (`scripts/run_calibration.py`, lines 3020–3041) builds hydro LP units via `_hydro_fleet()` and passes `hydro_gen_idx` + `hydro_monthly_energy` to `dispatch_kwargs` (lines 3903–3904). The LP's hydro budget family (`dispatch.py`) then constrains each plant's monthly generation to its energy budget while letting it choose WHEN within the month to generate (peak shaving).

The forecast path (`src/market_sim/runner.py`) passes NEITHER key. `DispatchModel.__init__` defaults both to `None`, so the hydro budget constraint is never built. Hydro units dispatch as unconstrained thermal (pmin/pmax × availability only, no monthly energy limit). In practice the forecast LP has **no hydro at all** — no hydro generators are built.

## What to Do

1. **Extract `_hydro_fleet()` to a shared location** (e.g. `src/market_sim/data/hydro.py` alongside `load_hydro_budget`). The function is already self-contained (takes ISO, year, zone_names + optional kwargs, returns generators + monthly budgets). Do NOT duplicate it in runner.py.

2. **Call the extracted function in `runner.py`** inside the per-year fleet build, after `load_fleet_from_csv` / `bins_to_fleet` and before `generators_to_fleet_arrays`. Use `forecast_budget=True` and pass `config.hydro_year` (the wet/dry/normal lever from ScenarioConfig) — this activates the normal-water-year climatology path, NOT the measured EIA-930 monthly pin:
   ```python
   hydro_units, hydro_monthly_energy = build_hydro_fleet(
       iso, year, zone_names,
       forecast_budget=True,
       hydro_year=config.hydro_year,
   )
   hydro_gen_idx = None
   if hydro_units:
       hydro_gen_idx = np.arange(len(fleet), len(fleet) + len(hydro_units), dtype=int)
       fleet = fleet + hydro_units
       fuel_fracs = list(fuel_fracs) + [1.0] * len(hydro_units)
   ```

3. **Add `hydro_gen_idx` and `hydro_monthly_energy` to `dispatch_kwargs`** in runner.py's dict construction (around line 605).

4. **Update the calibration script** to import from the shared location instead of using its local `_hydro_fleet`.

## What NOT to Do

- Do NOT use `eia930_monthly=True` in the forecast path — that pins to measured EIA-930 data (CLAUDE.md rule #12: no measured outcomes as answers).
- Do NOT use `backfill_year` in the forecast path — that is a backcast early-release workaround.
- Do NOT change the LP formulation in `dispatch.py` — the hydro budget constraint already exists and works.
- Do NOT modify any other mechanism in this change.

## Acceptance Criteria

1. A forecast run for any ISO with hydro plants (NEISO, NYISO, PJM, CAISO) produces `hydro_gen_idx` in `dispatch_kwargs` with the correct generator indices.
2. `hydro_monthly_energy` is a `(n_hydro, 12)` array from the normal-water-year climatology.
3. The LP solve log shows hydro budget constraint rows being added.
4. A trivial test: 1 hydro unit, 1 zone, 24 hours × 31 days — verify the unit dispatches ≤ its monthly budget.
5. Existing tests pass unchanged.

## CLAUDE.md Rules

- Rule #1: This is a structural mechanism (monthly energy constraint). It stays even if the backcast fit changes.
- Rule #12: The forecast uses `forecast_monthly_hydro` (climatology), NOT `measured_monthly_hydro`. The measured path is backcast-only.
- Rule #8: Full 8760 hours always.
