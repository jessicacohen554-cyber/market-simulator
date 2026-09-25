"""Tests for the combined-cycle block-rated-on-one-row reconciliation (miso-272).

``ScenarioConfig.cc_block_summer_rating``. Some EIA-860 filers report a
combined-cycle block's WHOLE net summer rating on the steam-part (``CA``) row
and leave every gas-turbine (``CT``) sibling blank; the loader's "summer, else
nameplate" fill then carries the block rating PLUS each blank CT's nameplate.
MISO 1004 Edwardsport (IGCC) is the defining case: 555 MW on a 331.5 MW CA
nameplate, CTs 240.6 MW each and blank, carried as 1,036 MW.

The tests pin: the predicate (which blocks qualify and which never do), the
nameplate-proportional allocation (block sums to the reported rating, unit
shares preserved), that the downstream CC guard then does not fire on a
reconciled block (rule 19), and that the flag is byte-identical off.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

import market_sim.data.fleet.eia860 as mod
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet.eia860 import (
    _apply_cc_block_summer_rating,
    _cc_block_summer_ratings,
    _rows_to_generators,
)


def _raw_row(plant, gen, pm, uc, np_mw, su_mw, status="OP", es="SGC"):
    """One row of the raw EIA-860 operable sheet (the columns the predicate reads)."""
    return {
        "Plant Code": plant,
        "Generator ID": gen,
        "Prime Mover": pm,
        "Unit Code": uc,
        "Status": status,
        "Nameplate Capacity (MW)": np_mw,
        "Summer Capacity (MW)": su_mw,
        "Energy Source 1": es,
    }


def _raw_sheet() -> pd.DataFrame:
    """Edwardsport, a Union-style multi-block plant, and four non-qualifying blocks."""
    return pd.DataFrame(
        [
            # 1004 Edwardsport: the defining block (blank CTs, CA > own nameplate).
            _raw_row(1004, "CT1", "CT", "1", 240.6, None),
            _raw_row(1004, "CT2", "CT", "1", 240.6, None),
            _raw_row(1004, "ST", "CA", "1", 331.5, 555.0),
            # Two blocks at one plant, each rated on its own CA row.
            _raw_row(55380, "CTG1", "CT", "BL01", 176.0, None),
            _raw_row(55380, "CTG2", "CT", "BL01", 176.0, None),
            _raw_row(55380, "STG1", "CA", "BL01", 255.0, 506.0),
            _raw_row(55380, "CTG3", "CT", "BL02", 176.0, None),
            _raw_row(55380, "CTG4", "CT", "BL02", 176.0, None),
            _raw_row(55380, "STG2", "CA", "BL02", 255.0, 504.0),
            # A standalone peaker at a qualifying plant: no unit code, never moves.
            _raw_row(55620, "2-CT", "GT", None, 186.2, 148.5),
            _raw_row(55620, "CT-1", "CT", "PB01", 198.9, None, es="NG"),
            _raw_row(55620, "CT-2", "CT", "PB01", 198.9, None, es="NG"),
            _raw_row(55620, "ST-1", "CA", "PB01", 240.1, 576.8, es="NG"),
            # Component filing: every row carries its own rating -> untouched.
            _raw_row(7000, "CT1", "CT", "A", 200.0, 180.0),
            _raw_row(7000, "ST1", "CA", "A", 120.0, 110.0),
            # Blank CT but the CA does NOT exceed its nameplate -> untouched
            # (nothing says the CA row is a block total).
            _raw_row(7001, "CT1", "CT", "A", 200.0, None),
            _raw_row(7001, "ST1", "CA", "A", 120.0, 110.0),
            # CA > nameplate but no unit code -> no block statement -> untouched.
            _raw_row(7002, "CT1", "CT", None, 200.0, None),
            _raw_row(7002, "ST1", "CA", None, 120.0, 300.0),
            # Retired (non-OP) rows never form a block.
            _raw_row(7003, "CT1", "CT", "A", 200.0, None, status="RE"),
            _raw_row(7003, "ST1", "CA", "A", 120.0, 300.0, status="RE"),
        ]
    )


class _SheetDir:
    """A temp EIA-860 directory holding the synthetic raw operable sheet."""

    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory()
        path = Path(self._tmp.name)
        _raw_sheet().to_parquet(path / "eia860_generator_operable.parquet")
        _cc_block_summer_ratings.cache_clear()
        return path

    def __exit__(self, *exc) -> None:
        _cc_block_summer_ratings.cache_clear()
        self._tmp.cleanup()


def _fleet_frame() -> pd.DataFrame:
    """The processed-parquet rows the loader reads for the Edwardsport block."""
    common = {
        "plant_name": "Edwardsport",
        "state": "IN",
        "operating_year": 2013,
        "status": "OP",
        "heat_rate": 10.5,
        "chp": "N",
        "plant_id": 1004,
        "technology": "Coal Integrated Gasification Combined Cycle",
        "energy_source": "SGC",
    }
    return pd.DataFrame(
        [
            {
                **common,
                "generator_id": "CT1",
                "prime_mover": "CT",
                "nameplate_capacity_mw": 240.6,
                "net_summer_capacity_mw": None,
            },
            {
                **common,
                "generator_id": "CT2",
                "prime_mover": "CT",
                "nameplate_capacity_mw": 240.6,
                "net_summer_capacity_mw": None,
            },
            {
                **common,
                "generator_id": "ST",
                "prime_mover": "CA",
                "nameplate_capacity_mw": 331.5,
                "net_summer_capacity_mw": 555.0,
            },
        ]
    )


class TestPredicate(unittest.TestCase):
    """Which blocks qualify, and what each row is allocated."""

    def test_qualifying_blocks_only(self) -> None:
        with _SheetDir() as d:
            ratings = _cc_block_summer_ratings(d)
        plants = {p for p, _ in ratings}
        self.assertEqual(plants, {1004, 55380})

    def test_block_sums_to_reported_rating(self) -> None:
        with _SheetDir() as d:
            r = _cc_block_summer_ratings(d)
        self.assertAlmostEqual(
            r[(1004, "CT1")] + r[(1004, "CT2")] + r[(1004, "ST")], 555.0
        )
        bl01 = r[(55380, "CTG1")] + r[(55380, "CTG2")] + r[(55380, "STG1")]
        bl02 = r[(55380, "CTG3")] + r[(55380, "CTG4")] + r[(55380, "STG2")]
        self.assertAlmostEqual(bl01, 506.0)
        self.assertAlmostEqual(bl02, 504.0)

    def test_allocation_is_nameplate_proportional(self) -> None:
        with _SheetDir() as d:
            r = _cc_block_summer_ratings(d)
        self.assertAlmostEqual(r[(1004, "CT1")], 555.0 * 240.6 / 812.7)
        self.assertAlmostEqual(r[(1004, "ST")], 555.0 * 331.5 / 812.7)

    def test_ng_block_is_left_to_the_measured_cc_guard(self) -> None:
        """v2 (rule 19/13): an NG block is owned by the measured CC guard / cap."""
        with _SheetDir() as d:
            r = _cc_block_summer_ratings(d)
        self.assertFalse(any(p == 55620 for p, _ in r))

    def test_standalone_peaker_never_moves(self) -> None:
        with _SheetDir() as d:
            r = _cc_block_summer_ratings(d)
        self.assertNotIn((55620, "2-CT"), r)

    def test_missing_sheet_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            _cc_block_summer_ratings.cache_clear()
            self.assertEqual(_cc_block_summer_ratings(Path(t)), {})


class TestLoaderSeam(unittest.TestCase):
    """The frame rewrite and what the row loop then builds from it."""

    def test_rewrite_moves_only_block_rows(self) -> None:
        frame = _fleet_frame()
        extra = frame.iloc[[0]].assign(
            plant_id=9999, generator_id="X", net_summer_capacity_mw=50.0
        )
        frame = pd.concat([frame, extra], ignore_index=True)
        with _SheetDir() as d:
            out = _apply_cc_block_summer_rating(frame, d, "MISO")
        self.assertAlmostEqual(out["net_summer_capacity_mw"].iloc[:3].sum(), 555.0)
        self.assertEqual(float(out["net_summer_capacity_mw"].iloc[3]), 50.0)

    def test_phantom_removed_from_fleet(self) -> None:
        before = _rows_to_generators(_fleet_frame(), "MISO", None)
        with _SheetDir() as d:
            fixed = _apply_cc_block_summer_rating(_fleet_frame(), d, "MISO")
        after = _rows_to_generators(fixed, "MISO", None)
        self.assertAlmostEqual(sum(g.pmax_mw for g in before), 1036.2, places=1)
        self.assertAlmostEqual(sum(g.pmax_mw for g in after), 555.0, places=6)

    def test_ng_block_keeps_the_measured_guard(self) -> None:
        """v2, rule 19: an NG block is NOT rewritten, so the CC guard still owns it."""
        frame = _fleet_frame().assign(
            plant_id=55620,
            energy_source="NG",
            technology="Natural Gas Fired Combined Cycle",
        )
        frame["generator_id"] = ["CT-1", "CT-2", "ST-1"]
        frame["nameplate_capacity_mw"] = [198.9, 198.9, 240.1]
        frame.loc[2, "net_summer_capacity_mw"] = 576.8
        with _SheetDir() as d:
            fixed = _apply_cc_block_summer_rating(frame, d, "MISO")
        pd.testing.assert_frame_equal(fixed, frame)
        mod._CC_PMAX_RECONCILED_PLANTS.pop("MISO", None)
        gens = _rows_to_generators(fixed, "MISO", None)
        # the guard clips the fill (576.8 + 2 x 198.9) to the nameplate bound
        self.assertAlmostEqual(sum(g.pmax_mw for g in gens), 637.9, places=6)
        self.assertIn(55620, mod.cc_pmax_reconciled_plants("MISO"))


class TestFlag(unittest.TestCase):
    """The ScenarioConfig field: default off, cache-key optional."""

    def test_default_off(self) -> None:
        self.assertIs(ScenarioConfig(iso="MISO").cc_block_summer_rating, False)

    def test_default_key_unmoved_armed_key_moves(self) -> None:
        base = ScenarioConfig(iso="MISO")
        armed = ScenarioConfig(iso="MISO", cc_block_summer_rating=True)
        self.assertNotEqual(base.cache_key(), armed.cache_key())
        self.assertEqual(
            base.cache_key(),
            ScenarioConfig(iso="MISO", cc_block_summer_rating=False).cache_key(),
        )


if __name__ == "__main__":
    unittest.main()
