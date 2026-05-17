"""Integration tests exercising dispatch, transmission and storage together."""

import unittest

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.storage import StorageUnit, storage_units_to_arrays
from market_sim.model.transmission import build_incidence_matrix, get_ttc_array


def _check_energy_balance(result, fleet, demand, incidence, storage_arrays, atol=1e-4):
    """Assert per-zone per-hour energy balance: gen + wind + solar + dis - chg + flow + slack = demand."""
    T = demand.shape[1]
    n_zones = demand.shape[0]
    gen_by_zone = np.zeros((n_zones, T))
    for g in range(fleet.n_gen):
        gen_by_zone[fleet.zone_idx[g]] += result.dispatch[g]
    net_flow = incidence.toarray() @ result.flows if result.flows is not None else np.zeros((n_zones, T))
    chg_by_zone = np.zeros((n_zones, T))
    dis_by_zone = np.zeros((n_zones, T))
    if storage_arrays is not None and result.storage_charge is not None:
        for s in range(storage_arrays.n_storage):
            chg_by_zone[storage_arrays.zone_idx[s]] += result.storage_charge[s]
            dis_by_zone[storage_arrays.zone_idx[s]] += result.storage_discharge[s]
    dump = result.dump if result.dump is not None else np.zeros_like(result.slack)
    supply = (gen_by_zone + result.wind_dispatched + result.solar_dispatched
              + dis_by_zone - chg_by_zone + net_flow + result.slack - dump)
    np.testing.assert_allclose(supply, demand, atol=atol)


class TestErcotIntegration(unittest.TestCase):
    """One-week ERCOT dispatch with transmission and storage."""

    def test_week_dispatch(self):
        T = 168
        iso = get_iso_config("ERCOT")
        zone_names = iso.zone_names

        gen_specs = [
            ("North", 4000.0, 20.0),
            ("North", 2000.0, 35.0),
            ("South", 2000.0, 40.0),
            ("West", 1000.0, 65.0),
            ("Houston", 3000.0, 42.0),
            ("Houston", 2000.0, 75.0),
        ]
        gens = [
            Generator(
                unit_id=f"G{i}",
                name=f"G{i}",
                zone=zone,
                fuel_type="gas_cc",
                pmax_mw=pmax,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=vom,
                eford=0.0,
            )
            for i, (zone, pmax, vom) in enumerate(gen_specs)
        ]
        fleet = generators_to_fleet_arrays(gens, zone_names, hours=T)
        mc = np.array([[g.vom] * T for g in gens], dtype=float)

        eta = 0.85**0.5
        units = [
            StorageUnit(
                unit_id="STO_Houston",
                zone="Houston",
                tech_name="li_ion_4hr",
                power_cap_mw=500.0,
                energy_cap_mwh=2000.0,
                eta_charge=eta,
                eta_discharge=eta,
            ),
            StorageUnit(
                unit_id="STO_North",
                zone="North",
                tech_name="li_ion_4hr",
                power_cap_mw=200.0,
                energy_cap_mwh=800.0,
                eta_charge=eta,
                eta_discharge=eta,
            ),
        ]
        sa = storage_units_to_arrays(units, zone_names)

        incidence = build_incidence_matrix(iso.links, zone_names)
        ttc = get_ttc_array(iso.links)

        hours = np.arange(T)
        hour_of_day = hours % 24
        daily_shape = 0.6 + 0.4 * np.sin(np.pi * (hour_of_day - 6) / 12)
        total_demand = 10000 * daily_shape
        demand = np.array([z.load_share for z in iso.zones])[:, None] * total_demand[None, :]

        n_zones = len(zone_names)
        west = zone_names.index("West")
        south_central = zone_names.index("South_Central")

        wind_cf = np.zeros((n_zones, T))
        wind_cf[west] = 0.3 + 0.2 * np.sin(2 * np.pi * hours / (24 * 7))
        wind_cap = np.zeros(n_zones)
        wind_cap[west] = 3000.0

        solar_cf = np.zeros((n_zones, T))
        solar_cf[south_central] = np.clip(
            0.7 * np.sin(np.pi * (hour_of_day - 6) / 12), 0, 1
        )
        solar_cap = np.zeros(n_zones)
        solar_cap[south_central] = 2000.0

        result = solve_dispatch(
            fleet,
            demand,
            wind_cf,
            wind_cap,
            solar_cf,
            solar_cap,
            mc=mc,
            incidence=incidence,
            ttc=ttc,
            storage_power_cap=sa.power_cap,
            storage_energy_cap=sa.energy_cap,
            storage_zone_idx=sa.zone_idx,
            eta_chg=sa.eta_chg,
            eta_dis=sa.eta_dis,
        )

        # a) energy balance holds
        _check_energy_balance(result, fleet, demand, incidence, sa)

        # b) flows stay within total transfer capability
        self.assertTrue(np.all(np.abs(result.flows) <= ttc[:, None] + 1e-6))

        # c) storage actually cycles
        self.assertGreater(result.storage_charge.sum(), 0)
        self.assertGreater(result.storage_discharge.sum(), 0)

        # d) storage charges cheap, discharges expensive (Houston, zone idx 3)
        chg_mask = result.storage_charge[0] > 1.0
        dis_mask = result.storage_discharge[0] > 1.0
        if chg_mask.any() and dis_mask.any():
            self.assertLess(
                result.prices[3][chg_mask].mean(),
                result.prices[3][dis_mask].mean(),
            )

        # e) state of charge is non-negative
        self.assertTrue(np.all(result.storage_soc >= -1e-6))

        # f) no negative slack
        self.assertTrue(np.all(result.slack >= -1e-6))


class TestFullYearPerformance(unittest.TestCase):
    """Full-year (8760h) dispatch performance over the ERCOT topology."""

    def test_full_year(self):
        T = 8760
        iso = get_iso_config("ERCOT")
        zone_names = iso.zone_names

        zones_cycle = zone_names * 50
        gens = [
            Generator(
                unit_id=f"G{i}",
                name=f"G{i}",
                zone=zones_cycle[i],
                fuel_type="gas_cc",
                pmax_mw=100.0,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=15 + 75 * i / 200,
                eford=0.0,
            )
            for i in range(200)
        ]
        fleet = generators_to_fleet_arrays(gens, zone_names, hours=T)
        mc = np.array([[g.vom] * T for g in gens], dtype=float)

        eta = 0.85**0.5
        units = [
            StorageUnit(
                unit_id=f"STO{i}",
                zone=zone_names[i % len(zone_names)],
                tech_name="li_ion_4hr",
                power_cap_mw=100.0,
                energy_cap_mwh=400.0,
                eta_charge=eta,
                eta_discharge=eta,
            )
            for i in range(5)
        ]
        sa = storage_units_to_arrays(units, zone_names)

        incidence = build_incidence_matrix(iso.links, zone_names)
        ttc = get_ttc_array(iso.links)

        hours = np.arange(T)
        hod = hours % 24
        daily = 0.6 + 0.4 * np.sin(np.pi * (hod - 6) / 12)
        total = 12000 * daily
        demand = np.array([z.load_share for z in iso.zones])[:, None] * total[None, :]

        n_zones = len(zone_names)
        west = zone_names.index("West")
        south_central = zone_names.index("South_Central")

        wind_cf = np.zeros((n_zones, T))
        wind_cf[west] = 0.35
        wind_cap = np.zeros(n_zones)
        wind_cap[west] = 2000.0

        solar_cf = np.zeros((n_zones, T))
        solar_cf[south_central] = np.clip(
            0.6 * np.sin(np.pi * (hod - 6) / 12), 0, 1
        )
        solar_cap = np.zeros(n_zones)
        solar_cap[south_central] = 1500.0

        result = solve_dispatch(
            fleet,
            demand,
            wind_cf,
            wind_cap,
            solar_cf,
            solar_cap,
            mc=mc,
            incidence=incidence,
            ttc=ttc,
            storage_power_cap=sa.power_cap,
            storage_energy_cap=sa.energy_cap,
            storage_zone_idx=sa.zone_idx,
            eta_chg=sa.eta_chg,
            eta_dis=sa.eta_dis,
        )

        # a) energy balance holds
        _check_energy_balance(result, fleet, demand, incidence, sa)

        # b) flows stay within total transfer capability
        self.assertTrue(np.all(np.abs(result.flows) <= ttc[:, None] + 1e-6))

        # c) matrix build stays fast
        self.assertLess(result.build_time, 3.0)

        # d) total build + solve stays within budget
        self.assertLess(result.build_time + result.solve_time, 30.0)

        # e) report timings
        print(
            f"8760h perf: build={result.build_time:.2f}s "
            f"solve={result.solve_time:.2f}s"
        )


if __name__ == "__main__":
    unittest.main()
