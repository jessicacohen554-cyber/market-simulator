"""Parity test for the clean-backed CAMPD emissions read path.

``campd.load_campd_hourly_clean`` — which ``load_campd_hourly`` routes through
when the opt-in ``MARKET_SIM_USE_CLEAN`` switch is set — reads curated hourly
emissions via ``scripts.lib.clean_io.read_clean("emissions", year=...)`` instead
of parsing the raw CAMPD state-year extracts. This asserts the clean-backed
loader reproduces the existing raw loader for one small ``(state, year)`` slice.

Slow / integration: it reads the real raw extracts under ``data/raw`` and the
curated clean tree (regenerate with ``python scripts/regenerate_clean.py
emissions``), so it skips cleanly when either input is absent.
"""

from __future__ import annotations

import pandas as pd
import pytest

from market_sim.config import paths
from market_sim.data import campd

pytestmark = [pytest.mark.slow, pytest.mark.integration]

# A small state present ONLY in the campd-unit-level grain, read in a non-leap
# year. The raw loader (facility-first, falling through to unit-level) and the
# clean curator (unit-first) therefore read the *same* unit-level extract with
# the *same* kg conversions, so per-plant totals match to floating point; and
# 2023 has no Feb-29 rows for the two paths to disagree on (the raw loader drops
# Feb 29, the clean tree keeps it).
_STATE = "RI"
_YEAR = 2023
_MASS_COLS = ["gross_mw", "co2_kg", "nox_kg", "so2_kg", "heat_mmbtu"]

_RAW_SLICE = paths.RAW_DATA_DIR / "campd-unit-level" / f"{_STATE}_{_YEAR}.parquet"
_CLEAN_SLICE = paths.clean_path("emissions", year=_YEAR)

_requires_inputs = pytest.mark.skipif(
    not (_RAW_SLICE.is_file() and _CLEAN_SLICE.is_file()),
    reason=(
        f"needs raw {_RAW_SLICE} and clean {_CLEAN_SLICE} "
        "(regenerate the clean slice: python scripts/regenerate_clean.py emissions)"
    ),
)


@_requires_inputs
def test_clean_matches_raw_per_plant_totals():
    """The clean-backed loader matches the raw loader for the RI/2023 slice."""
    raw = campd.load_campd_hourly([_STATE], [_YEAR])
    assert not raw.empty, "raw CAMPD slice unexpectedly empty"
    plants = set(raw["plant_id"].unique())

    # The clean datatype is partitioned by year (state is not a clean key), so
    # restrict the whole-year clean read to exactly the plants the raw
    # state-slice covers before comparing.
    clean = campd.load_campd_hourly_clean([_YEAR], plant_ids=plants)
    assert not clean.empty, "clean-backed slice unexpectedly empty"

    # Same plant coverage and (for this unit-only, non-leap slice) row count.
    assert set(clean["plant_id"].unique()) == plants
    assert len(clean) == len(raw)

    raw_tot = raw.groupby("plant_id")[_MASS_COLS].sum().sort_index()
    clean_tot = clean.groupby("plant_id")[_MASS_COLS].sum().sort_index()
    # Masses are in kg; tolerance covers summation-order float noise only.
    pd.testing.assert_frame_equal(
        clean_tot, raw_tot, rtol=1e-6, atol=1e-3, check_like=True
    )


@_requires_inputs
def test_clean_interval_start_is_tz_aware_utc():
    """The clean source carries tz-aware UTC interval starts (the contract)."""
    clean_io = campd._import_clean_io()
    utc = clean_io.read_clean(
        "emissions", year=_YEAR, validate=False, columns=["interval_start_utc"]
    )["interval_start_utc"]
    assert isinstance(utc.dtype, pd.DatetimeTZDtype)
    assert str(utc.dtype.tz) == "UTC"


def test_switch_defaults_off_and_routes_when_enabled(monkeypatch):
    """The env switch defaults OFF; when ON, load_campd_hourly uses the clean path."""
    monkeypatch.delenv("MARKET_SIM_USE_CLEAN", raising=False)
    assert campd._use_clean() is False

    # When enabled, load_campd_hourly delegates to the clean-backed loader
    # (verified without touching disk by stubbing it out).
    captured: dict[str, object] = {}

    def _fake_clean(years, *, plant_ids=None):
        captured["years"] = list(years)
        captured["plant_ids"] = plant_ids
        return pd.DataFrame({"plant_id": []})

    monkeypatch.setenv("MARKET_SIM_USE_CLEAN", "1")
    monkeypatch.setattr(campd, "load_campd_hourly_clean", _fake_clean)
    out = campd.load_campd_hourly([_STATE], [_YEAR])

    assert campd._use_clean() is True
    assert captured["years"] == [_YEAR]
    assert out.empty  # the stubbed clean frame flowed straight through
