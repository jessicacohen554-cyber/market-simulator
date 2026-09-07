"""``cc_summer_derate_reconciled_basis`` — the nyiso-212 seam repair.

Under ``cc_nameplate_summer_derate`` the Jun-Sep availability multiplier is
``net_summer / nameplate``, premised on the plant being carried at nameplate.
A ``cc_capacity_reconcile`` row moves the carried capacity off nameplate AFTER
that premise was fixed, so the ratio's denominator no longer matches the
capacity it multiplies. The flag divides by the carried capacity instead, at
the plants the reconcile table lists — and nowhere else.

Fixture: Cricket Valley 57185 (EIA-860 nameplate 1,312.5 MW, net summer
1,016.1 MW) carried at its CAMPD p99.9 of 1,086.9 MW as two tranches, beside an
unlisted control plant carried at nameplate. Statistical outage mode, so the
seasonal WEFOR split is identical on both arms and the summer ratio ON / OFF is
exactly ``nameplate / carried`` at the listed plant.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    cc_summer_capacity,
    generators_to_fleet_arrays,
)

PLANT = 57185
CARRIED_MW = 1086.9
_SUMMER = np.zeros(8760, dtype=bool)
_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
for _m in (6, 7, 8, 9):
    _SUMMER[_STARTS[_m - 1] : _STARTS[_m]] = True


def _gen(unit_id: str, plant_code: int, pmax: float) -> Generator:
    return Generator(
        unit_id=unit_id,
        name=f"CC {plant_code}",
        zone="Capital_Hudson",
        fuel_type="gas_cc",
        pmax_mw=pmax,
        heat_rate=6.5,
        eford=0.04,
        online_year=2020,
        is_campd_bin=True,
        plant_group="CC_REGULAR",
        plant_code=plant_code,
    )


class TestCcSummerDerateReconciledBasis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        caps = cc_summer_capacity()
        if PLANT not in caps:
            raise unittest.SkipTest("EIA-860 CC sheet not available in this checkout")
        cls.nameplate, cls.net_summer = caps[PLANT]
        # A control plant that IS on the EIA sheet but NOT in the reconcile table.
        cls.control = next(c for c in sorted(caps) if c != PLANT and caps[c][0] > 0)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.table = Path(cls.tmp.name) / "cc_capacity_reconcile_TEST.csv"
        cls.table.write_text(
            "plant_code,plant_name,current_mw,campd_p999_mw,eia860_winter_mw,"
            "reconciled_mw,delta_pct,source,mode\n"
            f"{PLANT},Cricket Valley Energy,{cls.nameplate},{CARRIED_MW},1138.2,"
            f"{CARRIED_MW},-17.2,campd_demonstrated_peak,cap\n"
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _avail(self, *, flag: bool, reconcile: bool = True) -> np.ndarray:
        cfg = ScenarioConfig(
            iso="NYISO",
            mode="backcast",
            outage_source="statistical",
            cc_nameplate_summer_derate=True,
            cc_capacity_reconcile=reconcile,
            cc_capacity_reconcile_path=str(self.table),
            cc_summer_derate_reconciled_basis=flag,
        )
        gens = [
            _gen("cv_a", PLANT, CARRIED_MW / 2),
            _gen("cv_b", PLANT, CARRIED_MW / 2),
            _gen("ctrl", self.control, float(cc_summer_capacity()[self.control][0])),
        ]
        fa = generators_to_fleet_arrays(
            gens, ["Capital_Hudson"], iso="NYISO", config=cfg, year=2024
        )
        return np.asarray(fa.availability, dtype=float)

    def test_listed_plant_summer_ratio_moves_by_nameplate_over_carried(self):
        off = self._avail(flag=False)
        on = self._avail(flag=True)
        expected = min(1.0, self.net_summer / CARRIED_MW) / min(
            1.0, self.net_summer / self.nameplate
        )
        self.assertAlmostEqual(expected, self.nameplate / CARRIED_MW, places=9)
        for row in (0, 1):
            ratio = on[row, _SUMMER] / off[row, _SUMMER]
            self.assertTrue(np.allclose(ratio, expected, atol=1e-9), ratio[:3])
            # Off-summer hours are untouched: the flag is a Jun-Sep statement.
            self.assertTrue(np.allclose(on[row, ~_SUMMER], off[row, ~_SUMMER]))
        # The two tranches of one plant read the same factor.
        self.assertTrue(np.allclose(on[0], on[1]))

    def test_unlisted_plant_is_byte_identical(self):
        off = self._avail(flag=False)
        on = self._avail(flag=True)
        self.assertTrue(np.array_equal(on[2], off[2]))

    def test_flag_is_inert_without_the_reconcile(self):
        off = self._avail(flag=False, reconcile=False)
        on = self._avail(flag=True, reconcile=False)
        self.assertTrue(np.array_equal(on, off))

    def test_default_is_off_and_registered(self):
        from market_sim.config import scenarios as sc

        self.assertFalse(ScenarioConfig().cc_summer_derate_reconciled_basis)
        self.assertIn(
            "cc_summer_derate_reconciled_basis", sc._CACHE_KEY_OPTIONAL_FIELDS
        )
        self.assertEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(cc_summer_derate_reconciled_basis=False).cache_key(),
        )
        self.assertNotEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(cc_summer_derate_reconciled_basis=True).cache_key(),
        )


if __name__ == "__main__":
    unittest.main()
