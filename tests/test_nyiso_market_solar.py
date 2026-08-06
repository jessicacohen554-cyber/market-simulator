"""Tests for the NYISO front-of-meter solar capacity basis (nyiso-128).

Covers the trivial cases first (CLAUDE.md testing pattern): a hand-written
one-zone artifact, then the committed three-year artifact, then the byte-
identity guarantee the default-off flag must honour.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.nyiso_market_solar import (
    ARTIFACT,
    load_market_solar_monthly,
)
from market_sim.data.renewables import load_renewable_profiles

ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]


def _write_artifact(path, rows: list[tuple]) -> None:
    """Write a minimal artifact CSV with the production header shape."""
    with open(path, "w") as fh:
        fh.write("# test fixture\n")
        fh.write("iso,year,month,model_zone,capacity_mw,n_units\n")
        for row in rows:
            fh.write(",".join(str(v) for v in row) + "\n")


def test_trivial_one_zone_one_month(tmp_path):
    """One zone, one month: the loader returns exactly what the artifact says."""
    art = tmp_path / "a.csv"
    _write_artifact(art, [("NYISO", 2023, m, "NYC", 100.0, 1) for m in range(1, 13)])
    monthly = load_market_solar_monthly("NYISO", 2023, ZONES, path=art)
    assert monthly is not None
    assert monthly.shape == (5, 12)
    assert monthly[ZONES.index("NYC")].tolist() == [100.0] * 12
    # Every zone absent from the artifact is an explicit zero, never a guess.
    assert monthly.sum() == pytest.approx(1200.0)


def test_ramp_is_month_resolved(tmp_path):
    """A plant entering mid-year shows up only from its in-service month."""
    art = tmp_path / "a.csv"
    rows = [
        ("NYISO", 2024, m, "Upstate_West", 0.0 if m < 7 else 50.0, 0 if m < 7 else 1)
        for m in range(1, 13)
    ]
    _write_artifact(art, rows)
    monthly = load_market_solar_monthly("NYISO", 2024, ZONES, path=art)
    z = ZONES.index("Upstate_West")
    assert monthly[z, :6].tolist() == [0.0] * 6
    assert monthly[z, 6:].tolist() == [50.0] * 6


def test_other_iso_returns_none(tmp_path):
    """Rule 25 — the mechanism never crosses an ISO boundary."""
    art = tmp_path / "a.csv"
    _write_artifact(art, [("NYISO", 2023, 1, "NYC", 1.0, 1)])
    assert load_market_solar_monthly("PJM", 2023, ZONES, path=art) is None


def test_foreign_iso_row_hard_errors(tmp_path):
    """Rule 25 — a non-NYISO row in the artifact is a hard error, not a silent read."""
    art = tmp_path / "a.csv"
    _write_artifact(art, [("PJM", 2023, 1, "NYC", 1.0, 1)])
    with pytest.raises(ValueError, match="NYISO-only"):
        load_market_solar_monthly("NYISO", 2023, ZONES, path=art)


def test_uncovered_year_returns_none(tmp_path):
    """A year the artifact does not cover leaves the EIA-860 basis untouched."""
    art = tmp_path / "a.csv"
    _write_artifact(art, [("NYISO", 2023, m, "NYC", 10.0, 1) for m in range(1, 13)])
    assert load_market_solar_monthly("NYISO", 2030, ZONES, path=art) is None


def test_missing_artifact_hard_errors(tmp_path):
    """An armed mechanism must never degrade silently to the basis it replaces."""
    with pytest.raises(FileNotFoundError, match="derive_nyiso_market_solar"):
        load_market_solar_monthly("NYISO", 2023, ZONES, path=tmp_path / "absent.csv")


@pytest.mark.skipif(not ARTIFACT.exists(), reason="committed artifact required")
def test_committed_artifact_matches_gold_book_registry():
    """The committed artifact reproduces NYISO's own published registry totals.

    Gold Book Table III-2a market-generator PV nameplate, year-end: 174.4 MW
    (2023), 573.4 MW (2024), 573.4 MW (2025 — the 2026 Gold Book confirms no
    PV market generator entered during 2025).
    """
    expected = {2023: 174.4, 2024: 573.4, 2025: 573.4}
    for year, total in expected.items():
        monthly = load_market_solar_monthly("NYISO", year, ZONES)
        assert monthly is not None
        assert monthly[:, -1].sum() == pytest.approx(total, abs=0.05)
        # Registered solar sits upstate (A-E), Capital (F-G) and Long Island
        # (K) only; the Gold Book lists no NYC or Lower-Hudson PV.
        assert monthly[ZONES.index("NYC")].sum() == 0.0
        assert monthly[ZONES.index("Lower_Hudson")].sum() == 0.0


@pytest.mark.skipif(not ARTIFACT.exists(), reason="committed artifact required")
def test_flag_off_is_byte_identical_and_on_moves_only_solar():
    """Default off changes nothing; armed changes solar and leaves wind alone."""
    iso_cfg = get_iso_config("NYISO")
    off = ScenarioConfig(mode="backcast")
    on = ScenarioConfig(mode="backcast", nyiso_solar_market_generator_basis=True)

    w_off, wc_off, s_off, sc_off = load_renewable_profiles("NYISO", 2024, iso_cfg, off)
    w_on, wc_on, s_on, sc_on = load_renewable_profiles("NYISO", 2024, iso_cfg, on)

    # Wind is untouched, exactly.
    assert np.array_equal(w_off, w_on)
    assert np.array_equal(wc_off, wc_on)

    # Solar capacity collapses to the registered market fleet.
    assert sc_off.sum() > 2000.0
    assert sc_on.sum() == pytest.approx(573.4, abs=0.05)

    # And the armed energy lands on NYISO's own published 2024 market-solar
    # output (0.503 TWh, Gold Book Table III-2a Net Energy) — the independent
    # level check that makes this an input repair rather than a retune.
    energy_twh = float((sc_on[:, None] * s_on).sum()) / 1e6
    assert energy_twh == pytest.approx(0.503, rel=0.10)


def test_other_iso_solve_path_untouched():
    """A non-NYISO ISO is unaffected even with the flag armed (rule 25)."""
    iso_cfg = get_iso_config("NEISO")
    off = ScenarioConfig(mode="backcast")
    on = ScenarioConfig(mode="backcast", nyiso_solar_market_generator_basis=True)
    _, _, s_off, sc_off = load_renewable_profiles("NEISO", 2024, iso_cfg, off)
    _, _, s_on, sc_on = load_renewable_profiles("NEISO", 2024, iso_cfg, on)
    assert np.array_equal(s_off, s_on)
    assert np.array_equal(sc_off, sc_on)
