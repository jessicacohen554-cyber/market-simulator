"""Tests for the EIA-923 CC-family heat-rate repair (NWPP-NEXT-14).

Covers the reader (committed NWPP artifact; ``ok`` rows only; an ISO with no
artifact is a no-op), the frame-level population rule (only a non-CHP plant's
CC-prime-mover rows below the CC physical floor move; GT rows, CHP plants,
plants the eGRID family construction covered and plants whose EIA-923 rate is
outside the window never move), the vintage lookup, and the committed
artifact's Clark 2322 rows.
"""

import unittest
from unittest import mock

import pandas as pd

from market_sim.config.constants import EGRID_CC_HR_PHYSICAL_CEILING, HEAT_RATE_BINS
from market_sim.data.fleet import eia860
from market_sim.data.fleet.eia860 import (
    EGRID_CC_HR_PHYSICAL_FLOOR,
    _apply_eia923_cc_family_heat_rates,
    _eia923_rate_for_vintage,
    eia923_cc_family_heat_rates_for,
)

CLARK = 2322


def _frame(chp: str = "N") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "plant_id": [CLARK, CLARK, CLARK, 9999],
            "prime_mover": ["CT", "CA", "GT", "CT"],
            "heat_rate": [3.007, 3.007, 3.007, 7.1],
            "chp": [chp, chp, chp, "N"],
        }
    )


class TestConstants(unittest.TestCase):
    def test_floor_is_the_h_class_bin(self):
        self.assertEqual(
            EGRID_CC_HR_PHYSICAL_FLOOR, HEAT_RATE_BINS["gas_cc"]["h_class"]
        )
        self.assertLess(EGRID_CC_HR_PHYSICAL_FLOOR, EGRID_CC_HR_PHYSICAL_CEILING)


class TestReader(unittest.TestCase):
    def test_nwpp_artifact_carries_clark(self):
        rates = eia923_cc_family_heat_rates_for("NWPP")
        for y in range(2019, 2026):
            hr = rates[(CLARK, y)]
            self.assertGreaterEqual(hr, EGRID_CC_HR_PHYSICAL_FLOOR)
            self.assertLessEqual(hr, EGRID_CC_HR_PHYSICAL_CEILING)
            self.assertAlmostEqual(hr, 9.3, delta=0.35)

    def test_missing_artifact_is_empty(self):
        self.assertEqual(eia923_cc_family_heat_rates_for("NOSUCHISO"), {})

    def test_vintage_lookup(self):
        rates = {(1, 2019): 9.0, (1, 2021): 9.2}
        self.assertEqual(_eia923_rate_for_vintage(rates, 1, 2020), 9.0)
        self.assertEqual(_eia923_rate_for_vintage(rates, 1, 2024), 9.2)
        self.assertEqual(_eia923_rate_for_vintage(rates, 1, 2018), 9.0)
        self.assertIsNone(_eia923_rate_for_vintage(rates, 2, 2020))


class TestApply(unittest.TestCase):
    def _run(self, df, rates, covered=frozenset(), vintage=2023):
        with (
            mock.patch.object(
                eia860, "eia923_cc_family_heat_rates_for", return_value=rates
            ),
            mock.patch(
                "market_sim.data.egrid.egrid_vintage_for_eia860_dir",
                return_value=vintage,
            ),
            mock.patch.dict(eia860._EGRID_FAMILY_COVERED_PLANTS, {"NWPP": covered}),
        ):
            return _apply_eia923_cc_family_heat_rates(df, "NWPP")

    def test_cc_rows_below_floor_move(self):
        out, rep = self._run(_frame(), {(CLARK, 2023): 9.4756})
        self.assertEqual(rep, frozenset({CLARK}))
        self.assertEqual(list(out["heat_rate"]), [9.4756, 9.4756, 3.007, 7.1])

    def test_input_not_mutated(self):
        df = _frame()
        self._run(df, {(CLARK, 2023): 9.4756})
        self.assertEqual(list(df["heat_rate"]), [3.007, 3.007, 3.007, 7.1])

    def test_chp_plant_untouched(self):
        out, rep = self._run(_frame(chp="Y"), {(CLARK, 2023): 9.4756})
        self.assertEqual(rep, frozenset())
        self.assertEqual(list(out["heat_rate"]), [3.007, 3.007, 3.007, 7.1])

    def test_family_covered_plant_untouched(self):
        out, rep = self._run(
            _frame(), {(CLARK, 2023): 9.4756}, covered=frozenset({CLARK})
        )
        self.assertEqual(rep, frozenset())

    def test_out_of_window_rate_refused(self):
        out, rep = self._run(_frame(), {(CLARK, 2023): 4.0})
        self.assertEqual(rep, frozenset())
        self.assertEqual(list(out["heat_rate"])[0], 3.007)

    def test_plausible_rate_untouched(self):
        df = _frame()
        df["heat_rate"] = 7.2
        out, rep = self._run(df, {(CLARK, 2023): 9.4756})
        self.assertEqual(rep, frozenset())

    def test_no_prime_mover_column_is_noop(self):
        df = _frame().drop(columns=["prime_mover"])
        out, rep = _apply_eia923_cc_family_heat_rates(df, "NWPP")
        self.assertIs(out, df)
        self.assertEqual(rep, frozenset())


if __name__ == "__main__":
    unittest.main()
