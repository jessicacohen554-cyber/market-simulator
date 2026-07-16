"""Tests for the mothballed-but-operating re-carry channel (Cottonwood lane).

``fleet.load_mothballed_but_operating`` re-carries an OA (mothballed) unit for
backcast solve year Y iff it is OP in the year-matched EIA-860 vintage — the
zero-DOF vintage-status availability oracle. Design charter:
``docs/handoffs/miso-cc-vintage-undercarry-plan-2026-07.md`` §5/§7.

Trivial synthetic cases first (one plant, two units, tmp-dir snapshot +
vintage), then the real committed-data case (Cottonwood 55358).
"""

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    EIA_860_PARQUET_NAME,
    load_fleet_from_csv,
    load_mothballed_but_operating,
)


def _frame(rows: list[dict]) -> pd.DataFrame:
    """Build a canonical-schema generator frame from row dicts."""
    base = {
        "plant_id": 99001,
        "generator_id": "U1",
        "plant_name": "Trivial CC",
        "balancing_authority_code": "MISO",
        "energy_source": "NG",
        "prime_mover": "CT",
        "technology": "Natural Gas Fired Combined Cycle",
        "nameplate_capacity_mw": 200.0,
        "net_summer_capacity_mw": 150.0,
        "operating_year": 2003,
        "status": "OP",
    }
    return pd.DataFrame([{**base, **r} for r in rows])


class TestVintageStatusOracle(unittest.TestCase):
    """Trivial-case synthetic snapshot/vintage pairs in a tmp dir."""

    def _write(
        self,
        tmp: Path,
        snapshot: pd.DataFrame,
        vintage: pd.DataFrame | None,
        year: int = 2023,
    ) -> None:
        snapshot.to_parquet(tmp / EIA_860_PARQUET_NAME)
        if vintage is not None:
            vdir = tmp / f"vintage_{year}"
            vdir.mkdir()
            vintage.to_parquet(vdir / EIA_860_PARQUET_NAME)

    def _load(self, tmp: Path, year: int | None = 2023) -> list:
        # The oracle resolves vintages under the canonical EIA-860 root;
        # point that root at the tmp dir so the test is hermetic.
        with unittest.mock.patch("market_sim.data.fleet.EIA_860_DIR", tmp):
            return load_mothballed_but_operating("MISO", data_dir=tmp, year=year)

    def test_oa_unit_op_in_vintage_is_carried(self):
        # One plant, two units: U1 stays OP (already in the fleet), U2 is OA
        # in the snapshot but OP in the year-matched vintage -> re-carried,
        # per-unit, at the VINTAGE row's year-matched capacity.
        snap = _frame([{}, {"generator_id": "U2", "status": "OA"}])
        vint = _frame([{}, {"generator_id": "U2", "net_summer_capacity_mw": 155.0}])
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            self._write(tmp, snap, vint)
            gens = self._load(tmp)
        self.assertEqual(len(gens), 1)
        self.assertEqual(gens[0].unit_id, "99001_U2")
        self.assertEqual(gens[0].pmax_mw, 155.0)

    def test_oa_unit_oa_in_vintage_stays_dropped(self):
        # The rule-13 hinge: OA status alone never re-carries capacity. A unit
        # OA in its own year-matched vintage genuinely sat idle -> stays out.
        snap = _frame([{}, {"generator_id": "U2", "status": "OA"}])
        vint = _frame([{}, {"generator_id": "U2", "status": "OA"}])
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            self._write(tmp, snap, vint)
            self.assertEqual(self._load(tmp), [])

    def test_missing_vintage_carries_nothing(self):
        # The 2025 leg (no committed vintage): the oracle cannot fire -> the
        # accepted under-carry, never a fallback to OA-status-alone.
        snap = _frame([{}, {"generator_id": "U2", "status": "OA"}])
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            self._write(tmp, snap, vintage=None)
            self.assertEqual(self._load(tmp), [])

    def test_year_none_carries_nothing(self):
        snap = _frame([{}, {"generator_id": "U2", "status": "OA"}])
        vint = _frame([{}, {"generator_id": "U2"}])
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            self._write(tmp, snap, vint)
            self.assertEqual(self._load(tmp, year=None), [])

    def test_op_units_never_duplicated(self):
        # Per-unit injection: the surviving OP unit is already loaded from the
        # snapshot and must not come back through this channel.
        snap = _frame([{}, {"generator_id": "U2", "status": "OA"}])
        vint = _frame([{}, {"generator_id": "U2"}])
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            self._write(tmp, snap, vint)
            gens = self._load(tmp)
        self.assertEqual([g.unit_id for g in gens], ["99001_U2"])

    def test_other_ba_rows_excluded(self):
        snap = _frame(
            [
                {},
                {
                    "generator_id": "U2",
                    "status": "OA",
                    "balancing_authority_code": "ERCO",
                },
            ]
        )
        vint = _frame([{}, {"generator_id": "U2", "balancing_authority_code": "ERCO"}])
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            self._write(tmp, snap, vint)
            self.assertEqual(self._load(tmp), [])

    def test_gate_default_off(self):
        # The channel is gated default-off in ScenarioConfig (rule 24: the
        # tunable is on-registry; a default run is byte-identical).
        self.assertFalse(ScenarioConfig().carry_operating_mothballs)


class TestCottonwoodRealData(unittest.TestCase):
    """The committed-data case the charter documents (plant 55358)."""

    def test_miso_2023_carries_cottonwood_oa_units(self):
        gens = load_mothballed_but_operating("MISO", year=2023)
        cw = [g for g in gens if int(g.plant_code) == 55358]
        self.assertEqual(
            sorted(g.unit_id for g in cw),
            ["55358_CT1", "55358_CT2", "55358_ST1", "55358_ST2"],
        )
        for g in cw:
            self.assertEqual(g.fuel_type, "gas_cc")
            self.assertEqual(g.plant_group, "CC_REGULAR")
            self.assertEqual(g.zone, "MISO-South")
            self.assertIsNone(g.retirement_year)
        # ~572.6 MW of year-matched (vintage_2023) net-summer capability.
        self.assertAlmostEqual(sum(g.pmax_mw for g in cw), 572.6, delta=1.0)

    def test_carried_units_absent_from_operable_fleet(self):
        # The whole point: the OP filter drops these units from the canonical
        # fleet, so this channel is their only way in (no double-count).
        operable = load_fleet_from_csv("MISO")
        cw_ids = {g.unit_id for g in operable if int(g.plant_code) == 55358}
        self.assertEqual(cw_ids, {"55358_CT3", "55358_CT4", "55358_ST3", "55358_ST4"})

    def test_miso_2025_no_vintage_carries_nothing(self):
        # No committed vintage_2025 (the canonical snapshot IS the 2025 Early
        # Release): the accepted 2025 under-carry, charter §10 owner default.
        self.assertEqual(load_mothballed_but_operating("MISO", year=2025), [])


if __name__ == "__main__":
    unittest.main()
