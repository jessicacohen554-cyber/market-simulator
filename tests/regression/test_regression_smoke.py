"""Smoke tests for ISO dispatch regression baseline.

For each of the 6 supported ISOs, builds a minimal single-zone fleet (2
generators, 24 hours) and runs ``solve_dispatch`` directly to verify:

  1. The LP solves successfully (status ``"Optimal"``).
  2. All zonal prices are non-negative.
  3. Energy balance holds every hour.

These tests do NOT exercise the full runner pipeline — they validate that
the core dispatch LP accepts each ISO's topology and returns a feasible
solution with sane prices. Total runtime target: <10 seconds.

Usage:
    pytest tests/regression/test_regression_smoke.py -v
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.transmission import build_incidence_matrix, get_ttc_array

ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP", "SOCO"]
T = 24


def _build_minimal_fleet(zone_names: list[str], hours: int = T):
    """Build a 2-generator fleet in the first load-carrying zone."""
    target_zone = zone_names[0]
    generators = [
        Generator(
            unit_id="G0",
            name="cheap_cc",
            zone=target_zone,
            fuel_type="gas_cc",
            pmax_mw=500.0,
            pmin_mw=0.0,
            heat_rate=7.0,
            vom=3.0,
            eford=0.0,
        ),
        Generator(
            unit_id="G1",
            name="peaker_ct",
            zone=target_zone,
            fuel_type="gas_ct",
            pmax_mw=200.0,
            pmin_mw=0.0,
            heat_rate=10.0,
            vom=5.0,
            eford=0.0,
        ),
    ]
    return generators_to_fleet_arrays(generators, zone_names, hours=hours)


def _build_dispatch_inputs(iso_name: str):
    """Assemble all inputs needed for a minimal solve_dispatch call."""
    iso_config = get_iso_config(iso_name)
    zone_names = iso_config.zone_names
    n_zones = iso_config.n_zones
    n_links = iso_config.n_links

    fleet = _build_minimal_fleet(zone_names, hours=T)

    mc = np.array([[30.0] * T, [60.0] * T])

    demand = np.full((n_zones, T), 100.0)

    wind_cf = np.full((n_zones, T), 0.3)
    wind_cap = np.full(n_zones, 50.0)
    solar_cf = np.full((n_zones, T), 0.2)
    solar_cap = np.full(n_zones, 30.0)

    kwargs = dict(
        fleet=fleet,
        demand=demand,
        wind_cf=wind_cf,
        wind_cap=wind_cap,
        solar_cf=solar_cf,
        solar_cap=solar_cap,
        mc=mc,
        voll=iso_config.voll,
        T=T,
    )

    if n_links > 0:
        incidence = build_incidence_matrix(iso_config.links, zone_names)
        ttc = get_ttc_array(iso_config.links)
        link_bidir = np.array(
            [link.is_bidirectional for link in iso_config.links], dtype=bool
        )
        kwargs["incidence"] = incidence
        kwargs["ttc"] = ttc
        kwargs["link_bidirectional"] = link_bidir

    return kwargs, n_zones


@pytest.fixture(params=ISOS)
def iso_name(request):
    """Parametrize over all 6 ISOs."""
    return request.param


class TestDispatchSmoke:
    """Smoke tests: each ISO solves a minimal LP successfully."""

    def test_lp_solves_optimally(self, iso_name):
        kwargs, _ = _build_dispatch_inputs(iso_name)
        result = solve_dispatch(**kwargs)
        assert result.status == "Optimal", (
            f"{iso_name}: LP status {result.status}, expected Optimal"
        )

    def test_prices_non_negative(self, iso_name):
        kwargs, _ = _build_dispatch_inputs(iso_name)
        result = solve_dispatch(**kwargs)
        assert np.all(result.prices >= 0), (
            f"{iso_name}: negative prices found, min={result.prices.min():.4f}"
        )

    def test_energy_balance(self, iso_name):
        kwargs, n_zones = _build_dispatch_inputs(iso_name)
        result = solve_dispatch(**kwargs)

        thermal_by_zone = np.zeros((n_zones, T))
        zone_idx = kwargs["fleet"].zone_idx
        for g in range(result.dispatch.shape[0]):
            z = zone_idx[g]
            thermal_by_zone[z] += result.dispatch[g]

        supply = (
            thermal_by_zone
            + result.wind_dispatched
            + result.solar_dispatched
            + result.slack
            - result.dump
        )

        if result.flows is not None:
            iso_config = get_iso_config(iso_name)
            incidence = build_incidence_matrix(iso_config.links, iso_config.zone_names)
            if hasattr(incidence, "toarray"):
                incidence = incidence.toarray()
            for t in range(T):
                supply[:, t] += incidence @ result.flows[:, t]

        if result.storage_charge is not None:
            storage_zone_idx = kwargs.get("storage_zone_idx")
            if storage_zone_idx is not None:
                for s in range(result.storage_charge.shape[0]):
                    z = storage_zone_idx[s]
                    supply[z] -= result.storage_charge[s]
                    supply[z] += result.storage_discharge[s]

        np.testing.assert_allclose(
            supply,
            kwargs["demand"],
            atol=1e-4,
            err_msg=f"{iso_name}: energy balance violated",
        )

    def test_dispatch_within_bounds(self, iso_name):
        kwargs, _ = _build_dispatch_inputs(iso_name)
        result = solve_dispatch(**kwargs)
        fleet = kwargs["fleet"]
        for g in range(result.dispatch.shape[0]):
            assert np.all(result.dispatch[g] >= -1e-6), (
                f"{iso_name}: gen {g} dispatch below zero"
            )
            pmax_avail = fleet.pmax[g] * fleet.availability[g]
            assert np.all(result.dispatch[g] <= pmax_avail + 1e-6), (
                f"{iso_name}: gen {g} dispatch exceeds pmax*availability"
            )
