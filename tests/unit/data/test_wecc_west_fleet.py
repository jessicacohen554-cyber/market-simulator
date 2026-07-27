"""Tests for the endogenous WECC-West neighbor fleet (caiso-110)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from market_sim.data.wecc_west_fleet import (
    WECC_WEST_ZONE,
    build_wecc_west_fleet,
    build_wecc_west_thermal_mc,
    is_wecc_west_unit,
    west_delivered_hub_blend,
)

pytestmark = pytest.mark.skipif(
    not Path("data/clean/wecc-west-supply").exists(),
    reason="wecc-west-supply clean frame not built",
)


def test_build_shape_and_labels():
    gens, avail, demand = build_wecc_west_fleet(2024, henry_hub_price=2.2)
    # 7 aggregated units (solar/wind/hydro/nuclear/coal/gas_cc/gas_ct).
    assert len(gens) == 7
    for g in gens:
        assert g.zone == WECC_WEST_ZONE
        assert g.fuel_type == "import"  # keeps the West out of CAISO gates
        assert g.heat_rate == 0.0
        assert g.emission_rate_co2 == 0.0  # West CO2 not in CAISO inventory
        assert g.vom >= 0.0
        assert is_wecc_west_unit(g.unit_id)
    # demand is a full-year hourly series, all finite, positive.
    assert demand.shape == (8760,)
    assert np.isfinite(demand).all()
    assert demand.min() > 0.0
    assert 40_000 < demand.mean() < 70_000  # ~54-57 GW West load


def test_merit_order_prices():
    gens, _avail, _d = build_wecc_west_fleet(2024, henry_hub_price=2.2)
    mc = {g.unit_id: g.vom for g in gens}
    # VRE free, hydro cheap, nuclear cheap, thermal costs positive.
    assert mc["WECCW_solar"] == 0.0
    assert mc["WECCW_wind"] == 0.0
    assert 0 < mc["WECCW_hydro"] < mc["WECCW_nuclear"] < mc["WECCW_coal"]
    # gas MC tracks the hub: gas_ct (higher HR) > gas_cc.
    assert mc["WECCW_gas_ct"] > mc["WECCW_gas_cc"] > 0.0


def test_availability_shaped_to_measured():
    gens, avail, _d = build_wecc_west_fleet(2024, henry_hub_price=2.2)
    # Shaped units present with (8760,) availability in [0, 1]; thermal absent.
    for uid in ("WECCW_solar", "WECCW_wind", "WECCW_hydro", "WECCW_nuclear"):
        a = avail[uid]
        assert a.shape == (8760,)
        assert (a >= 0.0).all() and (a <= 1.0).all()
    for uid in ("WECCW_coal", "WECCW_gas_cc", "WECCW_gas_ct"):
        assert uid not in avail  # dispatchable to nameplate (flat 1.0)
    # solar peaks midday, ~0 overnight (belly > overnight mean CF).
    sol = avail["WECCW_solar"]
    hod = np.arange(8760) % 24
    assert sol[np.isin(hod, [11, 12, 13])].mean() > sol[np.isin(hod, [0, 1, 2])].mean()


def test_supply_covers_demand_every_hour():
    # Per-hour available supply (shaped units at measured output + thermal at
    # nameplate) must cover West demand in EVERY hour, so the West zone never
    # hits VOLL slack (the tie import to CA is then pure export headroom, not a
    # feasibility crutch).
    gens, avail, demand = build_wecc_west_fleet(2024, henry_hub_price=2.2)
    supply = np.zeros(8760)
    for g in gens:
        a = avail.get(g.unit_id)
        supply += g.pmax_mw * (a if a is not None else 1.0)
    assert (supply >= demand).all(), (
        f"West infeasible in {(supply < demand).sum()} hours "
        f"(worst shortfall {(demand - supply).max():.0f} MW)"
    )


# --- caiso-114: measured-hub West-thermal re-pricing (THE caiso-110 fix) ---


def test_hub_blend_shape_and_finite():
    # The tie-weighted delivered West hub is a full-year finite series (the
    # 2023 Jan-Feb OASIS gap is reference-filled inside measured_import_hub_prices).
    blend = west_delivered_hub_blend(2024, 8760)
    assert blend is not None
    assert blend.shape == (8760,)
    assert np.isfinite(blend).all()
    # Mean sits in the measured desert-SW / PNW blended range (~$30-45), well
    # ABOVE bare Henry-Hub gas MC (~$18-20) — the whole point of the re-pricing.
    assert 20.0 < np.mean(blend) < 60.0


def test_thermal_mc_reprices_gas_above_henry_hub():
    # The override raises the West GAS units well above their bare Henry-Hub vom
    # (the flood fix): mean gas_cc offer clears the diagnostic's ~$30-56 target.
    hh = 2.5
    mc = build_wecc_west_thermal_mc(2024, hh, 8760)
    assert set(mc) == {"WECCW_gas_cc", "WECCW_gas_ct"}  # coal NOT overridden
    cc, ct = mc["WECCW_gas_cc"], mc["WECCW_gas_ct"]
    assert cc.shape == (8760,) and ct.shape == (8760,)
    assert np.isfinite(cc).all() and np.isfinite(ct).all()
    # gas_ct (higher HR) stays above gas_cc every hour (physical merit premium).
    assert (ct >= cc).all()
    # Mean gas_cc offer (the measured hub) is materially above the bare Henry-Hub
    # gas_cc MC — the whole point of the re-pricing (the flood fix).
    from market_sim.data.wecc_west_fleet import _thermal_mc

    assert np.mean(cc) > _thermal_mc("gas_cc", hh) + 10.0
    # Hour-varying (belly low, evening/scarcity high) — not a flat scalar.
    assert np.std(cc) > 5.0


def test_thermal_mc_empty_when_hub_missing():
    # A year with no measured intertie parquet -> empty dict (caller keeps vom).
    assert build_wecc_west_thermal_mc(1999, 2.5, 8760) == {}
