"""The UC commitment demand data layer (``data/commitment_demand.py``, lane UC-1-FIX-7).

Trivial cases first: the data-QA cut on synthetic hours, the zone mapping on
a two-zone toy, the forward season x hour lookup, then the dispatcher.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import market_sim.data.commitment_demand as cd
from market_sim.config.constants import (
    COMMITMENT_DF_DATA_ERROR_FRACTION,
    HOURS_PER_YEAR,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import UC_COMMITMENT_DEMAND_SOURCES
from tests.helpers.stale_snapshot import disable_stale_snapshot_repair_mp


def _cfg_zones(names, shares=None):
    """A stand-in ISO config: ``zone_names`` plus per-zone ``load_share``."""
    shares = [1.0] * len(names) if shares is None else shares
    return SimpleNamespace(
        name="TOY",
        zone_names=list(names),
        zones=[SimpleNamespace(name=n, load_share=s) for n, s in zip(names, shares)],
    )


def test_sources_in_step_with_the_config():
    assert cd.COMMITMENT_DEMAND_SOURCES == UC_COMMITMENT_DEMAND_SOURCES


def test_qa_drops_missing_and_gross_errors():
    actual = np.array([100.0, 100.0, 100.0, 100.0, 0.0, 100.0])
    forecast = np.array(
        [
            103.0,
            97.0,
            100.0 + 100.0 * COMMITMENT_DF_DATA_ERROR_FRACTION,
            170.0,
            5.0,
            np.nan,
        ]
    )
    err, valid = cd.qa_forecast_error(forecast, actual)
    assert valid.tolist() == [True, True, True, False, False, False]
    np.testing.assert_allclose(err, [3.0, -3.0, 30.0, 0.0, 0.0, 0.0])


def test_backcast_increment_uses_the_loader_zone_weights_and_losses(monkeypatch):
    """The BA error is split by the demand loader's own weights and grossed up
    by the same loss factor -- the forecast mapped to zones as the actual is."""
    import market_sim.data.eia930 as e9

    err = np.zeros(HOURS_PER_YEAR)
    err[:3] = [100.0, -40.0, 0.0]
    monkeypatch.setattr(cd, "ba_forecast_error_mw", lambda iso, year, **k: (err, 7))
    w = np.vstack([np.full(HOURS_PER_YEAR, 0.25), np.full(HOURS_PER_YEAR, 0.75)])
    monkeypatch.setattr(e9, "load_zone_weights", lambda *a, **k: w)
    inc, dropped = cd.backcast_commitment_increment(
        "SPP", 2020, _cfg_zones(["A", "B"]), ["A", "B"], td_loss_factor=0.1
    )
    assert dropped == 7 and inc.shape == (2, HOURS_PER_YEAR)
    np.testing.assert_allclose(inc[:, 0], [27.5, 82.5])
    np.testing.assert_allclose(inc[:, 1], [-11.0, -33.0])
    np.testing.assert_allclose(inc.sum(axis=0)[:2], [110.0, -44.0])


def test_ba_error_reads_the_hourly_frame(monkeypatch):
    import market_sim.data.eia930 as e9

    frame = pd.DataFrame(
        {
            "Demand": np.full(HOURS_PER_YEAR, 1000.0),
            "Demand forecast": np.r_[
                1050.0, 5000.0, np.full(HOURS_PER_YEAR - 2, 990.0)
            ],
        }
    )
    monkeypatch.setattr(e9, "_eia_hourly_frame_filled", lambda ba, year: frame)
    err, dropped = cd.ba_forecast_error_mw("NEISO", 2020)
    assert dropped == 1
    assert err[0] == 50.0 and err[1] == 0.0 and err[2] == -10.0
    monkeypatch.setattr(e9, "_eia_hourly_frame_filled", lambda ba, year: None)
    with pytest.raises(ValueError, match="no EIA-930 hourly frame"):
        cd.ba_forecast_error_mw("NEISO", 2020)


def _profile(bias_by_season: dict[str, float]) -> pd.DataFrame:
    rows = [
        dict(season=s, hour_of_day=h, bias_frac=b + h * 1e-4)
        for s, b in bias_by_season.items()
        for h in range(24)
    ]
    return pd.DataFrame(rows)


def test_forward_bias_maps_season_and_hour():
    prof = _profile({"DJF": 0.01, "MAM": 0.02, "JJA": 0.03, "SON": 0.04})
    frac = cd.forward_bias_fraction(prof)
    assert frac.shape == (HOURS_PER_YEAR,)
    assert frac[0] == pytest.approx(0.01)  # Jan 1, 00:00
    assert frac[5] == pytest.approx(0.01 + 5e-4)
    jul1_17 = (31 + 28 + 31 + 30 + 31 + 30) * 24 + 17
    assert frac[jul1_17] == pytest.approx(0.03 + 17e-4)
    assert frac[-1] == pytest.approx(0.01 + 23e-4)  # Dec 31, 23:00
    with pytest.raises(ValueError, match="lacks"):
        cd.forward_bias_fraction(prof[prof.season != "SON"])


def test_dispatcher(monkeypatch):
    demand = np.full((2, 24), 100.0)
    actual = cd.commitment_demand(
        SimpleNamespace(uc_commitment_demand_source="actual"), demand
    )
    assert actual.demand is demand and actual.basis == "actual"

    monkeypatch.setattr(
        cd,
        "load_forecast_error_profile",
        lambda iso: _profile({"DJF": 0.02, "MAM": 0.0, "JJA": 0.0, "SON": 0.0}),
    )
    fwd = cd.commitment_demand(
        SimpleNamespace(
            uc_commitment_demand_source="da_forecast", mode="forecast", iso="SPP"
        ),
        demand,
        ["SPP-North", "SPP-South"],
    )
    assert fwd.basis == "error_profile"
    np.testing.assert_allclose(fwd.demand[:, 0], 102.0)
    np.testing.assert_allclose(fwd.demand[:, 3], 100.0 * (1.02 + 3e-4))
    row = fwd.log_row(demand)
    assert row["increment_min_mw"] == pytest.approx(4.0)


# --------------------------------------------------------------------------- #
# Row mapping by zone name (lane UC-1-FIX-8)                                   #
# --------------------------------------------------------------------------- #
_LOAD = ["A", "B", "C"]
_W = np.vstack(
    [
        np.full(HOURS_PER_YEAR, 0.2),
        np.full(HOURS_PER_YEAR, 0.3),
        np.full(HOURS_PER_YEAR, 0.5),
    ]
)


def _err() -> np.ndarray:
    rng = np.random.default_rng(8)
    return rng.normal(0.0, 500.0, HOURS_PER_YEAR)


def _patch_backcast(monkeypatch, weights, err, dropped=0):
    import market_sim.data.eia930 as e9

    monkeypatch.setattr(
        cd, "ba_forecast_error_mw", lambda iso, year, **k: (err, dropped)
    )
    monkeypatch.setattr(e9, "load_zone_weights", lambda *a, **k: weights)


@pytest.mark.parametrize(
    "runtime",
    [
        ["A", "B", "C", "EXT"],  # pseudo-zone appended (extend_with_import_node)
        ["A", "EXT", "B", "C"],  # pseudo-zone in the middle
        ["C", "EXT", "A", "B", "EXT2"],  # reordered, two pseudo rows
    ],
)
def test_backcast_increment_lands_only_on_load_rows(monkeypatch, runtime):
    """Each load zone gets its weighted share on ITS runtime row; pseudo rows
    get 0; per hour the rows sum to the BA error x (1 + td_loss)."""
    err = _err()
    _patch_backcast(monkeypatch, _W, err)
    inc, _ = cd.backcast_commitment_increment(
        "TOY", 2021, _cfg_zones(_LOAD), runtime, td_loss_factor=0.05
    )
    assert inc.shape == (len(runtime), HOURS_PER_YEAR)
    for k, z in enumerate(_LOAD):
        np.testing.assert_array_equal(inc[runtime.index(z)], _W[k] * err * (1.0 + 0.05))
    for z in runtime:
        if z.startswith("EXT"):
            assert not inc[runtime.index(z)].any()
    np.testing.assert_allclose(inc.sum(axis=0), err * 1.05, rtol=1e-12, atol=1e-9)


@pytest.mark.parametrize("iso", ["ERCOT", "SPP", "NEISO"])
def test_identity_mapping_is_byte_identical_to_uc_1_7(monkeypatch, iso):
    """Where the runtime zones ARE the configured zones (ERCOT, SPP; NEISO with
    its configured zero-weight HQ_import), the increment equals the uc-1.7
    formula ``weights * err * (1 + td_loss)`` bit for bit -- the zero-weight
    configured zone included (still 0)."""
    cfg = get_iso_config(iso)
    n = len(cfg.zone_names)
    rng = np.random.default_rng(len(iso))
    w = rng.random((n, HOURS_PER_YEAR))
    if iso == "NEISO":
        w[cfg.zone_names.index("HQ_import")] = 0.0
    w = w / w.sum(axis=0, keepdims=True)
    err = _err()
    _patch_backcast(monkeypatch, w, err)
    for td in (0.0, 0.047):
        inc, _ = cd.backcast_commitment_increment(
            iso, 2021, cfg, list(cfg.zone_names), td_loss_factor=td
        )
        old = np.asarray(w, dtype=float) * err[None, :]
        if td > 0.0:
            old = old * (1.0 + td)
        assert inc.tobytes() == old.tobytes()
    if iso == "NEISO":
        assert not inc[cfg.zone_names.index("HQ_import")].any()


def test_missing_load_zone_raises(monkeypatch):
    _patch_backcast(monkeypatch, _W, _err())
    with pytest.raises(ValueError, match=r"\['B'\].*absent"):
        cd.backcast_commitment_increment(
            "TOY", 2021, _cfg_zones(_LOAD), ["A", "C", "EXT"]
        )


def test_replaced_zero_load_zone_is_admitted(monkeypatch):
    """A configured zone with no weight in any hour that the topology replaced
    (CAISO's WECC_import -> its per-hub corridors) carries nothing to map."""
    w = np.vstack([_W, np.zeros(HOURS_PER_YEAR)])
    err = _err()
    _patch_backcast(monkeypatch, w, err)
    runtime = ["A", "B", "C", "CORR_N", "CORR_S"]
    inc, _ = cd.backcast_commitment_increment(
        "TOY", 2021, _cfg_zones([*_LOAD, "IMP"]), runtime
    )
    assert not inc[3:].any()
    np.testing.assert_allclose(inc.sum(axis=0), err, rtol=1e-12, atol=1e-9)


def test_zone_list_is_required_and_consistent(monkeypatch):
    _patch_backcast(monkeypatch, _W, _err())
    with pytest.raises(ValueError, match="runtime zone list"):
        cd.load_row_index(_LOAD, None)
    with pytest.raises(ValueError, match="twice"):
        cd.load_row_index(_LOAD, ["A", "B", "C", "A"])
    bc = SimpleNamespace(
        uc_commitment_demand_source="da_forecast",
        mode="backcast",
        iso="NYISO",
        weather_year=2021,
    )
    with pytest.raises(ValueError, match="runtime zone list"):
        cd.commitment_demand(bc, np.zeros((6, 24)))
    with pytest.raises(ValueError, match="has 5 zones, demand 6"):
        cd.commitment_demand(bc, np.zeros((6, 24)), ["a", "b", "c", "d", "e"])


def test_backcast_dispatcher_on_an_appended_pseudo_zone(monkeypatch):
    """The FIX-8 defect: NYISO's runtime zones are its 5 load zones plus the
    appended NYISO_external; uc-1.7 raised "5 zones, demand 6"."""
    cfg = get_iso_config("NYISO")
    runtime = [*cfg.zone_names, "NYISO_external"]
    w = np.full((5, HOURS_PER_YEAR), 0.2)
    err = _err()
    _patch_backcast(monkeypatch, w, err)
    demand = np.full((6, 24), 1000.0)
    demand[5] = 300.0  # an export sink
    out = cd.commitment_demand(
        SimpleNamespace(
            uc_commitment_demand_source="da_forecast",
            mode="backcast",
            iso="NYISO",
            weather_year=2021,
            td_loss_factor=0.0,
        ),
        demand,
        runtime,
    )
    assert out.demand.shape == (6, 24)
    np.testing.assert_array_equal(out.demand[5], demand[5])
    np.testing.assert_allclose(
        (out.demand - demand).sum(axis=0), err[:24], rtol=1e-12, atol=1e-9
    )


@pytest.mark.parametrize("runtime", [["A", "B", "C", "EXT"], ["A", "EXT", "B", "C"]])
def test_forward_leaves_pseudo_rows_unscaled(monkeypatch, runtime):
    import market_sim.config.iso_configs as ic

    monkeypatch.setattr(ic, "get_iso_config", lambda iso: _cfg_zones(_LOAD))
    monkeypatch.setattr(
        cd,
        "load_forecast_error_profile",
        lambda iso: _profile({"DJF": 0.02, "MAM": 0.0, "JJA": 0.0, "SON": 0.0}),
    )
    demand = np.full((4, 24), 100.0)
    demand[runtime.index("EXT")] = 250.0
    out = cd.commitment_demand(
        SimpleNamespace(
            uc_commitment_demand_source="da_forecast", mode="forecast", iso="TOY"
        ),
        demand,
        runtime,
    ).demand
    np.testing.assert_array_equal(out[runtime.index("EXT")], 250.0)
    for z in _LOAD:
        np.testing.assert_allclose(out[runtime.index(z), 0], 102.0)


def test_forward_identity_is_byte_identical_and_missing_zone_raises():
    cfg = get_iso_config("ERCOT")
    assert cd.forward_load_row_mask(cfg, list(cfg.zone_names)).all()
    neiso = get_iso_config("NEISO")
    # NEISO's configured HQ_import (load_share 0) stays on the mask: the
    # forward arithmetic is the uc-1.7 ``demand * (1 + frac)`` on every row.
    assert cd.forward_load_row_mask(neiso, list(neiso.zone_names)).all()
    with pytest.raises(ValueError, match="absent"):
        cd.forward_load_row_mask(cfg, [z for z in cfg.zone_names if z != "North"])
    # A zero-share configured zone the topology replaced is admitted.
    assert cd.forward_load_row_mask(
        neiso, [z for z in neiso.zone_names if z != "HQ_import"]
    ).all()


# --------------------------------------------------------------------------- #
# Per-ISO forecast-error basis (lane UC-DA-BASIS, owner rulings R16, R17)      #
# --------------------------------------------------------------------------- #
from market_sim.config.constants import (  # noqa: E402
    SPP_DA_RUC_FORECAST_CUTOFF_HOUR_LOCAL,
    SPP_ID_RUC_CYCLE_HOURS,
    SPP_MARKET_TIMEZONE,
)
from market_sim.config.scenarios import UC_RUC_INTRADAY_FORECAST_ISOS  # noqa: E402

TZ = SPP_MARKET_TIMEZONE


def _ends(*local_starts: str) -> pd.DatetimeIndex:
    """Interval-end UTC stamps of hours beginning at the given CPT wall times."""
    starts = pd.DatetimeIndex(
        [pd.Timestamp(s).tz_localize(TZ, ambiguous=True) for s in local_starts]
    )
    return (starts + pd.Timedelta(hours=1)).tz_convert("UTC")


def _utc(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz="UTC")


def test_intraday_registry_in_step_with_the_config():
    assert cd.intraday_forecast_isos() == UC_RUC_INTRADAY_FORECAST_ISOS


def test_da_ruc_cutoff_is_13h_cpt_on_d_minus_1():
    """Trivial day (CDT, UTC-5): every hour of D shares one cutoff, D-1 13:00."""
    ends = _ends("2024-07-10 00:00", "2024-07-10 12:00", "2024-07-10 23:00")
    cut = cd.da_ruc_cutoff_utc(ends, TZ, SPP_DA_RUC_FORECAST_CUTOFF_HOUR_LOCAL)
    assert list(cut) == [_utc("2024-07-09 18:00")] * 3
    # The hour beginning at midnight belongs to D, not D-1.
    nxt = cd.da_ruc_cutoff_utc(_ends("2024-07-11 00:00"), TZ, 13)
    assert nxt[0] == _utc("2024-07-10 18:00")


@pytest.mark.parametrize(
    "start, cutoff_utc",
    [
        # Spring forward 2024-03-10 (02:00 CST -> 03:00 CDT): D = Mar 10, D-1 is
        # on CST (UTC-6); D = Mar 11's cutoff is Mar 10 13:00 CDT (UTC-5).
        ("2024-03-10 00:00", "2024-03-09 19:00"),
        ("2024-03-10 03:00", "2024-03-09 19:00"),
        ("2024-03-11 00:00", "2024-03-10 18:00"),
        # Fall back 2024-11-03 (02:00 CDT -> 01:00 CST): both 01:00 hours are
        # on D = Nov 3, cutoff Nov 2 13:00 CDT; Nov 4's is Nov 3 13:00 CST.
        ("2024-11-03 01:00", "2024-11-02 18:00"),
        ("2024-11-03 23:00", "2024-11-02 18:00"),
        ("2024-11-04 00:00", "2024-11-03 19:00"),
    ],
)
def test_da_ruc_cutoff_follows_the_wall_clock_across_dst(start, cutoff_utc):
    cut = cd.da_ruc_cutoff_utc(_ends(start), TZ, 13)
    assert cut[0] == _utc(cutoff_utc)


def test_da_ruc_cutoff_covers_both_fall_back_hours():
    """The repeated 01:00 (CDT then CST) are two operating hours of one day."""
    first = pd.Timestamp("2024-11-03 06:00", tz="UTC")  # 01:00 CDT
    ends = pd.DatetimeIndex([first, first + pd.Timedelta(hours=1)]) + pd.Timedelta(
        hours=1
    )
    cut = cd.da_ruc_cutoff_utc(ends, TZ, 13)
    assert list(cut) == [_utc("2024-11-02 18:00")] * 2


def _vintages(issues: list[str], ends: pd.DatetimeIndex, mw_of_issue) -> pd.DataFrame:
    rows = [
        dict(
            area="SPP",
            issue_time_utc=_utc(i),
            interval_end_utc=e,
            forecast_mw=float(mw_of_issue(_utc(i))),
        )
        for i in issues
        for e in ends
    ]
    return pd.DataFrame(rows)


def test_vintage_in_force_boundary_is_inclusive_at_13h():
    """Issued exactly at the cutoff counts; one hour later does not; with the
    13:00 vintage unpublished the 12:00 one is in force; none -> NaN."""
    ends = _ends("2024-07-10 05:00")
    cut = cd.da_ruc_cutoff_utc(ends, TZ, 13)  # 2024-07-09 18:00 UTC
    mw = {"2024-07-09 17:00": 1.0, "2024-07-09 18:00": 2.0, "2024-07-09 19:00": 3.0}
    v = _vintages(list(mw), ends, lambda t: mw[t.strftime("%Y-%m-%d %H:%M")])
    assert cd.vintage_in_force(v, ends, cut)[0] == 2.0
    v12 = v[v.issue_time_utc != _utc("2024-07-09 18:00")]
    assert cd.vintage_in_force(v12, ends, cut)[0] == 1.0
    late = v[v.issue_time_utc == _utc("2024-07-09 19:00")]
    assert np.isnan(cd.vintage_in_force(late, ends, cut)[0])


def test_cycle_cutoff_trivial_cases():
    """4-h grid from 00:00 CPT; the cycle at least one cycle before the start."""
    ends = _ends("2024-07-10 10:00", "2024-07-10 08:00", "2024-07-10 07:00")
    cut = cd.cycle_cutoff_utc(ends, TZ, SPP_ID_RUC_CYCLE_HOURS)
    wall = cut.tz_convert(TZ).tz_localize(None)
    assert list(wall.strftime("%H:%M")) == ["04:00", "04:00", "00:00"]
    with pytest.raises(ValueError, match="divide 24"):
        cd.cycle_cutoff_utc(ends, TZ, 5)


def test_cycle_cutoff_is_on_the_grid_and_a_full_cycle_ahead_all_year():
    """Every hour of 2024 incl. both DST days: the cutoff is a grid point of
    the local wall clock, at least one cycle before the hour's start and less
    than two cycles plus the DST hour before it."""
    starts = pd.date_range("2024-01-01 06:00", "2025-01-01 05:00", freq="h", tz="UTC")
    ends = starts + pd.Timedelta(hours=1)
    cut = cd.cycle_cutoff_utc(ends, TZ, 4)
    wall = cut.tz_convert(TZ)
    assert (wall.minute == 0).all() and (wall.hour % 4 == 0).all()
    lead = (starts - cut) / pd.Timedelta(hours=1)
    assert lead.min() >= 4 and lead.max() <= 8


def test_spp_reads_the_mtlf_at_the_da_ruc_never_the_eia_df(monkeypatch):
    """SPP's DA forecast is the MTLF vintage in force at 13:00 CPT D-1 on the
    frame's hour-end UTC stamps; the EIA DF column is not read."""
    disable_stale_snapshot_repair_mp(monkeypatch)  # synthetic frame
    import market_sim.data.eia930 as e9
    from market_sim.data import load_forecast_vintages as lfv

    ends = _ends("2024-07-10 00:00", "2024-07-10 01:00", "2024-07-10 02:00")
    frame = pd.DataFrame(
        {
            "UTC time": ends.tz_convert("UTC").tz_localize(None),
            "Demand": [1000.0, 1000.0, 1000.0],
            "Demand forecast": [9e9, 9e9, 9e9],
        }
    )
    v = _vintages(
        ["2024-07-09 17:00", "2024-07-09 18:00", "2024-07-09 22:00"],
        ends,
        lambda t: 1000.0 + t.hour,  # 1017 / 1018 / 1022
    )
    monkeypatch.setattr(e9, "_eia_hourly_frame_filled", lambda ba, year: frame)
    monkeypatch.setattr(lfv, "available_years", lambda iso: [2023, 2024])
    monkeypatch.setattr(lfv, "load_vintages", lambda iso, years, area=None: v)
    err, dropped = cd.ba_forecast_error_mw("SPP", 2024)
    assert dropped == 0 and err.tolist() == [18.0, 18.0, 18.0]
    fc, act = cd.forecast_and_actual_mw("SPP", 2024)
    assert fc.tolist() == [1018.0] * 3 and act.tolist() == [1000.0] * 3
    # Intraday: the cycle at least 4 h before 00:00 / 01:00 / 02:00 CDT is
    # 20:00 CDT D-1 (01:00 UTC): the 22:00 UTC vintage is in force.
    err_id, _ = cd.ba_forecast_error_mw("SPP", 2024, horizon="intraday")
    assert err_id.tolist() == [22.0, 22.0, 22.0]


def test_spp_missing_vintage_partition_raises(monkeypatch):
    disable_stale_snapshot_repair_mp(monkeypatch)  # synthetic frame
    import market_sim.data.eia930 as e9
    from market_sim.data import load_forecast_vintages as lfv

    frame = pd.DataFrame(
        {
            "UTC time": pd.date_range("2024-07-10 06:00", periods=3, freq="h"),
            "Demand": [1000.0] * 3,
            "Demand forecast": [1010.0] * 3,
        }
    )
    monkeypatch.setattr(e9, "_eia_hourly_frame_filled", lambda ba, year: frame)
    monkeypatch.setattr(lfv, "available_years", lambda iso: [2023])
    with pytest.raises(cd.MissingForecastVintages, match="no EIA-930 fallback"):
        cd.ba_forecast_error_mw("SPP", 2024)
    with pytest.raises(cd.MissingForecastVintages):
        cd.ba_forecast_error_mw("SPP", 2024, horizon="intraday")


def test_caiso_actual_is_net_of_battery_charging(monkeypatch):
    """err = DF - (Demand - max(-NG: OTH, 0)); discharge and unreported hours
    net nothing. The DF itself is the EIA-930 CISO column."""
    import market_sim.data.eia930 as e9

    frame = pd.DataFrame(
        {
            "Demand": [20000.0, 20000.0, 20000.0, 20000.0],
            "Demand forecast": [19500.0, 19500.0, 19500.0, 19500.0],
            "NG: OTH": [-500.0, 300.0, np.nan, 0.0],
        }
    )
    monkeypatch.setattr(e9, "_eia_hourly_frame_filled", lambda ba, year: frame)
    np.testing.assert_array_equal(cd.storage_charging_mw(frame), [500.0, 0, 0, 0])
    err, dropped = cd.ba_forecast_error_mw("CAISO", 2024)
    assert dropped == 0
    np.testing.assert_array_equal(err, [0.0, -500.0, -500.0, -500.0])
    assert cd.forecast_error_basis("CAISO").label == (
        "eia930_da_forecast_net_storage_charging"
    )
    with pytest.raises(ValueError, match="NG: OTH"):
        cd.storage_charging_mw(frame.drop(columns="NG: OTH"))
    with pytest.raises(ValueError, match="no measured intraday"):
        cd.ba_forecast_error_mw("CAISO", 2024, horizon="intraday")


@pytest.mark.parametrize(
    "iso", ["ERCOT", "MISO", "NEISO", "NYISO", "PJM", "SOCO", "NWPP"]
)
def test_other_isos_keep_the_eia930_basis_bit_for_bit(monkeypatch, iso):
    """INERT outside SPP / CAISO: DF - Demand off the raw columns, as uc-1.9."""
    import market_sim.data.eia930 as e9

    rng = np.random.default_rng(3)
    dem = rng.uniform(1e4, 2e4, 48)
    df = dem * rng.uniform(0.95, 1.05, 48)
    frame = pd.DataFrame(
        {"Demand": dem, "Demand forecast": df, "NG: OTH": -np.ones(48) * 1e3}
    )
    monkeypatch.setattr(e9, "_eia_hourly_frame_filled", lambda ba, year: frame)
    assert cd.forecast_error_basis(iso) is cd.EIA930_BASIS
    err, dropped = cd.ba_forecast_error_mw(iso, 2023)
    old, valid = cd.qa_forecast_error(df, dem)
    assert dropped == int((~valid).sum()) and err.tobytes() == old.tobytes()


def test_dispatcher_labels_the_basis(monkeypatch):
    monkeypatch.setattr(
        cd,
        "backcast_commitment_increment",
        lambda *a, **k: (np.zeros((len(a[3]), HOURS_PER_YEAR)), 0),
    )
    cfg = get_iso_config("SPP")
    out = cd.commitment_demand(
        SimpleNamespace(
            uc_commitment_demand_source="da_forecast",
            mode="backcast",
            iso="SPP",
            weather_year=2024,
        ),
        np.zeros((len(cfg.zone_names), 24)),
        list(cfg.zone_names),
    )
    assert out.basis == "spp_mtlf_da_ruc"


def test_intraday_commitment_demand_maps_like_the_da_increment(monkeypatch):
    seen = {}

    def fake(
        iso, year, iso_config, zone_names, td_loss_factor=0.0, horizon="day_ahead"
    ):
        seen.update(iso=iso, year=year, horizon=horizon, td=td_loss_factor)
        return np.full((len(zone_names), HOURS_PER_YEAR), 5.0), 0

    monkeypatch.setattr(cd, "backcast_commitment_increment", fake)
    zones = list(get_iso_config("SPP").zone_names)
    demand = np.full((len(zones), 24), 100.0)
    cfg = SimpleNamespace(
        iso="SPP", mode="backcast", weather_year=2024, td_loss_factor=0.03
    )
    out = cd.intraday_commitment_demand(cfg, demand, zones)
    np.testing.assert_array_equal(out, demand + 5.0)
    assert seen == dict(iso="SPP", year=2024, horizon="intraday", td=0.03)
    with pytest.raises(ValueError, match="no measured intraday"):
        cd.intraday_commitment_demand(
            SimpleNamespace(iso="NEISO", mode="backcast", weather_year=2024),
            demand,
            zones,
        )
    with pytest.raises(ValueError, match="backcast only"):
        cd.intraday_commitment_demand(
            SimpleNamespace(iso="SPP", mode="forecast", weather_year=2024),
            demand,
            zones,
        )
    with pytest.raises(ValueError, match="runtime zone list"):
        cd.intraday_commitment_demand(cfg, demand, None)
