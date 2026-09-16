"""SOCO per-zone solar SHAPE — the builder's physics and the reader's wiring.

Lane SOCO-32. The ``renewables.py`` and ``paths.py`` hunks are a **membership
and a registry entry**, not new ``ScenarioConfig`` fields (plan §7 gate G8), so
what these tests pin is (a) that SOCO is wired in, (b) that the transposition
arithmetic behind the committed parquet is right, and (c) — the part that
actually protects the other eight regions — that neither hunk can reach them.

Every fixture is synthetic and lives in a tempdir: nothing here reads
``data/raw`` and nothing hits the network, so the file runs unchanged under
CI's sparse checkout (plan §7 gate G17).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import SUPPORTED_ISOS, get_iso_config
from market_sim.config.paths import SOLAR_SHAPE_DIRS, solar_shape_dir
from market_sim.data import renewables as rn
from scripts.data import build_soco_solar_shape as builder

_ZONES = ["SOCO_AL", "SOCO_GA", "SOCO_MS"]
_YEAR = 2023


def _write_shape_parquet(directory, year: int, per_zone: dict[str, np.ndarray]):
    """Write a synthetic per-zone solar-shape parquet in the shared schema."""
    directory.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame({"hour": np.arange(HOURS_PER_YEAR, dtype=np.int64)})
    for zone, series in per_zone.items():
        frame[zone] = series
    path = directory / f"soco_{year}_solar_zone_shape.parquet"
    frame.to_parquet(path, index=False)
    return path


def _diurnal(peak_hour: float, amplitude: float = 1.0) -> np.ndarray:
    """Return a positive half-cosine 'solar' series peaking at ``peak_hour``."""
    hod = np.arange(HOURS_PER_YEAR) % 24
    return amplitude * np.clip(np.cos((hod - peak_hour) * np.pi / 12.0), 0.0, None)


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------


def test_soco_is_a_measured_solar_shape_region():
    """SOCO takes the measured-irradiance solar SHAPE, unconditionally."""
    assert "SOCO" in rn._SOLAR_ZONE_REANALYSIS_ISOS


def test_soco_needs_no_scenario_config_gate():
    """G8: the membership is not a field, so no keeper's cache key moves."""
    config_fields = set(vars(rn.ScenarioConfig()).keys())
    assert not any(
        name.startswith("soco_solar") or name.endswith("solar_zone_shape")
        for name in config_fields
    )


def test_solar_shape_dir_is_registered():
    """The path registry resolves SOCO, so no call site branches on the ISO."""
    assert solar_shape_dir("SOCO") == SOLAR_SHAPE_DIRS["SOCO"]
    assert solar_shape_dir("SOCO").name == "soco-solar-shape"


def test_the_two_solar_paths_are_mutually_exclusive():
    """One solar shape per region (rule 19 [R-ONE-MECH]).

    A region in both sets would have the measured parquet silently shadow its
    clear-sky shape — two mechanisms for one phenomenon, decided by the order
    of an ``if``.
    """
    assert not (rn._SOLAR_ZONE_REANALYSIS_ISOS & rn._SOLAR_ZONE_SHAPE_ISOS)


def test_no_other_region_is_registered():
    """Only SOCO. NWPP's committed solar parquet is deliberately unregistered.

    NWPP-33 landed ``data/raw/nwpp-solar-shape`` as DATA and routed arming to
    NWPP-DESK. Registering it here would arm another region's mechanism from
    this lane's file (rule 25 ``[R-ISO-SCOPE]``).
    """
    assert set(SOLAR_SHAPE_DIRS) == {"SOCO"}
    assert rn._SOLAR_ZONE_REANALYSIS_ISOS == frozenset({"SOCO"})


# ---------------------------------------------------------------------------
# The reader
# ---------------------------------------------------------------------------


def test_reader_returns_the_parquets_columns(tmp_path):
    """The committed table's zone columns come back in model-zone order."""
    per_zone = {z: _diurnal(12.0 + i) for i, z in enumerate(_ZONES)}
    _write_shape_parquet(tmp_path, _YEAR, per_zone)
    shapes = rn._solar_zone_reanalysis_shapes(
        "SOCO", "solar", _ZONES, _YEAR, data_dir=tmp_path
    )
    assert shapes.shape == (3, HOURS_PER_YEAR)
    for i, zone in enumerate(_ZONES):
        assert np.allclose(shapes[i], per_zone[zone])


def test_reader_noops_for_wind(tmp_path):
    """Wind never reaches the solar reader."""
    _write_shape_parquet(tmp_path, _YEAR, {z: _diurnal(12.0) for z in _ZONES})
    assert (
        rn._solar_zone_reanalysis_shapes(
            "SOCO", "wind", _ZONES, _YEAR, data_dir=tmp_path
        )
        is None
    )


def test_reader_noops_for_an_unregistered_region(tmp_path):
    """A region outside the membership gets None even with a parquet present."""
    _write_shape_parquet(tmp_path, _YEAR, {z: _diurnal(12.0) for z in _ZONES})
    assert (
        rn._solar_zone_reanalysis_shapes(
            "MISO", "solar", _ZONES, _YEAR, data_dir=tmp_path
        )
        is None
    )


def test_reader_noops_when_the_parquet_is_absent(tmp_path):
    """A missing year degrades to None, so the caller keeps its old behaviour."""
    assert (
        rn._solar_zone_reanalysis_shapes(
            "SOCO", "solar", _ZONES, 1999, data_dir=tmp_path
        )
        is None
    )


def test_reader_noops_when_a_zone_column_is_missing(tmp_path):
    """A table that does not cover every model zone is refused, not patched."""
    _write_shape_parquet(tmp_path, _YEAR, {z: _diurnal(12.0) for z in _ZONES[:2]})
    assert (
        rn._solar_zone_reanalysis_shapes(
            "SOCO", "solar", _ZONES, _YEAR, data_dir=tmp_path
        )
        is None
    )


def test_dispatcher_prefers_the_measured_table(tmp_path, monkeypatch):
    """_zone_renewable_shapes routes SOCO solar to the measured parquet."""
    monkeypatch.setattr(rn, "solar_shape_dir", lambda iso: tmp_path)
    per_zone = {z: _diurnal(12.0 + i) for i, z in enumerate(_ZONES)}
    _write_shape_parquet(tmp_path, _YEAR, per_zone)
    shapes = rn._zone_renewable_shapes("SOCO", "solar", _ZONES, _YEAR)
    assert np.allclose(shapes[0], per_zone["SOCO_AL"])


def test_other_regions_solar_path_is_untouched(tmp_path, monkeypatch):
    """The eight incumbent regions keep exactly the solar shape they had.

    The membership is the only thing that can reach them, and it does not.
    """
    monkeypatch.setattr(rn, "solar_shape_dir", lambda iso: tmp_path)
    _write_shape_parquet(tmp_path, _YEAR, {z: _diurnal(12.0) for z in _ZONES})
    for iso in SUPPORTED_ISOS:
        if iso == "SOCO":
            continue
        zone_names = get_iso_config(iso).zone_names
        assert rn._solar_zone_reanalysis_shapes(iso, "solar", zone_names, _YEAR) is None


# ---------------------------------------------------------------------------
# The redistribution contract — the reason a level here can never leak
# ---------------------------------------------------------------------------


def test_redistribution_preserves_the_system_series_exactly():
    """Whatever the shape says, the ISO-wide hourly series does not move.

    This is why the builder's units (Wh/m^2) are irrelevant and why no level is
    ever pinned to an actual (rule 13 ``[R-MEASURED]``): only the inter-zone
    split survives ``_redistribute_preserving_total``.
    """
    rng = np.random.default_rng(7)
    hours = 240
    cf_profile = np.clip(rng.random(hours), 0.0, 1.0)
    cap = np.array([620.7, 4132.7, 159.5])
    ramp = np.ones((3, hours))
    shapes = np.vstack(
        [_diurnal(11.25)[:hours], _diurnal(11.03)[:hours], _diurnal(11.39)[:hours]]
    )
    flat = cf_profile[None, :] * ramp
    moved = rn._redistribute_preserving_total(cf_profile, cap, ramp, shapes)
    system_flat = (flat * cap[:, None]).sum(axis=0)
    system_moved = (moved * cap[:, None]).sum(axis=0)
    assert np.abs(system_moved - system_flat).max() < 1e-9
    # And it really did move something between zones.
    assert np.abs(moved - flat).max() > 1e-6


# ---------------------------------------------------------------------------
# The builder's physics
# ---------------------------------------------------------------------------


def test_solar_position_carries_longitude_to_the_minute():
    """Solar noon moves 4 minutes per degree of longitude — measured, not assumed.

    This is the whole reason this builder exists: Georgia (-83.63 E) is 5.53
    degrees east of Mississippi (-89.16 E), so its solar noon falls
    5.53 x 4 = 22.1 minutes earlier. ``renewables._clearsky_geometry`` cannot
    express this at all — it omits longitude and the equation of time on the
    documented grounds that a shared offset cancels between zones, which is
    true for a north-south stack and false for SOCO.

    Walked on a 1-minute grid, which is also the guard against the sun position
    quietly becoming hour-resolution again (it was, in this lane's first cut:
    reading only ``.hour`` made every longitude peak in the same minute).
    """
    times = pd.date_range("2023-06-21 00:00", periods=1440, freq="1min")
    noon = {}
    for name, lon in (("GA", -83.63), ("AL", -86.35), ("MS", -89.16)):
        cos_zen, _ = builder.solar_position(31.9, lon, times)
        noon[name] = int(np.argmax(cos_zen))
    assert noon["GA"] < noon["AL"] < noon["MS"]
    assert abs((noon["MS"] - noon["GA"]) - 22.1) <= 1.0
    assert abs((noon["AL"] - noon["GA"]) - (86.35 - 83.63) * 4.0) <= 1.0


def test_solar_position_is_below_the_horizon_at_local_midnight():
    """Night is night: cos(zenith) < 0 at the local solar midnight hour."""
    times = pd.date_range("2023-06-21 00:00", periods=24, freq="1h")
    cos_zen, _ = builder.solar_position(31.9, -86.35, times)
    assert cos_zen.min() < 0.0
    assert cos_zen.max() > 0.9  # near-overhead at the summer solstice


def test_dual_axis_poa_is_the_full_beam_plus_diffuse():
    """cos(AOI) = 1 for a plane that tracks the sun in two axes."""
    n = 12
    cos_zen = np.linspace(0.1, 1.0, n)
    dni = np.full(n, 800.0)
    diffuse = np.full(n, 100.0)
    poa = builder.plane_of_array(
        dni, diffuse, cos_zen, np.full(n, 180.0), "dual_axis", 20.0, 180.0
    )
    expected = dni + diffuse * (1.0 + cos_zen) / 2.0
    assert np.allclose(poa, expected)


def test_horizontal_fixed_plane_reproduces_global_horizontal_irradiance():
    """A 0-degree 'tilt' must return GHI = DNI*cos(z) + DIFF.

    The closure identity of the whole transposition: if the plane is flat, the
    plane-of-array irradiance IS the global horizontal irradiance, which is the
    third NASA POWER parameter the builder pulls as its check.
    """
    n = 12
    cos_zen = np.linspace(0.1, 1.0, n)
    dni = np.full(n, 800.0)
    diffuse = np.full(n, 100.0)
    poa = builder.plane_of_array(
        dni, diffuse, cos_zen, np.full(n, 180.0), "fixed", 0.0, 180.0
    )
    assert np.allclose(poa, dni * cos_zen + diffuse)


def test_single_axis_tracker_is_flatter_than_fixed_tilt():
    """The tracker's beam term never falls below the fixed plane's.

    cos(AOI) for an ideal N-S horizontal tracker is sqrt(cos^2 z + east-west^2)
    >= cos z, which is what makes a high-tracking zone's shape broader than a
    high-fixed-tilt zone's — the second-order effect that separates SOCO_AL
    (30 % fixed) from SOCO_GA (14 %).
    """
    n = 48
    azimuth = np.linspace(90.0, 270.0, n)
    cos_zen = np.clip(np.cos(np.deg2rad(azimuth - 180.0)), 0.05, 1.0)
    dni = np.full(n, 700.0)
    diffuse = np.zeros(n)
    tracker = builder.plane_of_array(
        dni, diffuse, cos_zen, azimuth, "single_axis", 0.0, 180.0
    )
    horizontal = builder.plane_of_array(
        dni, diffuse, cos_zen, azimuth, "fixed", 0.0, 180.0
    )
    assert (tracker >= horizontal - 1e-9).all()
    assert tracker.max() > horizontal.max()


def test_night_hours_are_zero_for_every_tracking_class():
    """No class produces output with the sun below the horizon."""
    n = 6
    cos_zen = np.full(n, -0.3)
    dni = np.full(n, 500.0)
    diffuse = np.full(n, 50.0)
    for tech in ("fixed", "single_axis", "dual_axis"):
        poa = builder.plane_of_array(
            dni, diffuse, cos_zen, np.full(n, 180.0), tech, 20.0, 180.0
        )
        assert np.array_equal(poa, np.zeros(n))


def test_builder_writes_the_schema_the_reader_expects():
    """The builder's output columns are exactly what the reader consumes."""
    assert builder.HOUR_COLUMN == rn._WIND_SHAPE_HOUR_COLUMN
    assert builder.FILE_STEM == "solar_zone_shape"
    assert builder.SOLAR_SHAPE_DIR == SOLAR_SHAPE_DIRS["SOCO"]


def test_builder_pulls_the_two_transposition_inputs_plus_the_closure_check():
    """DNI and diffuse drive the POA; GHI is carried only as the check."""
    assert builder.NASA_PARAMETERS[:2] == (
        "ALLSKY_SFC_SW_DNI",
        "ALLSKY_SFC_SW_DIFF",
    )
    assert builder.NASA_PARAMETERS[2] == "ALLSKY_SFC_SW_DWN"


@pytest.mark.fulldata
def test_committed_parquets_carry_every_zone_and_a_full_year():
    """The three committed tables are readable and complete."""
    directory = SOLAR_SHAPE_DIRS["SOCO"]
    for year in (2023, 2024, 2025):
        path = directory / f"soco_{year}_solar_zone_shape.parquet"
        if not path.exists():
            pytest.skip(f"{path} not hydrated")
        frame = pd.read_parquet(path)
        assert len(frame) == HOURS_PER_YEAR
        assert set(_ZONES) <= set(frame.columns)
        assert (frame[_ZONES].to_numpy() >= 0.0).all()


@pytest.mark.fulldata
def test_committed_parquets_keep_the_geographic_peak_order():
    """GA peaks earliest and MS latest, every year — the east-west signature.

    If a future rebuild ever inverts this, the builder has lost its longitude
    (the defect the whole dataset exists to avoid) and the run would hold SOCO's
    solar in the wrong zone at the wrong hour.
    """
    directory = SOLAR_SHAPE_DIRS["SOCO"]
    hod = np.arange(HOURS_PER_YEAR) % 24
    for year in (2023, 2024, 2025):
        path = directory / f"soco_{year}_solar_zone_shape.parquet"
        if not path.exists():
            pytest.skip(f"{path} not hydrated")
        frame = pd.read_parquet(path).sort_values("hour")
        mean_hod = {
            zone: float(
                (frame[zone].to_numpy() * hod).sum() / frame[zone].to_numpy().sum()
            )
            for zone in _ZONES
        }
        assert mean_hod["SOCO_GA"] < mean_hod["SOCO_AL"] < mean_hod["SOCO_MS"]
