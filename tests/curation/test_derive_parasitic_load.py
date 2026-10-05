"""Tests for ``scripts/data/derive_parasitic_load.py`` (merge, check, streaming)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.data import derive_parasitic_load as dpl


def _rows(records: list[tuple]) -> pd.DataFrame:
    """Build a parasitic frame from ``(plant, year, factor, source)`` tuples."""
    return pd.DataFrame(
        [
            {
                "plant_id": p,
                "year": y,
                "gross_mwh": 100.0,
                "net_mwh": 100.0 * f,
                "parasitic_factor": f,
                "parasitic_load_pct": 1.0 - f,
                "source": s,
                "flag": "ok" if s == "measured" else "no_net",
            }
            for p, y, f, s in records
        ]
    )


def test_merge_keeps_committed_rows_and_adds_new_plants() -> None:
    """Committed rows stay byte-identical; a new plant gains rows + pooled."""
    existing = _rows(
        [
            (1, 0, 0.95, "measured"),
            (1, 2023, 0.95, "measured"),
            (3, 2022, 0.92, "measured"),  # per-year only, no pooled row
        ]
    )
    fresh = _rows(
        [
            (3, 0, 0.91, "measured"),  # pooled for a per-year-only plant: added
            (3, 2022, 0.80, "measured"),  # committed plant-year: kept as-is
            (1, 0, 0.90, "measured"),  # pooled for a covered plant: dropped
            (1, 2023, 0.90, "measured"),  # committed plant-year: kept as-is
            (1, 2019, 0.94, "measured"),  # absent plant-year: added
            (2, 0, 0.97, "measured"),  # new plant pooled: added
            (2, 2019, 0.97, "measured"),
        ]
    )
    out = dpl.merge_parasitic(existing, fresh)
    by_key = out.set_index(["plant_id", "year"])["parasitic_factor"]
    assert by_key[(1, 0)] == 0.95
    assert by_key[(1, 2023)] == 0.95
    assert by_key[(1, 2019)] == 0.94
    assert by_key[(2, 0)] == 0.97
    assert by_key[(3, 0)] == 0.91
    assert by_key[(3, 2022)] == 0.92
    assert len(out) == 7
    assert list(out["plant_id"]) == sorted(out["plant_id"])


def test_merge_never_adds_a_class_default_row() -> None:
    """An unmeasurable plant-year stays absent so consumers keep their fallback."""
    existing = _rows([(1, 0, 0.95, "measured")])
    fresh = _rows(
        [
            (2, 0, 0.97, "class_default"),
            (2, 2023, 0.97, "class_default"),
            (1, 2024, 0.97, "class_default"),
            (3, 0, 0.93, "measured"),
            (3, 2023, 0.97, "class_default"),
        ]
    )
    out = dpl.merge_parasitic(existing, fresh)
    assert set(map(tuple, out[["plant_id", "year"]].to_numpy())) == {(1, 0), (3, 0)}
    assert set(out["source"]) == {"measured"}


def test_reproduce_check_flags_factor_and_source_drift() -> None:
    """A shared plant-year fails on |diff| > tol or a changed source."""
    existing = _rows(
        [
            (1, 0, 0.95, "measured"),
            (1, 2023, 0.950, "measured"),
            (2, 2023, 0.930, "class_default"),
            (3, 2023, 0.960, "measured"),
        ]
    )
    fresh = _rows(
        [
            (1, 0, 0.80, "measured"),  # pooled rows are never compared
            (1, 2023, 0.953, "measured"),
            (2, 2023, 0.931, "measured"),
            (3, 2023, 0.950, "measured"),
            (4, 2023, 0.900, "measured"),  # not shared: not compared
        ]
    )
    cmp = dpl.reproduce_check(existing, fresh, tol=0.005).set_index("plant_id")
    assert set(cmp.index) == {1, 2, 3}
    assert bool(cmp.loc[1, "within_tol"])
    assert not bool(cmp.loc[2, "within_tol"])  # source changed
    assert not bool(cmp.loc[3, "within_tol"])  # 0.010 > tol


def test_campd_totals_sums_across_extracts(monkeypatch) -> None:
    """Per-extract totals summed per plant-year equal one pooled call."""
    hourly = {
        ("AA", 2023): pd.DataFrame(
            {
                "plant_id": [1, 1, 2],
                "year": [2023, 2023, 2023],
                "gross_mw": [10.0, 0.0, 5.0],
                "heat_mmbtu": [100.0, 0.0, 50.0],
                "co2_kg": [1.0, 0.0, 1.0],
                "nox_kg": [0.0, 0.0, 0.0],
                "so2_kg": [0.0, 0.0, 0.0],
                "facility_name": ["A", "A", "B"],
                "date": pd.to_datetime(["2023-01-05", "2023-02-05", "2023-01-05"]),
            }
        ),
        ("BB", 2023): pd.DataFrame(
            {
                "plant_id": [1],
                "year": [2023],
                "gross_mw": [4.0],
                "heat_mmbtu": [40.0],
                "co2_kg": [1.0],
                "nox_kg": [0.0],
                "so2_kg": [0.0],
                "facility_name": ["A"],
                "date": pd.to_datetime(["2023-01-09"]),
            }
        ),
    }

    def fake_load(states, years):
        return hourly.get((states[0], years[0]), pd.DataFrame())

    monkeypatch.setattr(dpl.campd, "load_campd_hourly", fake_load)
    annual, monthly = dpl.campd_totals(["AA", "BB", "CC"], [2023])
    out = annual.set_index("plant_id")
    assert out.loc[1, "gross_mwh"] == 14.0
    assert out.loc[1, "op_hours"] == 2
    assert out.loc[2, "gross_mwh"] == 5.0
    pooled = dpl.campd.annual_plant_totals(pd.concat(list(hourly.values())))
    pooled = pooled.set_index("plant_id")
    assert out.loc[1, "heat_mmbtu"] == pooled.loc[1, "heat_mmbtu"]
    by_month = monthly.set_index(["plant_id", "month"])["gross_mwh"]
    assert by_month[(1, 1)] == 14.0
    assert by_month[(1, 2)] == 0.0
    assert by_month[(2, 1)] == 5.0


def _months(
    pid: int, slope: float, intercept: float, gross: np.ndarray
) -> pd.DataFrame:
    """Monthly rows whose net is exactly ``intercept + slope * gross``."""
    return pd.DataFrame(
        {
            "plant_id": pid,
            "year": 2021,
            "month": np.arange(1, len(gross) + 1),
            "gross_mwh": gross,
            "net_mwh": intercept + slope * gross,
        }
    )


def test_running_slope_recovers_running_factor_not_annual_ratio() -> None:
    """A fixed offline draw lowers the annual ratio but not the running slope."""
    gross = np.linspace(50_000, 400_000, 12)
    m = _months(1, 0.93, -12_000.0, gross)
    out = dpl.running_parasitic_factors(m, {1: {"COAL"}})
    assert len(out) == 1
    assert abs(out.parasitic_factor.iloc[0] - 0.93) < 1e-6
    assert out.source.iloc[0] == "measured_running"
    assert m.net_mwh.sum() / m.gross_mwh.sum() < 0.93


def test_running_slope_skips_ct_mixed_positive_intercept_out_of_band() -> None:
    """CT, mixed-family, positive-intercept and out-of-band plants get no row."""
    gross = np.linspace(50_000, 400_000, 12)
    m = pd.concat(
        [
            _months(2, 0.95, -1_000.0, gross),
            _months(3, 0.95, -1_000.0, gross),
            _months(4, 0.95, 5_000.0, gross),
            _months(5, 0.70, -1_000.0, gross),
        ]
    )
    fams = {2: {"CT"}, 3: {"COAL", "CC"}, 4: {"CC"}, 5: {"ST"}}
    assert dpl.running_parasitic_factors(m, fams).empty


def test_fill_gives_uncovered_fleet_plants_their_largest_family_default() -> None:
    """Only fleet plants without a pooled row are filled, at the dominant family."""
    parasitic = _rows([(1, 0, 0.95, "measured"), (2, 2022, 0.90, "measured")])
    family_mw = {
        1: {"COAL": 500.0},  # already pooled: untouched
        2: {"CC": 600.0, "CT": 100.0},  # per-year only: filled at CC
        3: {"CT": 200.0},
        4: {},  # no combustion family: no row
    }
    fill = dpl.fleet_class_default_rows(parasitic, family_mw).set_index("plant_id")
    assert set(fill.index) == {2, 3}
    assert fill.loc[2, "parasitic_factor"] == 0.975
    assert fill.loc[3, "parasitic_factor"] == 0.99
    assert set(fill["source"]) == {"class_default_fleet"}
    assert set(fill["year"]) == {0}
