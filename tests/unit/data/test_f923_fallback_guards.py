"""The two F923 nearby-plant fallback guards (caiso-243).

FINDING-caiso242-offer-basis-identity-2026-09-03.md §5 measured three compounding
defects that delivered one EIA-923 row (96.161 $/MMBtu on 2.6 % of a plant's
normal volume) to 2,446 MW of CAISO neighbours for all of November 2025:

  D1  ``bins_to_fleet`` never set ``Generator.state``, so the fallback's
      state-first donor tier (the only one with a reporter-count guard) was
      skipped on every plant-level fleet;
  D2  the zone tier had NO reporter-count guard and served from a pool of ONE.

Repair form (c) ``ScenarioConfig.fleet_state_from_eia860`` stamps the EIA-860
plant state onto the CAMPD-bin fleet; form (a)
``ScenarioConfig.nearby_fuel_price_zone_donor_guard`` extends the EXISTING
``nearby_fuel_price_min_state_plants`` floor to the zone tier. These tests pin
the contracts: both OFF paths are byte-identical to the historical behaviour;
a pool-of-one zone-month is refused only under the guard, at the registered
floor, with no new constant; a zone that clears the floor is untouched; the
state stamp reaches every tranche row and stays empty for plants absent from
the table.
"""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays, bins_to_fleet
from market_sim.data.fuel import _NearbyFuelPrices

YEAR = 2025
#: The row that motivated the guard, in the shape the resolver sees it.
BAD_PRICE = 96.161
BAD_QTY = 5_234.0
GOOD_PRICE = 4.2
GOOD_QTY = 2_000_000.0


def _fleet(states: list[str], zones: list[int]) -> FleetArrays:
    n = len(states)
    hours = 24
    return FleetArrays(
        pmax=np.full(n, 100.0),
        pmin=np.zeros(n),
        heat_rate=np.full(n, 7.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.array(zones, dtype=int),
        fuel_type_idx=np.full(n, FUEL_TYPE_MAP["gas_cc"]),
        availability=np.ones((n, hours)),
        unit_ids=[f"U{i}" for i in range(n)],
        efficiency_bin=np.zeros(n, dtype=int),
        plant_code=np.arange(1, n + 1),
        state=np.array(states, dtype=object),
        plant_group=np.array(["CC_REGULAR"] * n, dtype=object),
    )


def _costs(rows: list[tuple[int, str, float, float]]) -> pd.DataFrame:
    """``(plant_id, state, price, quantity)`` reported in every month of YEAR."""
    out = []
    for month in range(1, 13):
        for plant_id, state, price, qty in rows:
            out.append(
                {
                    "year": YEAR,
                    "month": month,
                    "plant_id": plant_id,
                    "state": state,
                    "fuel_group": "Natural Gas",
                    "price_per_mmbtu": price,
                    "quantity": qty,
                }
            )
    return pd.DataFrame(out)


def _config(**overrides) -> ScenarioConfig:
    base = dict(
        iso="CAISO",
        hours=24,
        gas_plant_monthly_fuel_pricing=True,
        nearby_fuel_price_fallback=True,
        nearby_fuel_price_min_state_plants=2,
    )
    base.update(overrides)
    return ScenarioConfig(**base)


class ZoneDonorGuardTest(unittest.TestCase):
    """Repair form (a): the zone tier carries the state tier's reporter floor."""

    def _nearby(self, guard: bool) -> _NearbyFuelPrices:
        # zone 0: ONE reporter (plant 1, the bad row); zone 1: TWO reporters.
        # No plant carries a state, so the state tier is unreachable (D1) and
        # the zone tier is what prices every recipient — the keeper's path.
        fleet = _fleet(states=["", "", "", "", ""], zones=[0, 0, 1, 1, 1])
        costs = _costs(
            [
                (1, "NV", BAD_PRICE, BAD_QTY),
                (3, "CA", GOOD_PRICE, GOOD_QTY),
                (4, "CA", GOOD_PRICE + 0.4, GOOD_QTY),
            ]
        )
        return _NearbyFuelPrices(
            costs, YEAR, fleet, _config(nearby_fuel_price_zone_donor_guard=guard)
        )

    def test_off_path_is_the_historical_pool_of_one(self):
        fill = self._nearby(guard=False).month_prices(
            "Natural Gas", "", 0, "CC_REGULAR"
        )
        np.testing.assert_allclose(fill, np.full(12, BAD_PRICE))

    def test_guard_refuses_the_pool_of_one(self):
        fill = self._nearby(guard=True).month_prices("Natural Gas", "", 0, "CC_REGULAR")
        self.assertTrue(
            np.isnan(fill).all(), "a pool of one must return NaN under the guard"
        )

    def test_guard_keeps_a_zone_that_clears_the_floor(self):
        nearby = self._nearby(guard=True)
        fill = nearby.month_prices("Natural Gas", "", 1, "CC_REGULAR")
        expected = (GOOD_PRICE + (GOOD_PRICE + 0.4)) / 2.0  # equal quantities
        np.testing.assert_allclose(fill, np.full(12, expected))
        # and the off path gives the identical number for that zone
        off = self._nearby(guard=False).month_prices("Natural Gas", "", 1, "CC_REGULAR")
        np.testing.assert_array_equal(fill, off)

    def test_floor_is_the_registered_state_floor_not_a_new_constant(self):
        nearby = self._nearby(guard=True)
        self.assertEqual(nearby._min_zone, nearby._min_state)
        self.assertEqual(nearby._min_zone, 2)
        # relaxing the registered floor to 1 re-admits the pool of one:
        fleet = _fleet(states=[""], zones=[0])
        costs = _costs([(1, "NV", BAD_PRICE, BAD_QTY)])
        relaxed = _NearbyFuelPrices(
            costs,
            YEAR,
            fleet,
            _config(
                nearby_fuel_price_zone_donor_guard=True,
                nearby_fuel_price_min_state_plants=1,
            ),
        )
        np.testing.assert_allclose(
            relaxed.month_prices("Natural Gas", "", 0, "CC_REGULAR"),
            np.full(12, BAD_PRICE),
        )

    def test_state_tier_wins_when_the_fleet_carries_state(self):
        # Repair (c) in effect: a CA recipient with the two CA reporters in
        # its state is priced from the state pool BEFORE the zone tier, so
        # the pool-of-one zone never reaches it, guard or no guard.
        fleet = _fleet(states=["NV", "CA", "CA", "CA", "CA"], zones=[0, 0, 1, 1, 1])
        costs = _costs(
            [
                (1, "NV", BAD_PRICE, BAD_QTY),
                (3, "CA", GOOD_PRICE, GOOD_QTY),
                (4, "CA", GOOD_PRICE + 0.4, GOOD_QTY),
            ]
        )
        expected = (GOOD_PRICE + (GOOD_PRICE + 0.4)) / 2.0
        for guard in (False, True):
            nearby = _NearbyFuelPrices(
                costs, YEAR, fleet, _config(nearby_fuel_price_zone_donor_guard=guard)
            )
            fill = nearby.month_prices("Natural Gas", "CA", 0, "CC_REGULAR")
            np.testing.assert_allclose(fill, np.full(12, expected))
        # the NV recipient (one NV reporter < floor 2) still falls to the zone
        # tier — which only the guard refuses: (a) is what protects a thin state.
        nv_off = _NearbyFuelPrices(costs, YEAR, fleet, _config()).month_prices(
            "Natural Gas", "NV", 0, "CC_REGULAR"
        )
        np.testing.assert_allclose(nv_off, np.full(12, BAD_PRICE))
        nv_on = _NearbyFuelPrices(
            costs, YEAR, fleet, _config(nearby_fuel_price_zone_donor_guard=True)
        ).month_prices("Natural Gas", "NV", 0, "CC_REGULAR")
        self.assertTrue(np.isnan(nv_on).all())


ZONE_NAMES = get_iso_config("CAISO").zone_names
ZONE = ZONE_NAMES[0]
BASE_HR = 7.0


def _bin(plant: int) -> dict:
    """One synthetic per-plant CC_REGULAR bin row."""
    return {
        "Plant_Group": "CC_REGULAR",
        "ERCOT_Zone": ZONE,
        "Bin_Number": 1,
        "Bin_Label": f"TEST{plant}",
        "Plant_Code": plant,
        "Plant_Name": f"Test Plant {plant}",
        "capacity_mw": 500.0,
        "hr_weighted": BASE_HR,
        "hr_mr": BASE_HR,
        "hr_mc": BASE_HR * 0.92,
        "hr_econ": BASE_HR,
        "hr_peak": BASE_HR * 2.0,
        "pct_mr": 0,
        "pct_mc": 40,
        "pct_econ": 50,
        "pct_peak": 10,
        "min_run": 0,
        "min_down": 0,
        "plant_count": 1,
        "plant_codes": [plant],
        "fuel": "gas_cc",
    }


class FleetStateFromEia860Test(unittest.TestCase):
    """Repair form (c): the EIA-860 state reaches every tranche row of the CAMPD-bin fleet."""

    STATES = {55518: "CA", 55077: "NV"}

    def _build(self, flag: bool):
        bins = pd.DataFrame([_bin(55518), _bin(55077), _bin(999001)])
        config = ScenarioConfig(
            iso="CAISO", hours=24, plant_level_fleet=True, fleet_state_from_eia860=flag
        )
        with mock.patch(
            "market_sim.data.fleet.assembly.eia860_plant_states",
            return_value=self.STATES,
        ) as reader:
            gens, arrays = bins_to_fleet(bins, list(ZONE_NAMES), config)
        return gens, arrays, reader

    def test_off_path_carries_no_state_and_never_reads_the_table(self):
        gens, arrays, reader = self._build(flag=False)
        reader.assert_not_called()
        self.assertTrue(all(g.state == "" for g in gens))
        self.assertTrue(all(str(s) == "" for s in arrays.state))

    def test_on_path_stamps_every_tranche_row(self):
        gens, arrays, _ = self._build(flag=True)
        by_plant = {}
        for g in gens:
            by_plant.setdefault(int(g.plant_code), set()).add(g.state)
        self.assertEqual(by_plant[55518], {"CA"})
        self.assertEqual(by_plant[55077], {"NV"})
        # a plant absent from the table keeps the empty string (zonal tier)
        self.assertEqual(by_plant[999001], {""})
        self.assertEqual(sorted(set(str(s) for s in arrays.state)), ["", "CA", "NV"])

    def test_only_state_differs_between_the_two_paths(self):
        off, _, _ = self._build(flag=False)
        on, _, _ = self._build(flag=True)
        self.assertEqual(len(off), len(on))
        for a, b in zip(off, on):
            da, db = a.model_dump(), b.model_dump()
            da.pop("state"), db.pop("state")
            self.assertEqual(da, db)


if __name__ == "__main__":
    unittest.main()
