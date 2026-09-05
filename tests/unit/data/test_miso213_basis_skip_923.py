"""miso-213: the MISO zonal basis skips print-derived cells under its scope flag.

Rule 19 ``[R-ONE-MECH]``: a gas cell whose delivered price the EIA-923 print
path SET already embeds the regional delivered premium, so the mean-zero zonal
increment must not be layered on top of it. Pinned here:

* ``apply_plant_monthly_fuel_prices`` returns the ``(n_gen, T)`` written-cell
  mask (all-False when the overlay is a no-op);
* with ``miso_zonal_gas_basis_skip_923_priced`` ON, masked cells are left
  byte-untouched and unmasked cells receive EXACTLY the spread they receive
  with the flag off (the capacity-weighted mean is still over ALL gas rows);
* with the flag OFF a passed mask is ignored (byte-identical to HEAD);
* ``resolve_fuel_prices`` threads the mask to the MISO applier only under the
  flag, and never to another ISO's applier.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import fuel
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fuel import (
    apply_miso_zonal_gas_basis,
    apply_plant_monthly_fuel_prices,
    miso_zonal_gas_basis_by_zone,
    resolve_fuel_prices,
)

# Must mirror the real six-zone config order (the applier maps basis through
# get_iso_config("MISO").zone_names positions).
_MISO_ZONES = [
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
]
HOURS = 48


def _fleet(hours: int = HOURS):
    gens = [
        Generator(
            unit_id=f"GAS_{z.split('-')[1].upper()}",
            name=f"{z} CC",
            zone=z,
            fuel_type="gas_cc",
            pmax_mw=400.0,
        )
        for z in ("MISO-West", "MISO-Illinois", "MISO-South")
    ]
    return generators_to_fleet_arrays(gens, _MISO_ZONES, hours=hours)


def _idx(fleet, uid: str) -> int:
    return fleet.unit_ids.index(uid)


def test_basis_rows_exist_for_2025():
    assert miso_zonal_gas_basis_by_zone(2025) is not None


def test_skip_mask_leaves_masked_cells_untouched_and_keeps_spread_elsewhere():
    fleet = _fleet()
    base = np.full((fleet.n_gen, HOURS), 3.0)
    on_cfg = ScenarioConfig(iso="MISO", hours=HOURS, miso_zonal_gas_basis=True)
    on = base.copy()
    apply_miso_zonal_gas_basis(on, fleet, on_cfg, 2025)
    south, west, ill = (
        _idx(fleet, u) for u in ("GAS_SOUTH", "GAS_WEST", "GAS_ILLINOIS")
    )
    assert not np.allclose(on[south], base[south])  # the basis is live

    # A "print-derived" South cell set: first half of the hours.
    mask = np.zeros((fleet.n_gen, HOURS), dtype=bool)
    mask[south, : HOURS // 2] = True
    arm_cfg = on_cfg.with_overrides(miso_zonal_gas_basis_skip_923_priced=True)
    arm = base.copy()
    apply_miso_zonal_gas_basis(arm, fleet, arm_cfg, 2025, skip_cells=mask)
    # masked cells: byte-untouched (the print IS the delivered price)
    np.testing.assert_array_equal(arm[south, : HOURS // 2], base[south, : HOURS // 2])
    # unmasked South cells and the other zones: exactly the flag-off spread —
    # the capacity-weighted mean is still taken over ALL gas rows
    np.testing.assert_array_equal(arm[south, HOURS // 2 :], on[south, HOURS // 2 :])
    np.testing.assert_array_equal(arm[west], on[west])
    np.testing.assert_array_equal(arm[ill], on[ill])


def test_flag_off_ignores_a_passed_mask():
    fleet = _fleet()
    base = np.full((fleet.n_gen, HOURS), 3.0)
    cfg = ScenarioConfig(iso="MISO", hours=HOURS, miso_zonal_gas_basis=True)
    on = base.copy()
    apply_miso_zonal_gas_basis(on, fleet, cfg, 2025)
    with_mask = base.copy()
    apply_miso_zonal_gas_basis(
        with_mask, fleet, cfg, 2025, skip_cells=np.ones_like(base, dtype=bool)
    )
    np.testing.assert_array_equal(with_mask, on)


def test_all_true_mask_under_the_flag_is_a_noop():
    fleet = _fleet()
    base = np.full((fleet.n_gen, HOURS), 3.0)
    cfg = ScenarioConfig(
        iso="MISO",
        hours=HOURS,
        miso_zonal_gas_basis=True,
        miso_zonal_gas_basis_skip_923_priced=True,
    )
    arm = base.copy()
    apply_miso_zonal_gas_basis(
        arm, fleet, cfg, 2025, skip_cells=np.ones_like(base, dtype=bool)
    )
    np.testing.assert_array_equal(arm, base)


def test_plant_monthly_overlay_returns_all_false_mask_when_it_is_a_noop():
    fleet = _fleet()
    cfg = ScenarioConfig(iso="MISO", hours=HOURS, mode="backcast")
    prices = np.full((fleet.n_gen, HOURS), 2.5)
    before = prices.copy()
    written = apply_plant_monthly_fuel_prices(prices, fleet, cfg, year=2099)
    assert written.dtype == bool and written.shape == (fleet.n_gen, HOURS)
    assert not written.any()
    np.testing.assert_array_equal(prices, before)
    # forecast mode: the overlay is gated off before any table is read
    fc = ScenarioConfig(iso="MISO", hours=HOURS, mode="forecast")
    written_fc = apply_plant_monthly_fuel_prices(prices, fleet, fc, year=2025)
    assert written_fc.shape == (fleet.n_gen, HOURS) and not written_fc.any()


def _seam(monkeypatch, cfg):
    """Run resolve_fuel_prices with a crafted print mask and a recording MISO applier."""
    fleet = _fleet()
    crafted = np.zeros((fleet.n_gen, HOURS), dtype=bool)
    crafted[_idx(fleet, "GAS_SOUTH"), :] = True
    seen: dict = {}

    def fake_overlay(fuel_prices, fleet_, config, year):
        return crafted

    def recorder(fuel_prices, fleet_, config, year, **kw):
        seen["kw"] = kw

    monkeypatch.setattr(
        "market_sim.data.fuel.resolve.apply_plant_monthly_fuel_prices", fake_overlay
    )
    monkeypatch.setitem(fuel.ZONAL_BASIS_APPLIERS, "MISO", recorder)
    resolve_fuel_prices(cfg, fleet, 2025)
    return crafted, seen


def test_resolve_threads_the_mask_to_the_miso_applier_only_under_the_flag(monkeypatch):
    armed = ScenarioConfig(
        iso="MISO",
        hours=HOURS,
        mode="backcast",
        miso_zonal_gas_basis=True,
        miso_zonal_gas_basis_skip_923_priced=True,
    )
    crafted, seen = _seam(monkeypatch, armed)
    assert seen["kw"]["skip_cells"] is crafted

    off = armed.with_overrides(miso_zonal_gas_basis_skip_923_priced=False)
    _crafted, seen_off = _seam(monkeypatch, off)
    assert "skip_cells" not in seen_off["kw"]


def test_resolve_never_passes_the_mask_to_another_iso(monkeypatch):
    """A PJM run with the MISO flag set must not touch the PJM applier's call."""
    fleet = _fleet()
    seen: dict = {}

    def recorder(fuel_prices, fleet_, config, year, **kw):
        seen["kw"] = kw

    monkeypatch.setattr(
        "market_sim.data.fuel.resolve.apply_plant_monthly_fuel_prices",
        lambda fp, fl, c, y: np.ones((fl.n_gen, c.hours), dtype=bool),
    )
    monkeypatch.setitem(fuel.ZONAL_BASIS_APPLIERS, "PJM", recorder)
    cfg = ScenarioConfig(
        iso="PJM",
        hours=HOURS,
        mode="backcast",
        miso_zonal_gas_basis_skip_923_priced=True,
    )
    resolve_fuel_prices(cfg, fleet, 2025)
    assert seen["kw"] == {}
