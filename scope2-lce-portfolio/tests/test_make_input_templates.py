"""Tests for the full-8760 fillable skeleton template generator (HP-01 §5).

Data-free and RNG-free: scripts/make_input_templates.py is a pure function of
its arguments, so shapes/coverage are checked directly and the "fillable"
promise is checked by round-tripping through the real intake functions both
as-generated (placeholder values) and after overwriting the placeholders.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from make_input_templates import (  # noqa: E402
    DEFAULT_ISOS,
    main,
    make_annual_average_lmp_skeleton,
    make_hourly_lmp_skeleton,
    make_load_skeleton,
)

from lce_portfolio.config import HOURS_PER_YEAR, LMP_KIND_ANNUAL_AVERAGE_FLAT  # noqa: E402
from lce_portfolio.intake import (  # noqa: E402
    aggregate_by_hour_iso,
    load_intake,
    prepare_lmp,
)

_ISOS = ["ERCOT", "CAISO"]


def test_default_isos_are_the_six_real_isos() -> None:
    """The generator's default target is the tool's six real ISOs."""
    assert set(DEFAULT_ISOS) == {"ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"}


def test_make_load_skeleton_full_calendar_per_iso() -> None:
    """Every requested ISO carries the complete 0..HOURS_PER_YEAR-1 calendar."""
    df = make_load_skeleton(_ISOS)
    assert set(df.columns) == {"hour", "iso", "facility", "load_mwh"}
    assert len(df) == HOURS_PER_YEAR * len(_ISOS)
    for iso in _ISOS:
        hours = sorted(df.loc[df["iso"] == iso, "hour"])
        assert hours == list(range(HOURS_PER_YEAR))


def test_make_hourly_lmp_skeleton_full_calendar_per_iso() -> None:
    """Every requested ISO carries the complete hourly LMP calendar."""
    df = make_hourly_lmp_skeleton(_ISOS)
    assert set(df.columns) == {"hour", "iso", "lmp"}
    assert len(df) == HOURS_PER_YEAR * len(_ISOS)
    for iso in _ISOS:
        hours = sorted(df.loc[df["iso"] == iso, "hour"])
        assert hours == list(range(HOURS_PER_YEAR))


def test_make_annual_average_lmp_skeleton_one_row_per_iso() -> None:
    """One row per ISO, no hour column (HP-01 §2b annual-average schema)."""
    df = make_annual_average_lmp_skeleton(_ISOS)
    assert set(df.columns) == {"iso", "annual_avg_lmp"}
    assert len(df) == len(_ISOS)
    assert sorted(df["iso"]) == sorted(_ISOS)


def test_load_skeleton_round_trips_through_intake_unmodified(tmp_path) -> None:
    """The generated load skeleton passes intake validation as-is (placeholder
    values already satisfy every check: finite, non-negative, full calendar)."""
    path = tmp_path / "load_skeleton.csv"
    make_load_skeleton(_ISOS).to_csv(path, index=False)

    df = load_intake(path)  # raises on missing columns / bad hour range
    by_iso = aggregate_by_hour_iso(df)  # raises on dup rows / missing hours
    assert set(by_iso) == set(_ISOS)
    for iso in _ISOS:
        assert by_iso[iso].shape == (HOURS_PER_YEAR,)


def test_hourly_lmp_skeleton_round_trips_after_filling_values(tmp_path) -> None:
    """After overwriting the placeholder lmp values, prepare_lmp succeeds with
    zero validation errors and reports the hourly lmp_kind."""
    df = make_hourly_lmp_skeleton(_ISOS)
    rng_shape = np.arange(len(df))
    df["lmp"] = 20.0 + 0.01 * (rng_shape % HOURS_PER_YEAR)  # deterministic fill
    path = tmp_path / "lmp_skeleton.csv"
    df.to_csv(path, index=False)

    for iso in _ISOS:
        lmp, lmp_kind = prepare_lmp(path, iso)
        assert lmp.shape == (HOURS_PER_YEAR,)
        assert lmp_kind == "hourly"


def test_annual_average_skeleton_round_trips_after_filling_values(tmp_path) -> None:
    """After overwriting the placeholder annual_avg_lmp values, prepare_lmp
    expands each ISO to a flat vector with zero validation errors."""
    df = make_annual_average_lmp_skeleton(_ISOS)
    df["annual_avg_lmp"] = [42.5, 55.0][: len(df)]
    path = tmp_path / "annual_avg_skeleton.csv"
    df.to_csv(path, index=False)

    lmp, lmp_kind = prepare_lmp(path, "ERCOT")
    assert lmp_kind == LMP_KIND_ANNUAL_AVERAGE_FLAT
    assert np.all(lmp == 42.5)


def test_main_writes_three_skeleton_files(tmp_path) -> None:
    """main() writes the load, hourly-LMP, and annual-average-LMP skeletons."""
    out_dir = tmp_path / "skeletons"
    rc = main(["--isos", "ERCOT", "CAISO", "--out-dir", str(out_dir)])
    assert rc == 0

    load_path = out_dir / "load_8760_by_facility_skeleton.csv"
    lmp_path = out_dir / "lmp_8760_skeleton.csv"
    annual_path = out_dir / "lmp_annual_average_skeleton.csv"
    assert load_path.exists() and lmp_path.exists() and annual_path.exists()

    assert set(pd.read_csv(load_path)["iso"].unique()) == {"ERCOT", "CAISO"}
    assert set(pd.read_csv(lmp_path)["iso"].unique()) == {"ERCOT", "CAISO"}
    assert set(pd.read_csv(annual_path)["iso"].unique()) == {"ERCOT", "CAISO"}
