"""Tests for the CAISO measured storage-AS reservation (caiso-74 mechanism).

Trivial cases first (CLAUDE.md testing pattern): the award allocation and SOC
sustain floor are exercised on a 2-unit (battery + pumped-storage) fleet with
patched measured series, then the SOC lower bound is verified end-to-end on a
tiny 1-zone/4-hour LP (``build_variable_bounds``) — no clean-data dependency.
"""

import unittest
from unittest import mock

import numpy as np

from market_sim.model.storage import (
    StorageUnit,
    caiso_storage_as_soc_min,
    reserve_caiso_storage_as_power,
)

HOURS = 4


def _units() -> list[StorageUnit]:
    return [
        StorageUnit(
            unit_id="LA_BASIN_eia860_storage",
            zone="LA_BASIN",
            tech_name="li_ion",
            power_cap_mw=300.0,
            energy_cap_mwh=1200.0,
        ),
        StorageUnit(
            unit_id="NP15_eia860_storage",
            zone="NP15",
            tech_name="li_ion",
            power_cap_mw=100.0,
            energy_cap_mwh=400.0,
        ),
        StorageUnit(
            unit_id="NP15_eia860_pumped_storage",
            zone="NP15",
            tech_name="pumped_storage",
            power_cap_mw=1000.0,
            energy_cap_mwh=12000.0,
        ),
    ]


class TestReserveCaisoStorageAsPower(unittest.TestCase):
    def test_pro_rata_battery_only(self) -> None:
        pc = np.array([300.0, 100.0, 1000.0])
        with mock.patch(
            "market_sim.data.storage_as_awards.upward_award_mw",
            return_value=np.full(HOURS, 40.0),
        ):
            out = reserve_caiso_storage_as_power(pc, _units(), 2024, HOURS)
        self.assertEqual(out.shape, (3, HOURS))
        # 40 MW allocated 3:1 across the two batteries; PS untouched.
        np.testing.assert_allclose(out[0], 300.0 - 30.0)
        np.testing.assert_allclose(out[1], 100.0 - 10.0)
        np.testing.assert_allclose(out[2], 1000.0)

    def test_award_never_negative(self) -> None:
        pc = np.array([300.0, 100.0, 1000.0])
        with mock.patch(
            "market_sim.data.storage_as_awards.upward_award_mw",
            return_value=np.full(HOURS, 10_000.0),
        ):
            out = reserve_caiso_storage_as_power(pc, _units(), 2024, HOURS)
        self.assertTrue((out >= 0.0).all())
        np.testing.assert_allclose(out[2], 1000.0)

    def test_empty_fleet_passthrough(self) -> None:
        pc = np.zeros(0)
        out = reserve_caiso_storage_as_power(pc, [], 2024, HOURS)
        self.assertIs(out, pc)


class TestCaisoStorageAsSocMin(unittest.TestCase):
    def test_sustain_floor_pro_rata_and_capped(self) -> None:
        pc = np.array([300.0, 100.0, 1000.0])
        ec = np.array([1200.0, 400.0, 12000.0])
        with mock.patch(
            "market_sim.data.storage_as_awards.sustain_energy_mwh",
            return_value=np.full(HOURS, 200.0),
        ):
            soc_min = caiso_storage_as_soc_min(pc, ec, _units(), 2024, HOURS)
        # 200 MWh allocated 3:1 by battery power; PS row zero.
        np.testing.assert_allclose(soc_min[0], 150.0)
        np.testing.assert_allclose(soc_min[1], 50.0)
        np.testing.assert_allclose(soc_min[2], 0.0)

    def test_floor_clipped_at_energy_cap(self) -> None:
        pc = np.array([300.0, 100.0, 1000.0])
        ec = np.array([100.0, 400.0, 12000.0])  # small LA_BASIN energy cap
        with mock.patch(
            "market_sim.data.storage_as_awards.sustain_energy_mwh",
            return_value=np.full(HOURS, 10_000.0),
        ):
            soc_min = caiso_storage_as_soc_min(pc, ec, _units(), 2024, HOURS)
        self.assertTrue((soc_min[0] <= 100.0 + 1e-9).all())
        self.assertTrue((soc_min[1] <= 400.0 + 1e-9).all())


class TestSocMinBounds(unittest.TestCase):
    def test_build_variable_bounds_soc_floor(self) -> None:
        """1 gen / 1 zone / 4 h / 1 storage: SOC lower bound lands in place."""
        from market_sim.data.fleet import FleetArrays
        from market_sim.model.dispatch import VariableLayout, build_variable_bounds

        n_gen, n_zones, T, n_storage = 1, 1, HOURS, 1
        fleet = FleetArrays(
            pmax=np.array([100.0]),
            pmin=np.zeros(1),
            heat_rate=np.full(1, 8.0),
            vom=np.zeros(1),
            emission_rate=np.zeros(1),
            nox_rate=np.zeros(1),
            so2_rate=np.zeros(1),
            zone_idx=np.zeros(1, dtype=int),
            fuel_type_idx=np.zeros(1, dtype=int),
            availability=np.ones((1, T)),
            unit_ids=["g0"],
            efficiency_bin=np.zeros(1, dtype=int),
            plant_code=np.zeros(1, dtype=int),
        )
        layout = VariableLayout(
            n_gen=n_gen, n_zones=n_zones, T=T, n_storage=n_storage, n_links=0
        )
        soc_min = np.full((n_storage, T), 25.0)
        lo, hi = build_variable_bounds(
            layout,
            fleet,
            wind_cf=np.zeros((n_zones, T)),
            wind_cap=np.zeros(n_zones),
            solar_cf=np.zeros((n_zones, T)),
            solar_cap=np.zeros(n_zones),
            storage_power_cap=np.array([50.0]),
            storage_energy_cap=np.array([200.0]),
            storage_soc_min=soc_min,
        )
        lo2d = lo.reshape(HOURS, -1)
        soc_lo = lo2d[:, layout._soc_off : layout._flow_off]
        np.testing.assert_allclose(soc_lo, 25.0)
        # Floor above the cap is clipped to the cap (feasible pair).
        lo2, _ = build_variable_bounds(
            layout,
            fleet,
            wind_cf=np.zeros((n_zones, T)),
            wind_cap=np.zeros(n_zones),
            solar_cf=np.zeros((n_zones, T)),
            solar_cap=np.zeros(n_zones),
            storage_power_cap=np.array([50.0]),
            storage_energy_cap=np.array([200.0]),
            storage_soc_min=np.full((n_storage, T), 999.0),
        )
        np.testing.assert_allclose(
            lo2.reshape(HOURS, -1)[:, layout._soc_off : layout._flow_off], 200.0
        )


class TestStorageDischargeFloor(unittest.TestCase):
    """ERCOT ercot_storage_as_deployment: the discharge lower bound + helper."""

    def test_build_variable_bounds_discharge_floor(self) -> None:
        """1 gen / 1 zone / 4 h / 1 storage: discharge lower bound lands + clips."""
        from market_sim.data.fleet import FleetArrays
        from market_sim.model.dispatch import VariableLayout, build_variable_bounds

        n_gen, n_zones, T, n_storage = 1, 1, HOURS, 1
        fleet = FleetArrays(
            pmax=np.array([100.0]),
            pmin=np.zeros(1),
            heat_rate=np.full(1, 8.0),
            vom=np.zeros(1),
            emission_rate=np.zeros(1),
            nox_rate=np.zeros(1),
            so2_rate=np.zeros(1),
            zone_idx=np.zeros(1, dtype=int),
            fuel_type_idx=np.zeros(1, dtype=int),
            availability=np.ones((1, T)),
            unit_ids=["g0"],
            efficiency_bin=np.zeros(1, dtype=int),
            plant_code=np.zeros(1, dtype=int),
        )
        layout = VariableLayout(
            n_gen=n_gen, n_zones=n_zones, T=T, n_storage=n_storage, n_links=0
        )
        dmin = np.full((n_storage, T), 20.0)
        lo, _ = build_variable_bounds(
            layout,
            fleet,
            wind_cf=np.zeros((n_zones, T)),
            wind_cap=np.zeros(n_zones),
            solar_cf=np.zeros((n_zones, T)),
            solar_cap=np.zeros(n_zones),
            storage_power_cap=np.array([50.0]),
            storage_energy_cap=np.array([200.0]),
            storage_discharge_min=dmin,
        )
        dis_lo = lo.reshape(HOURS, -1)[:, layout._dis_off : layout._soc_off]
        np.testing.assert_allclose(dis_lo, 20.0)
        # Floor above the power cap is clipped to the cap (feasible bound pair).
        lo2, _ = build_variable_bounds(
            layout,
            fleet,
            wind_cf=np.zeros((n_zones, T)),
            wind_cap=np.zeros(n_zones),
            solar_cf=np.zeros((n_zones, T)),
            solar_cap=np.zeros(n_zones),
            storage_power_cap=np.array([50.0]),
            storage_energy_cap=np.array([200.0]),
            storage_discharge_min=np.full((n_storage, T), 999.0),
        )
        np.testing.assert_allclose(
            lo2.reshape(HOURS, -1)[:, layout._dis_off : layout._soc_off], 50.0
        )

    def test_deployment_helper_is_measured_and_gated(self) -> None:
        """The deployment MW is non-negative, ramp-gated, and zero without a file."""
        from market_sim.results.scarcity import ercot_storage_as_deployment_mw

        T = 8760
        # Low overnight / high daytime net load -> the gate zeroes the night limb.
        nl = np.tile(np.concatenate([np.full(12, 30000.0), np.full(12, 55000.0)]), 365)[
            :T
        ]
        d = ercot_storage_as_deployment_mw(2023, T, nl)
        self.assertEqual(d.shape, (T,))
        self.assertTrue((d >= 0.0).all())
        # Overnight (net load below its own daily median) never deploys.
        hod = np.arange(T) % 24
        self.assertTrue((d[hod < 12] == 0.0).all())
        # A year with no award file returns all-zero (forward no-op).
        self.assertTrue((ercot_storage_as_deployment_mw(1990, T, nl) == 0.0).all())


if __name__ == "__main__":
    unittest.main()
