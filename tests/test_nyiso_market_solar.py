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

    # The armed energy is the DOCUMENTED level of the current keeper, not a
    # target. This assertion read `approx(0.503, rel=0.10)` — NYISO's published
    # 2024 Net Energy — which was right when the ISO-wide CF was 0.15, and went
    # STALE (failing on main) when nyiso-132 re-levelled
    # RENEWABLE_AVG_CF["NYISO"]["solar"] to the measured 0.1955 without updating
    # it. Repaired at nyiso-133 to the level that constant actually implies:
    # 389.9 MW mean-monthly x 8760 x 0.1955 = 0.668 TWh, i.e. the +33.2 % 2024
    # over-statement FINDING-nyiso132 §4 reports against interest. The
    # published 0.503 TWh is carried below as the reference it is measured
    # against, not as an assertion the model is expected to meet.
    energy_twh = float((sc_on[:, None] * s_on).sum()) / 1e6
    assert energy_twh == pytest.approx(0.670, rel=0.05)
    published_2024_twh = 0.503
    assert energy_twh > published_2024_twh  # over-stated; see cod_dates below


def _write_dual_basis_artifact(path, rows: list[tuple]) -> None:
    """Write a fixture carrying BOTH published in-service date bases."""
    with open(path, "w") as fh:
        fh.write("# test fixture\n")
        fh.write(
            "iso,year,month,model_zone,capacity_mw,n_units,"
            "capacity_mw_cod,n_units_cod\n"
        )
        for row in rows:
            fh.write(",".join(str(v) for v in row) + "\n")


def test_cod_basis_trivial_two_month_shift(tmp_path):
    """Trivial case: the two bases differ only in the switch-on month."""
    art = tmp_path / "a.csv"
    # Gold Book says the plant is on from July; EIA-860 says September.
    rows = [
        (
            "NYISO",
            2024,
            m,
            "Upstate_West",
            0.0 if m < 7 else 50.0,
            0 if m < 7 else 1,
            0.0 if m < 9 else 50.0,
            0 if m < 9 else 1,
        )
        for m in range(1, 13)
    ]
    _write_dual_basis_artifact(art, rows)
    z = ZONES.index("Upstate_West")
    gold = load_market_solar_monthly("NYISO", 2024, ZONES, path=art)
    cod = load_market_solar_monthly("NYISO", 2024, ZONES, path=art, cod_basis=True)
    assert gold[z].tolist() == [0.0] * 6 + [50.0] * 6
    assert cod[z].tolist() == [0.0] * 8 + [50.0] * 4
    # Year-end capacity — membership and nameplate — is IDENTICAL by design.
    assert gold[:, -1].tolist() == cod[:, -1].tolist()


def test_cod_basis_missing_column_hard_errors(tmp_path):
    """An armed basis never falls back to the other one silently."""
    art = tmp_path / "a.csv"
    _write_artifact(art, [("NYISO", 2024, m, "NYC", 10.0, 1) for m in range(1, 13)])
    # The default basis still reads a legacy single-basis artifact.
    assert load_market_solar_monthly("NYISO", 2024, ZONES, path=art) is not None
    with pytest.raises(ValueError, match="capacity_mw_cod"):
        load_market_solar_monthly("NYISO", 2024, ZONES, path=art, cod_basis=True)


@pytest.mark.skipif(not ARTIFACT.exists(), reason="committed artifact required")
def test_committed_artifact_cod_basis_matches_measured_identification():
    """The committed COD basis reproduces the nyiso-133 measured date swap.

    Mean-monthly registered capacity by basis, from
    ``results/calibration/_nyiso133_commissioning_ramp.json``: the EIA-860
    ``Operating Month`` basis moves 2023 UP 1.0 % (Darby and Stillwater are
    EARLIER there) and 2024 DOWN 10.2 % (Morris Ridge +2 months, High River and
    East Point +1), and leaves the flat 2025 fleet untouched. The signed-both-
    ways move is what distinguishes a basis repair from a correction fitted
    toward the residual.
    """
    expected_ratio = {2023: 1.0103, 2024: 0.8978, 2025: 1.0000}
    for year, ratio in expected_ratio.items():
        gold = load_market_solar_monthly("NYISO", year, ZONES)
        cod = load_market_solar_monthly("NYISO", year, ZONES, cod_basis=True)
        assert gold is not None and cod is not None
        assert cod.sum() / gold.sum() == pytest.approx(ratio, abs=5e-4)

    # Year-end capacity is invariant in 2024 and 2025 — the same 15 units at the
    # same published nameplates, only re-timed within the year. It is NOT
    # invariant in 2023, and that is the mechanism working rather than a leak:
    # Stillwater Solar's EIA-860 Operating Month is 2023-11 against a Gold Book
    # 2024-02, and EIA-923 records it metering 745 MWh in December 2023, so on
    # the measured basis its 20 MW belongs to the 2023 year-end fleet.
    for year in (2024, 2025):
        gold = load_market_solar_monthly("NYISO", year, ZONES)
        cod = load_market_solar_monthly("NYISO", year, ZONES, cod_basis=True)
        assert cod[:, -1].sum() == pytest.approx(gold[:, -1].sum(), abs=0.05)
    gold_2023 = load_market_solar_monthly("NYISO", 2023, ZONES)
    cod_2023 = load_market_solar_monthly("NYISO", 2023, ZONES, cod_basis=True)
    assert cod_2023[:, -1].sum() - gold_2023[:, -1].sum() == pytest.approx(
        20.0, abs=0.05
    )


@pytest.mark.skipif(not ARTIFACT.exists(), reason="committed artifact required")
def test_cod_dates_flag_off_is_byte_identical_and_on_moves_only_solar():
    """Default off is byte-identical; armed moves 2024 solar and nothing else."""
    iso_cfg = get_iso_config("NYISO")
    base = dict(mode="backcast", nyiso_solar_market_generator_basis=True)
    off = ScenarioConfig(**base)
    on = ScenarioConfig(**base, nyiso_solar_registry_cod_dates=True)

    w_off, wc_off, s_off, sc_off = load_renewable_profiles("NYISO", 2024, iso_cfg, off)
    w_on, wc_on, s_on, sc_on = load_renewable_profiles("NYISO", 2024, iso_cfg, on)

    # Wind is untouched, exactly (the K4 scope gate of PREREG-nyiso133).
    assert np.array_equal(w_off, w_on)
    assert np.array_equal(wc_off, wc_on)
    # 2024 year-end solar capacity is untouched — only the ramp inside the year
    # moves (2023 is the one year that does move; see the test above).
    assert sc_on.sum() == pytest.approx(sc_off.sum(), abs=0.05)

    off_twh = float((sc_off[:, None] * s_off).sum()) / 1e6
    on_twh = float((sc_on[:, None] * s_on).sum()) / 1e6
    # The K3 liveness gate: the armed basis must actually reach the LP bound.
    # The ENERGY ratio (0.875) is below the flat mean-monthly CAPACITY ratio
    # (0.898) because the re-timed months are not CF-neutral: Morris Ridge's
    # +2-month shift moves 179 MW out of September and October, whose solar CF
    # sits above the annual mean.
    assert on_twh / off_twh == pytest.approx(0.875, abs=0.01)
    # And it moves TOWARD NYISO's own published 2024 Net Energy (0.503 TWh)
    # without reaching it — the remaining gap is the fleet-CF composition
    # object nyiso-133 hands on, not this repair's to close.
    assert 0.503 < on_twh < off_twh


def test_cod_dates_other_iso_untouched():
    """Rule 25 — a non-NYISO ISO is unaffected even with the flag armed."""
    iso_cfg = get_iso_config("NEISO")
    off = ScenarioConfig(mode="backcast")
    on = ScenarioConfig(mode="backcast", nyiso_solar_registry_cod_dates=True)
    _, _, s_off, sc_off = load_renewable_profiles("NEISO", 2024, iso_cfg, off)
    _, _, s_on, sc_on = load_renewable_profiles("NEISO", 2024, iso_cfg, on)
    assert np.array_equal(s_off, s_on)
    assert np.array_equal(sc_off, sc_on)


def test_other_iso_solve_path_untouched():
    """A non-NYISO ISO is unaffected even with the flag armed (rule 25)."""
    iso_cfg = get_iso_config("NEISO")
    off = ScenarioConfig(mode="backcast")
    on = ScenarioConfig(mode="backcast", nyiso_solar_market_generator_basis=True)
    _, _, s_off, sc_off = load_renewable_profiles("NEISO", 2024, iso_cfg, off)
    _, _, s_on, sc_on = load_renewable_profiles("NEISO", 2024, iso_cfg, on)
    assert np.array_equal(s_off, s_on)
    assert np.array_equal(sc_off, sc_on)
