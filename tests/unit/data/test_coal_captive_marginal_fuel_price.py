"""NWPP-NEXT-15: captive-mine marginal coal price (``coal_captive_marginal_fuel_price``).

Pinned, on trivial synthetic fixtures (no LP, no on-disk data):

* the PHASE0 §1 captive classifier (TC/TR in-state contract = captive; rail =
  non-captive; spot = non-captive; out-of-state conveyor = non-captive);
* default-off byte-identity of the fuel-price array;
* armed, only the ECON / PEAKING rows of a MIXED plant move, to the plant-month
  non-captive price (the year's when a month has none with a cost), while its
  must-run / committed rows keep the host seam's blend;
* a 100 %-captive, a 100 %-non-captive and an all-withheld mixed plant are
  untouched;
* forecast mode is a no-op, and a year with no Page 5 file is left untouched
  and logged.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import fuel
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fuel import apply_plant_monthly_fuel_prices
from market_sim.data.fuel import captive_coal

ZONES = ["Z"]
HOURS = 24 * 90  # Jan + Feb + Mar (non-leap)
YEAR = 2023
BLEND = 3.5
MIXED, CAPTIVE_ONLY, NONCAPTIVE_ONLY, WITHHELD = 101, 102, 103, 104
TRANCHES = ("mustrun", "committed", "econlo", "econhi", "peak")


def _lot(pid, st, mine_st, mode, ptype, month, qty, cost):
    """One Page 5 lot row (verbatim EIA column names)."""
    return {
        "YEAR": YEAR,
        "MONTH": month,
        "Plant Id": pid,
        "Plant State": st,
        "Purchase Type": ptype,
        "Coalmine State": mine_st,
        "Primary Transportation Mode": mode,
        "QUANTITY": qty,
        "Average Heat Content": 20.0,
        "FUEL_COST": cost,
    }


def _receipts() -> pd.DataFrame:
    rows = []
    for m in (1, 2, 3):
        rows.append(_lot(MIXED, "WY", "WY", "TC", "C", m, 1000, 400))
        rows.append(_lot(CAPTIVE_ONLY, "UT", "UT", "TR", "C", m, 1000, 200))
        rows.append(_lot(NONCAPTIVE_ONLY, "MT", "WY", "RR", "C", m, 1000, 250))
        rows.append(_lot(WITHHELD, "MT", "MT", "TR", "C", m, 1000, 300))
        rows.append(_lot(WITHHELD, "MT", "WY", "RR", "C", m, 500, "."))
    # MIXED non-captive: Jan 2.50, Feb 3.00, Mar withheld -> year's 2.75.
    rows.append(_lot(MIXED, "WY", "WY", "RR", "C", 1, 500, 250))
    rows.append(_lot(MIXED, "WY", "WY", "RR", "C", 2, 500, 300))
    rows.append(_lot(MIXED, "WY", "WY", "RR", "C", 3, 500, "."))
    return pd.DataFrame(rows)


def _legacy_costs(year: int = YEAR) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "year": year,
                "month": m,
                "plant_id": p,
                "fuel_group": "Coal",
                "price_per_mmbtu": BLEND,
                "quantity": 1.0,
            }
            for p in (MIXED, CAPTIVE_ONLY, NONCAPTIVE_ONLY, WITHHELD)
            for m in (1, 2, 3)
        ]
    )


@pytest.fixture
def page5(tmp_path, monkeypatch):
    """A tmp raw coal-receipts dir holding a synthetic YEAR file."""
    _receipts().to_csv(tmp_path / f"coal_receipts_{YEAR}.csv", index=False)
    monkeypatch.setattr(captive_coal, "COAL_RECEIPTS_RAW_DIR", tmp_path)
    captive_coal._RECEIPTS_CACHE.clear()
    monkeypatch.setattr(fuel, "_load_monthly_cache", lambda _p: _legacy_costs())
    yield tmp_path
    captive_coal._RECEIPTS_CACHE.clear()


def _fleet():
    gens = [
        Generator(
            unit_id=f"COAL_Z_p{p}_{t}",
            name=f"p{p} {t}",
            zone="Z",
            fuel_type="coal",
            plant_group="COAL_BIT",
            pmax_mw=100.0,
            heat_rate=10.0,
            plant_code=p,
        )
        for p in (MIXED, CAPTIVE_ONLY, NONCAPTIVE_ONLY, WITHHELD)
        for t in TRANCHES
    ]
    return generators_to_fleet_arrays(gens, ZONES, hours=HOURS)


def _run(mode: str = "backcast", armed: bool | None = True, year: int = YEAR):
    fleet = _fleet()
    kw = {} if armed is None else {"coal_captive_marginal_fuel_price": armed}
    cfg = ScenarioConfig(iso="NWPP", mode=mode, hours=HOURS, **kw)
    fp = np.full((fleet.n_gen, HOURS), 9.0)
    apply_plant_monthly_fuel_prices(fp, fleet, cfg, year)
    return fleet, fp


def _row(fleet, p, t):
    return fleet.unit_ids.index(f"COAL_Z_p{p}_{t}")


def test_field_defaults_off():
    assert ScenarioConfig().coal_captive_marginal_fuel_price is False


def test_classifier_phase0_rule():
    df = pd.DataFrame(
        [
            _lot(1, "WY", "WY", "TC", "C", 1, 1, 1),  # conveyor, in-state contract
            _lot(1, "WY", "WY", "TR", "NC", 1, 1, 1),  # truck, in-state new contract
            _lot(1, "WY", "WY", "RR", "C", 1, 1, 1),  # rail
            _lot(1, "WY", "WY", "TR", "S", 1, 1, 1),  # spot
            _lot(1, "WY", "MT", "TC", "C", 1, 1, 1),  # out-of-state
        ]
    )
    assert captive_coal.classify_captive(df).tolist() == [
        True,
        True,
        False,
        False,
        False,
    ]


def test_plant_prices_shares_and_withheld_rows():
    info = captive_coal.captive_plant_prices(_receipts())
    m = info[MIXED]
    # withheld March non-captive lot counts toward the share
    assert m.captive_share == pytest.approx(3000 / 4500)
    assert m.annual_noncaptive == pytest.approx(2.75)
    np.testing.assert_allclose(m.month_prices()[:3], [2.50, 3.00, 2.75])
    assert info[CAPTIVE_ONLY].captive_share == 1.0
    assert info[NONCAPTIVE_ONLY].captive_share == 0.0
    assert info[WITHHELD].mixed and info[WITHHELD].month_prices() is None


def test_default_off_is_byte_identical(page5):
    _, fp_default = _run(armed=None)
    _, fp_off = _run(armed=False)
    _, fp_on = _run(armed=True)
    np.testing.assert_array_equal(fp_default, fp_off)
    assert (fp_on != fp_off).any()  # the fixture does reach the mechanism


def test_armed_moves_only_econ_and_peak_of_mixed_plant(page5):
    fleet, fp = _run(armed=True)
    jan, feb, mar = slice(0, 31 * 24), slice(31 * 24, 59 * 24), slice(59 * 24, HOURS)
    for t in ("econlo", "econhi", "peak"):
        g = _row(fleet, MIXED, t)
        assert np.all(fp[g, jan] == pytest.approx(2.50))
        assert np.all(fp[g, feb] == pytest.approx(3.00))
        assert np.all(fp[g, mar] == pytest.approx(2.75))
    for t in ("mustrun", "committed"):
        assert np.all(fp[_row(fleet, MIXED, t)] == BLEND)


@pytest.mark.parametrize("plant", [CAPTIVE_ONLY, NONCAPTIVE_ONLY, WITHHELD])
def test_single_source_and_withheld_plants_untouched(page5, plant):
    fleet, fp = _run(armed=True)
    for t in TRANCHES:
        assert np.all(fp[_row(fleet, plant, t)] == BLEND)


def test_forecast_mode_is_noop(page5):
    fleet = _fleet()
    cfg = ScenarioConfig(
        iso="NWPP", mode="forecast", hours=HOURS, coal_captive_marginal_fuel_price=True
    )
    fp = np.full((fleet.n_gen, HOURS), 9.0)
    apply_plant_monthly_fuel_prices(fp, fleet, cfg, YEAR)
    assert np.all(fp == 9.0)


def test_year_without_page5_file_untouched_and_logged(page5, monkeypatch, caplog):
    monkeypatch.setattr(fuel, "_load_monthly_cache", lambda _p: _legacy_costs(2025))
    with caplog.at_level(logging.INFO, logger="market_sim.data.fuel"):
        _, fp_on = _run(armed=True, year=2025)
    _, fp_off = _run(armed=False, year=2025)
    np.testing.assert_array_equal(fp_on, fp_off)
    assert any("no EIA-923 Page 5" in r.getMessage() for r in caplog.records)
