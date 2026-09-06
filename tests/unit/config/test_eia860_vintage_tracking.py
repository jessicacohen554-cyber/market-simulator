"""pjm-167: the backcast EIA-860 vintage resolves from the SOLVED year.

Guards ``paths.resolve_backcast_eia860_vintage`` — the one place both backcast
entry points (``scripts/run_calibration.py::run_year`` and
``runner.run_scenario_iso``) resolve the vintage, per rule 19 ``[R-ONE-MECH]``.

The defect it exists for (FINDING-pjm167-input-clock-2021-2022-2026-09-06.md §3):
``eia860_vintage_year`` is a RUN-level scalar while a rule-16 ``[R-ALLYEARS]``
bundle spans three years, so the model read one 2025-Early-Release snapshot for
every solved year and carried an identical 38,722 MW PJM coal fleet in 2021,
2022 and 2023.
"""

from __future__ import annotations

from market_sim.config.paths import (
    EIA_860_DIR,
    active_eia860_dir,
    resolve_backcast_eia860_vintage,
    set_eia860_vintage,
)
from market_sim.config.scenarios import ScenarioConfig


def test_gate_is_off_by_default() -> None:
    """The mechanism ships disarmed, so every existing run is unchanged."""
    assert ScenarioConfig().eia860_vintage_tracks_solve_year is False
    assert ScenarioConfig().eia860_vintage_year is None


def test_off_resolves_to_none_for_every_year() -> None:
    """Disarmed, the resolution is byte-identical to the pre-pjm-167 behaviour."""
    for year in (2019, 2021, 2023, 2025):
        assert resolve_backcast_eia860_vintage(None, year, False) is None


def test_armed_resolves_to_the_solved_year() -> None:
    """Armed, each year of a multi-year bundle reads its own annual release."""
    for year in (2021, 2022, 2023):
        assert resolve_backcast_eia860_vintage(None, year, True) == year


def test_explicit_pin_wins_over_tracking() -> None:
    """An explicit ``eia860_vintage_year`` keeps its exact meaning and cache key."""
    assert resolve_backcast_eia860_vintage(2024, 2021, True) == 2024
    assert resolve_backcast_eia860_vintage(2024, 2021, False) == 2024


def test_no_solve_year_falls_through() -> None:
    """A caller with no single year in hand gets the canonical snapshot."""
    assert resolve_backcast_eia860_vintage(None, None, True) is None


def test_missing_vintage_directory_degrades_to_the_canonical_snapshot() -> None:
    """A year with no committed ``vintage_<year>/`` must not fail the solve."""
    try:
        assert set_eia860_vintage(1990) == EIA_860_DIR
        assert active_eia860_dir() == EIA_860_DIR
    finally:
        set_eia860_vintage(None)


def test_committed_vintage_directory_is_selected() -> None:
    """A committed vintage redirects the loaders; ``None`` restores the default."""
    try:
        for year in (2021, 2022, 2023, 2024):
            candidate = EIA_860_DIR / f"vintage_{year}"
            expected = candidate if candidate.is_dir() else EIA_860_DIR
            assert set_eia860_vintage(year) == expected
    finally:
        set_eia860_vintage(None)
    assert active_eia860_dir() == EIA_860_DIR
