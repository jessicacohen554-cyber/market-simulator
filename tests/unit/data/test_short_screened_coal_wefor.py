"""Tests for ``ScenarioConfig.wefor_residual_short_screened_coal`` (miso-273).

The short coal family measures the sub-5-day forced outages of the coal
unit-years that pass its baseload guard; the screened-set derive output names
those unit-years, and :func:`outages.short_screened_coal_shares` turns them into
each coal bin's measured capacity share on the short overlay's own numerator
(extract unit MW) and denominator (the dispatched bin's pmax).
"""

from __future__ import annotations

import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import outages


def _write_screened(tmp_path, monkeypatch, rows):
    monkeypatch.setattr(outages, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
    pd.DataFrame(
        rows,
        columns=[
            "facility_name",
            "facility_id",
            "unit_id",
            "year",
            "unit_capacity_mw",
            "plant_group",
            "capacity_source",
            "when_operable_cf",
        ],
    ).to_csv(tmp_path / "campd-unit-outages-short-screened-MISO.csv", index=False)


def test_share_is_screened_mw_over_dispatched_bin(tmp_path, monkeypatch):
    """Two of three units screened -> their MW over the bin pmax; year-scoped."""
    _write_screened(
        tmp_path,
        monkeypatch,
        [
            ("A", 10, "1", 2023, 300.0, "COAL", "eia_exact", 0.8),
            ("A", 10, "2", 2023, 300.0, "COAL", "eia_exact", 0.7),
            ("A", 10, "3", 2022, 300.0, "COAL", "eia_exact", 0.7),
            ("B", 20, "1", 2023, 700.0, "COAL", "eia_exact", 0.9),
        ],
    )
    roster = (((10, "COAL"), 900.0), ((20, "COAL"), 600.0), ((30, "COAL"), 500.0))
    got = outages.short_screened_coal_shares(2023, "MISO", roster)
    assert got[(10, "COAL")] == pytest.approx(600.0 / 900.0)
    # nameplate-share numerator above a net-summer bin clips at 1
    assert got[(20, "COAL")] == 1.0
    # an unscreened bin carries no share (keeps the full statistical term)
    assert (30, "COAL") not in got


def test_bin_absent_from_roster_is_skipped(tmp_path, monkeypatch):
    """A screened unit whose bin the LP does not dispatch contributes nothing."""
    _write_screened(
        tmp_path, monkeypatch, [("A", 10, "1", 2023, 300.0, "COAL", "x", 0.8)]
    )
    assert outages.short_screened_coal_shares(2023, "MISO", ()) == {}


def test_missing_file_is_empty(tmp_path, monkeypatch):
    """An ISO without the derive output gets no relief."""
    monkeypatch.setattr(outages, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
    assert (
        outages.short_screened_coal_shares(2023, "MISO", (((10, "COAL"), 1.0),)) == {}
    )


def test_fails_closed_without_roster_or_on_ercot():
    """Non-ERCOT only; the dispatched-bin roster is required."""
    with pytest.raises(ValueError):
        outages.short_screened_coal_shares(2023, "ERCOT", ())
    with pytest.raises(ValueError):
        outages.short_screened_coal_shares(2023, "MISO", None)


def test_default_off():
    """The field ships off, so every existing run is byte-inert."""
    assert ScenarioConfig().wefor_residual_short_screened_coal is False


def test_blend_formula_matches_relief_semantics():
    """wefor_eff = (1-s) w + s min(w, res): s=0 identity, s=1 full cap."""
    w, res = 0.08, 0.0

    def eff(s):
        return (1.0 - s) * w + s * min(w, res)

    assert eff(0.0) == w
    assert eff(1.0) == res
    assert eff(0.5) == pytest.approx(0.04)
