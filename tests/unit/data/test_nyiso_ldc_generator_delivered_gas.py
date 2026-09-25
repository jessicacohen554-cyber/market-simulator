"""NYISO-STGAS-2023: ``nyiso_ldc_generator_delivered_gas`` — the LDC delivery leg.

Trivial cases first (CLAUDE.md Testing Pattern): a small fleet, a tmp EIA-860
plant file and a tmp filed-rate table. Checks that the flag is byte-inert off
and on another ISO; that every non-CT_PEAKER gas row at a plant EIA-860 records
as served by an intaken LDC moves by hub x loss + transport; that CT_PEAKER rows,
a pipeline-connected plant, an LDC without an intaken class and a plant below
the class's filed size threshold are untouched; and that a partial or missing
year raises rather than filling.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fuel.basis import nyiso as nyiso_basis

_ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
_HOURS = 8760
_CONED = "CONSOLIDATED EDISON NEW YORK INC"


def _gen(uid, zone, fuel, mw, group, code):
    return Generator(
        unit_id=uid,
        name=uid,
        zone=zone,
        fuel_type=fuel,
        pmax_mw=mw,
        plant_group=group,
        plant_code=code,
    )


def _fleet():
    """Con Ed steam + CC + CT at one site, a small Con Ed plant, and non-Con Ed plants."""
    gens = [
        _gen("ST_CONED", "NYC", "gas_st", 300.0, "ST_GAS", 2500),
        _gen("CC_CONED", "NYC", "gas_cc", 250.0, "CC_REGULAR", 2500),
        _gen("CT_CONED", "NYC", "gas_ct", 50.0, "CT_PEAKER", 2500),
        _gen("ST_SMALL", "NYC", "gas_st", 30.0, "ST_GAS", 7777),
        _gen("ST_CHUD", "Capital_Hudson", "gas_st", 300.0, "ST_GAS", 8006),
        _gen("ST_PIPE", "Long_Island", "gas_st", 300.0, "ST_GAS", 2516),
    ]
    return generators_to_fleet_arrays(gens, _ZONES, hours=_HOURS)


@pytest.fixture()
def tmp_inputs(tmp_path, monkeypatch):
    """Point the mechanism at a tmp EIA-860 plant file and a tmp rate table."""
    eia = tmp_path / "eia860"
    eia.mkdir()
    pd.DataFrame(
        {
            "Plant Code": [2500, 7777, 8006, 2516],
            "Natural Gas LDC Name": [
                _CONED,
                _CONED,
                "CENTRAL HUDSON GAS ELECTRIC",
                None,
            ],
        }
    ).to_parquet(eia / "eia860_plant.parquet")
    import market_sim.config.paths as paths

    monkeypatch.setattr(paths, "active_eia860_dir", lambda: eia)
    rates = tmp_path / "rates.csv"
    rows = [
        {
            "ldc_eia860_name": _CONED,
            "year": 2023,
            "month": m,
            "transport_usd_per_mmbtu": 0.20 if m < 7 else 0.30,
            "loss_factor": 1.005,
            "min_plant_mw": 50,
        }
        for m in range(1, 13)
    ] + [
        {
            "ldc_eia860_name": _CONED,
            "year": 2024,
            "month": m,
            "transport_usd_per_mmbtu": 0.20,
            "loss_factor": 1.005,
            "min_plant_mw": 50,
        }
        for m in range(1, 7)
    ]
    pd.DataFrame(rows).to_csv(rates, index=False)
    monkeypatch.setattr(nyiso_basis, "NYISO_LDC_GENERATOR_TRANSPORT_PATH", rates)
    return rates


def _armed(iso="NYISO"):
    return ScenarioConfig(iso=iso, hours=_HOURS).with_overrides(
        nyiso_ldc_generator_delivered_gas=True
    )


def test_off_is_byte_inert(tmp_inputs):
    """Flag off (the default) leaves every fuel price untouched."""
    fleet = _fleet()
    base = np.full((fleet.n_gen, _HOURS), 2.0)
    out = base.copy()
    nyiso_basis.apply_nyiso_ldc_generator_delivered_gas(
        out, fleet, ScenarioConfig(iso="NYISO", hours=_HOURS), 2023
    )
    np.testing.assert_array_equal(out, base)


def test_ldc_served_generators_move_and_nothing_else(tmp_inputs):
    """Con Ed ST + CC: hub x 1.005 + monthly rate; CT, small, non-Con Ed untouched."""
    fleet = _fleet()
    base = np.full((fleet.n_gen, _HOURS), 2.0)
    out = base.copy()
    nyiso_basis.apply_nyiso_ldc_generator_delivered_gas(out, fleet, _armed(), 2023)
    for uid in ("ST_CONED", "CC_CONED"):
        i = fleet.unit_ids.index(uid)
        assert out[i, 5] == pytest.approx(2.0 * 1.005 + 0.20)  # January
        assert out[i, 24 * 200] == pytest.approx(2.0 * 1.005 + 0.30)  # July
    for uid in ("CT_CONED", "ST_SMALL", "ST_CHUD", "ST_PIPE"):
        i = fleet.unit_ids.index(uid)
        np.testing.assert_array_equal(out[i], base[i])


def test_other_iso_is_inert(tmp_inputs):
    """The mechanism is NYISO-scoped."""
    fleet = _fleet()
    base = np.full((fleet.n_gen, _HOURS), 2.0)
    out = base.copy()
    nyiso_basis.apply_nyiso_ldc_generator_delivered_gas(
        out, fleet, _armed("NEISO"), 2023
    )
    np.testing.assert_array_equal(out, base)


def test_partial_year_raises(tmp_inputs):
    """An intaken LDC with only part of the year is refused, never filled."""
    fleet = _fleet()
    out = np.full((fleet.n_gen, _HOURS), 2.0)
    with pytest.raises(nyiso_basis.LdcGeneratorTransportDataError):
        nyiso_basis.apply_nyiso_ldc_generator_delivered_gas(out, fleet, _armed(), 2024)


def test_missing_year_for_served_ldc_raises(tmp_inputs):
    """An intaken LDC serving a model plant with no rows for the year raises."""
    fleet = _fleet()
    out = np.full((fleet.n_gen, _HOURS), 2.0)
    with pytest.raises(nyiso_basis.LdcGeneratorTransportDataError):
        nyiso_basis.apply_nyiso_ldc_generator_delivered_gas(out, fleet, _armed(), 2019)


def test_committed_table_is_complete_2021_2025():
    """The committed Con Ed D(2) table covers every month 2021-2025 at the filed values."""
    for year in range(2021, 2026):
        legs = nyiso_basis.ldc_generator_transport_monthly(year)
        loss, rate, min_mw = legs[_CONED]
        np.testing.assert_allclose(rate, 0.192)
        np.testing.assert_allclose(loss, 1.005)
        assert min_mw == 50
