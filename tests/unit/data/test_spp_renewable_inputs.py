"""SPP per-zone wind SHAPE and reference curtailment rate (lane SPP-32).

Both of this lane's ``renewables.py`` hunks are **memberships and a registry
entry**, not new ``ScenarioConfig`` fields (plan §7 gate G8), so what these
tests pin is (a) that SPP is wired in, (b) that the arithmetic downstream of
the wiring is right, and (c) — the part that actually protects the other six
ISOs — that neither hunk can reach them.

Every fixture is synthetic and lives in a tempdir: nothing here reads
``data/raw``, so the file runs unchanged under CI's sparse checkout (gate G17).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import WIND_SHAPE_DIRS, wind_shape_dir
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import renewables as rn

_ZONES = ["SPP-North", "SPP-South"]
_YEAR = 2023


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------


def test_spp_is_a_wind_zone_shape_iso():
    """SPP takes the per-zone wind SHAPE unconditionally, like MISO."""
    assert "SPP" in rn._WIND_ZONE_SHAPE_ISOS
    assert rn._wind_zone_shape_enabled("SPP", ScenarioConfig(iso="SPP"))


def test_spp_needs_no_scenario_config_gate():
    """G8: the membership is not a field, so no keeper's cache key moves."""
    assert "SPP" not in rn._WIND_ZONE_SHAPE_GATES


def test_spp_wind_shape_dir_is_registered():
    """The path registry resolves SPP, so no call site branches on the ISO."""
    assert wind_shape_dir("SPP") == WIND_SHAPE_DIRS["SPP"]
    assert wind_shape_dir("SPP").name == "spp-wind-shape"


def test_spp_is_an_uncurtailed_fallback_iso():
    """SPP's ~9.7%/yr wind curtailment puts it on the uncurtailed path."""
    assert "SPP" in rn._UNCURTAILED_FALLBACK_ISOS


def test_the_other_six_isos_are_untouched():
    """Neither membership reaches an ISO that already has a keeper.

    This is the G-DRIFT claim expressed as a test: both hunks are SPP-keyed
    set members, so an ISO absent from the sets keeps its prior behaviour and
    its prior cache key.
    """
    assert rn._WIND_ZONE_SHAPE_ISOS == frozenset({"MISO", "SPP"})
    # NWPP joined the fallback set at its registration (2026-09-14, lane
    # NWPP-20): no pool-wide separable curtailment series exists. SOCO joined
    # the same day (lane SOCO-20) on the same footing — no HSL, no curtailment
    # publication, no wind — a documentary no-op (no reference rate resolves).
    assert rn._UNCURTAILED_FALLBACK_ISOS == frozenset(
        {"ERCOT", "CAISO", "MISO", "SPP", "NWPP", "SOCO"}
    )
    for iso in ("PJM", "NYISO", "NEISO"):
        assert not rn._wind_zone_shape_enabled(iso, ScenarioConfig(iso=iso))
        assert wind_shape_dir(iso) is None


# ---------------------------------------------------------------------------
# The wind SHAPE loader, against a synthetic parquet
# ---------------------------------------------------------------------------


def _write_shape_parquet(directory, year: int, north, south):
    """Write a two-zone wind-shape parquet in the schema the loader expects."""
    directory.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        {
            "hour": np.arange(HOURS_PER_YEAR, dtype="int64"),
            "SPP-North": north,
            "SPP-South": south,
        }
    )
    pq.write_table(
        pa.Table.from_pandas(df, preserve_index=False),
        directory / f"spp_{year}_wind_zone_shape.parquet",
    )


def _diurnal(night_weight: float) -> np.ndarray:
    """Return a shape whose 00-06 mean is ``night_weight`` and 12-18 mean 1.0."""
    hod = np.arange(HOURS_PER_YEAR) % 24
    out = np.ones(HOURS_PER_YEAR, dtype=float)
    out[(hod >= 0) & (hod < 6)] = night_weight
    return out


def test_shape_loader_reads_both_zones(tmp_path):
    """A well-formed parquet yields one relative SHAPE row per model zone."""
    _write_shape_parquet(tmp_path, _YEAR, _diurnal(0.9), _diurnal(1.1))
    shapes = rn._wind_zone_reanalysis_shapes(
        "SPP",
        "wind",
        _ZONES,
        _YEAR,
        data_dir=tmp_path,
        config=ScenarioConfig(iso="SPP"),
    )
    assert shapes is not None
    assert shapes.shape == (2, HOURS_PER_YEAR)
    hod = np.arange(HOURS_PER_YEAR) % 24
    night = shapes[:, (hod >= 0) & (hod < 6)].mean(axis=1)
    aft = shapes[:, (hod >= 12) & (hod < 18)].mean(axis=1)
    # SPP-South is the nocturnal zone (LLJ core over OK/KS/TX Panhandle);
    # this asserts the loader preserves the sign, not that the sign is 1.1.
    assert night[0] / aft[0] < 1.0 < night[1] / aft[1]


def test_shape_loader_is_a_noop_for_solar(tmp_path):
    """Only wind is shaped here; solar keeps the legacy single profile."""
    _write_shape_parquet(tmp_path, _YEAR, _diurnal(0.9), _diurnal(1.1))
    assert (
        rn._wind_zone_reanalysis_shapes(
            "SPP",
            "solar",
            _ZONES,
            _YEAR,
            data_dir=tmp_path,
            config=ScenarioConfig(iso="SPP"),
        )
        is None
    )


def test_shape_loader_is_a_noop_when_the_parquet_is_absent(tmp_path):
    """A year with no built shape degrades to the legacy behaviour, not an error."""
    assert (
        rn._wind_zone_reanalysis_shapes(
            "SPP",
            "wind",
            _ZONES,
            2099,
            data_dir=tmp_path,
            config=ScenarioConfig(iso="SPP"),
        )
        is None
    )


def test_shape_loader_is_a_noop_when_a_zone_column_is_missing(tmp_path):
    """A parquet that does not cover every model zone is refused wholesale."""
    directory = tmp_path
    directory.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        {
            "hour": np.arange(HOURS_PER_YEAR, dtype="int64"),
            "SPP-North": np.ones(HOURS_PER_YEAR),
        }
    )
    pq.write_table(
        pa.Table.from_pandas(df, preserve_index=False),
        directory / f"spp_{_YEAR}_wind_zone_shape.parquet",
    )
    assert (
        rn._wind_zone_reanalysis_shapes(
            "SPP",
            "wind",
            _ZONES,
            _YEAR,
            data_dir=directory,
            config=ScenarioConfig(iso="SPP"),
        )
        is None
    )


# ---------------------------------------------------------------------------
# THE GATE: the redistribution identity holds to 1e-9
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ramp_on", [False, True])
def test_redistribution_preserves_the_iso_aggregate(tmp_path, ramp_on):
    """Re-splitting SPP wind across zones cannot move the ISO-wide series.

    ``Sum_z cap_z * cf_z(t)`` must equal ``M(t) = cf_profile(t) * Sum_z
    cap_z * ramp_z(t)`` in EVERY hour. This is what makes the per-zone SHAPE a
    redistribution rather than a new degree of freedom: annual energy and the
    system shape are untouched, only WHICH ZONE holds the wind moves.
    """
    _write_shape_parquet(tmp_path, _YEAR, _diurnal(0.85), _diurnal(1.15))
    shapes = rn._wind_zone_reanalysis_shapes(
        "SPP",
        "wind",
        _ZONES,
        _YEAR,
        data_dir=tmp_path,
        config=ScenarioConfig(iso="SPP"),
    )
    cap = np.array([17664.3, 17799.1])
    rng = np.random.default_rng(7)
    ramp_t = (
        rng.uniform(0.5, 1.0, size=(2, HOURS_PER_YEAR))
        if ramp_on
        else np.ones((2, HOURS_PER_YEAR))
    )
    cf_profile = np.clip(rng.uniform(0.0, 0.8, size=HOURS_PER_YEAR), 0.0, 1.0)

    cf = rn._redistribute_preserving_total(cf_profile, cap, ramp_t, shapes)

    system = cf_profile * (cap[:, None] * ramp_t).sum(axis=0)
    rebuilt = (cap[:, None] * cf).sum(axis=0)
    assert np.abs(rebuilt - system).max() / max(system.max(), 1.0) < 1e-9
    assert (cf <= 1.0 + 1e-12).all()
    assert (cf >= 0.0).all()


def test_redistribution_actually_moves_wind_between_zones(tmp_path):
    """The mechanism is not inert: differing shapes give differing zone CFs.

    Guards the ERCOT-113 silent-inertness trap — an overlay that preserves the
    aggregate by doing nothing at all would pass the identity test above.
    """
    _write_shape_parquet(tmp_path, _YEAR, _diurnal(0.5), _diurnal(1.5))
    shapes = rn._wind_zone_reanalysis_shapes(
        "SPP",
        "wind",
        _ZONES,
        _YEAR,
        data_dir=tmp_path,
        config=ScenarioConfig(iso="SPP"),
    )
    cap = np.array([17664.3, 17799.1])
    ramp_t = np.ones((2, HOURS_PER_YEAR))
    cf_profile = np.full(HOURS_PER_YEAR, 0.35)
    flat = cf_profile[None, :] * ramp_t
    cf = rn._redistribute_preserving_total(cf_profile, cap, ramp_t, shapes)
    assert np.abs(cf - flat).max() > 1e-3


# ---------------------------------------------------------------------------
# The reference curtailment rate
# ---------------------------------------------------------------------------


_CURTAILMENT_COLUMNS = [
    "iso",
    "year",
    "metric",
    "value",
    "unit",
    "basis",
    "derived",
    "source_doc",
    "source_page",
    "note",
]


def _write_curtailment_table(path, rows):
    """Write a synthetic SPP annual wind-curtailment table."""
    frame = pd.DataFrame(
        [
            {
                "iso": "SPP",
                "year": year,
                "metric": metric,
                "value": value,
                "unit": "mw",
                "basis": "test",
                "derived": "yes",
                "source_doc": "synthetic fixture",
                "source_page": "n/a",
                "note": "",
            }
            for year, metric, value in rows
        ],
        columns=_CURTAILMENT_COLUMNS,
    )
    frame.to_csv(path, index=False)


@pytest.fixture
def curtailment_table(tmp_path, monkeypatch):
    """Point the SPP provider at a synthetic table in a tempdir."""
    path = tmp_path / "spp_wind_curtailment_annual.csv"
    monkeypatch.setattr(rn, "_SPP_WIND_CURTAILMENT_ANNUAL", path)
    return path


def test_rate_is_curtailed_over_potential(curtailment_table):
    """rate = curtailed / (delivered + curtailed), on the average-MW basis."""
    _write_curtailment_table(
        curtailment_table,
        [
            (2023, "avg_hourly_curtailment_mw", 1000.0),
            (2023, "avg_hourly_wind_delivered_mw", 9000.0),
        ],
    )
    rate, year = rn._spp_wind_reference_curtailment_rate()
    assert rate == pytest.approx(0.10)
    assert year == 2023


def test_rate_is_the_mean_over_training_years(curtailment_table):
    """Multiple training years average, and the tag is the latest of them."""
    _write_curtailment_table(
        curtailment_table,
        [
            (2023, "avg_hourly_curtailment_mw", 1000.0),
            (2023, "avg_hourly_wind_delivered_mw", 9000.0),
            (2024, "avg_hourly_curtailment_mw", 2000.0),
            (2024, "avg_hourly_wind_delivered_mw", 8000.0),
        ],
    )
    rate, year = rn._spp_wind_reference_curtailment_rate()
    assert rate == pytest.approx((0.10 + 0.20) / 2)
    assert year == 2024


def test_holdout_years_can_never_enter_the_rate(curtailment_table):
    """2019 and 2022 rows are excluded by construction, not by discipline.

    SPP's real table carries both (rule 22 ``[R-HOLDOUT]`` years), so the
    restriction to 2023-2025 is load-bearing rather than decorative.
    """
    assert 2019 not in rn._SPP_REFERENCE_RATE_YEARS
    assert 2022 not in rn._SPP_REFERENCE_RATE_YEARS
    _write_curtailment_table(
        curtailment_table,
        [
            (2019, "avg_hourly_curtailment_mw", 9999.0),
            (2019, "avg_hourly_wind_delivered_mw", 1.0),
            (2022, "avg_hourly_curtailment_mw", 9999.0),
            (2022, "avg_hourly_wind_delivered_mw", 1.0),
            (2023, "avg_hourly_curtailment_mw", 1000.0),
            (2023, "avg_hourly_wind_delivered_mw", 9000.0),
        ],
    )
    rate, year = rn._spp_wind_reference_curtailment_rate()
    assert rate == pytest.approx(0.10)
    assert year == 2023


def test_a_year_missing_either_leg_is_dropped(curtailment_table):
    """Both legs must be present; a half-populated year contributes nothing."""
    _write_curtailment_table(
        curtailment_table,
        [
            (2023, "avg_hourly_curtailment_mw", 1000.0),
            (2023, "avg_hourly_wind_delivered_mw", 9000.0),
            (2024, "avg_hourly_curtailment_mw", 2000.0),
        ],
    )
    rate, year = rn._spp_wind_reference_curtailment_rate()
    assert rate == pytest.approx(0.10)
    assert year == 2023


def test_missing_table_returns_none(tmp_path, monkeypatch):
    """No table -> None, and the caller keeps the delivered profile."""
    monkeypatch.setattr(rn, "_SPP_WIND_CURTAILMENT_ANNUAL", tmp_path / "absent.csv")
    assert rn._spp_wind_reference_curtailment_rate() is None


def test_provider_is_reached_through_the_registry(curtailment_table, monkeypatch):
    """``_reference_curtailment_rate`` routes SPP wind via the registry.

    Rule 24 ``[R-REGISTRY]``: a new ISO registers a callable rather than
    growing an ``if iso ==`` ladder. The HSL probe is stubbed out so the test
    exercises the registry rather than a hydrated HSL parquet.
    """
    assert rn._ANNUAL_REFERENCE_RATE_PROVIDERS[("SPP", "wind")] is (
        rn._spp_wind_reference_curtailment_rate
    )
    _write_curtailment_table(
        curtailment_table,
        [
            (2023, "avg_hourly_curtailment_mw", 1000.0),
            (2023, "avg_hourly_wind_delivered_mw", 9000.0),
        ],
    )
    monkeypatch.setattr(rn, "load_hsl_hourly", lambda iso, year: None)
    assert rn._reference_curtailment_rate("SPP", "wind")[0] == pytest.approx(0.10)


def test_spp_solar_has_no_reference_rate(monkeypatch):
    """SPP solar is ~0.73% of SPP's curtailment and keeps the delivered profile."""
    monkeypatch.setattr(rn, "load_hsl_hourly", lambda iso, year: None)
    assert rn._reference_curtailment_rate("SPP", "solar") is None


def test_registry_does_not_capture_any_other_iso(monkeypatch):
    """The registry holds SPP wind and nothing else."""
    assert set(rn._ANNUAL_REFERENCE_RATE_PROVIDERS) == {("SPP", "wind")}
    monkeypatch.setattr(rn, "load_hsl_hourly", lambda iso, year: None)
    for iso in ("PJM", "NYISO", "NEISO"):
        assert rn._reference_curtailment_rate(iso, "wind") is None
