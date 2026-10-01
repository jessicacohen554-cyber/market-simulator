# PJM DAM availability — consumption wiring (ready-to-apply)

**Status (2026-07-19):** the PJM outage/availability **data + loader + pipeline +
contract + tests** are committed (branch `claude/pjm-dam-data-intake-19dqnf`).
The two edits below — the `ScenarioConfig` gate and the `data.fleet` application
— are **not committed**: they touch `src/market_sim/config/scenarios.py` (~8k
lines) and `src/market_sim/data/fleet.py` (~10.7k lines), and this session's
API-only push path (`mcp__github__push_files`) commits file content the model
must emit in the call, which cannot be done safely for files that large without
risking the truncation incident CLAUDE.md rule 27 was written to prevent. They
are captured here verbatim for a session with local `git` (Opus/Fable per the
rule-27 model-assignment clause) to apply.

Applying them makes `ScenarioConfig.pjm_dam_availability` (default **off**,
backcast only) drive the overlay through the **same bidirectional cap-1.0
water-fill the ERCOT `ercot_thermal_dam_availability` overlay already uses** —
the ERCOT block is only generalized to select its measured target by ISO+flag.

The overlay is intake-ready but **NOT yet calibration-validated**: turning it on
and choosing the final allocation/denominator is a keeper session subject to the
holdout tiers (rule 22). The transform is a fleet-wide *uniform* derate
(forced + maintenance vs the model's PJM fossil-thermal nameplate) because PJM
publishes no per-fuel-class outage split — see
`src/market_sim/data/pjm_outages.py` and `data/raw/pjm-outages/README.md`.

---

## 1. `src/market_sim/config/scenarios.py`

Add the field immediately after `ercot_thermal_dam_availability: bool = False`:

```python
    # PJM measured generation-outage availability (default off, PJM backcast-gated).
    # The PJM analogue of ercot_thermal_dam_availability: rescales the covered
    # PJM fossil-thermal classes' (COAL, CC_REGULAR, CT_PEAKER, ST_GAS + the three
    # CHP classes) class-day MEAN availability to the measured value derived from
    # PJM Data Miner 2's "Generation Outage for Seven Days by Type"
    # (gen_outages_by_type). PJM publishes outages only at RTO/sub-region
    # aggregate (never per fuel class), so the measured UNPLANNED-outage MW
    # (forced + maintenance; planned is excluded to avoid double-counting nuclear
    # refuel which the nuclear overlay carries) is converted to a single
    # fleet-wide availability fraction = 1 - outage_mw / fossil_thermal_capacity
    # and applied UNIFORMLY across the covered classes — the honest first-order
    # transform the public aggregate supports; a zone/class-resolved allocation
    # is a documented future refinement (the parquet keeps the sub-regional
    # detail). data/raw/pjm-outages/by-year/*.csv (+ gitignored
    # data/raw/pjm-dam-availability.parquet), scripts/data/derive_pjm_dam_availability.py
    # (raw fetch: scripts/data/fetch_pjm_outages.py). The published outage forecast
    # is a forward-looking, operator-published capacity-availability quantity that
    # regenerates for a future day (rule 13); forecast years keep the statistical
    # stack (the G4 mode-aware seam). Uncovered dates keep the pre-overlay
    # availability. Applied by the same bidirectional cap-1.0 water-fill as the
    # ERCOT overlay (data.fleet). See data.pjm_outages.pjm_dam_availability_series.
    # NOTE: intake-ready but NOT yet calibration-validated — turning it on and
    # choosing the final allocation/denominator is a keeper session's job
    # (subject to the holdout discipline), not the data-intake session's.
    pjm_dam_availability: bool = False
```

(No `TIER_TAGS` entry is required — the ERCOT availability analogues are not in
`TIER_TAGS` either; it is a curated subset, not an every-field registry.)

## 2. `src/market_sim/data/fleet.py`

In `generators_to_fleet_arrays`, the ERCOT thermal-DAM block currently opens with
an ERCOT-only guard that sets `_meas` from `ercot_thermal_dam_availability_series`.
Generalize the guard so `_meas` is selected by ISO+flag; the water-fill body that
follows is **unchanged**. Replace:

```python
    if (
        config is not None
        and _iso == "ERCOT"
        and getattr(config, "ercot_thermal_dam_availability", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        from market_sim.data.outages import ercot_thermal_dam_availability_series

        _meas = ercot_thermal_dam_availability_series(int(_yr), hours)
        _n_days = hours // 24
```

with:

```python
    # Select the measured class-day availability target by ISO+flag. ERCOT
    # sources it from the 60-Day DAM disclosure (per-class HSL/rating); PJM from
    # the Data Miner 2 aggregate outage feed converted to a single fleet-wide
    # fraction broadcast to every covered fossil-thermal class (a UNIFORM derate —
    # PJM publishes no per-class outage split). Both are backcast-only measured
    # inputs that REPLACE the statistical WEFOR for their covered classes and run
    # through the identical bidirectional water-fill below.
    _meas: dict[str, np.ndarray] | None = None
    if (
        config is not None
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        if _iso == "ERCOT" and getattr(config, "ercot_thermal_dam_availability", False):
            from market_sim.data.outages import ercot_thermal_dam_availability_series

            _meas = ercot_thermal_dam_availability_series(int(_yr), hours)
        elif _iso == "PJM" and getattr(config, "pjm_dam_availability", False):
            from market_sim.data.pjm_outages import pjm_dam_availability_series

            _meas = pjm_dam_availability_series(int(_yr), hours)
    if _meas:
        _n_days = hours // 24
```

And make the block's `logger.info(...)` ISO-generic — change the leading
`"ERCOT measured thermal DAM availability ..."` literal to `"%s ..."` and pass
`_iso` as the first format argument (before `_yr`).

## 3. Verify after applying

```bash
python -m pytest tests/test_pjm_dam_availability.py tests/test_outages.py -q
```

The two pre-existing `test_outages.py` failures
(`ErcotThermalDamAvailabilityTest::test_committed_series_shape_and_values` and
`NEISOUnitOutageSmokeTest::test_coal_target_is_merrimack_only_all_years`) are
unrelated stale assertions from the 2026-07-18 ST_GAS re-architecture; the ERCOT
DAM fleet-application tests (`test_fleet_application_rescales_class_day_mean`,
`test_zeroed_tranches_stay_zero_and_cap_holds`) must still pass, confirming the
guard generalization did not regress ERCOT. A quick on/off check that the PJM
overlay moves only the covered fossil-thermal classes for a backcast year (e.g.
2023) is in this branch's session notes.
