"""Tests for the combined-cycle STEAM-part capacity repair (miso-126).

``ScenarioConfig.cc_steam_part_capacity``. EIA-860's ``Energy Source 1`` on a
``CA`` prime-mover row names the block's SUPPLEMENTARY / duct fuel, not its
primary energy input, which arrives as its own combustion turbines' exhaust —
so a duct-fired steam part reports ``BFG`` / ``OG`` / ``DFO``,
``fleet.eia860._map_fuel_type`` returns ``None``, the row is skipped and its
capacity never reaches the LP.

Four seams:

1. the **predicate** (:func:`_cc_steam_part_generators`) — each clause of the
   conjunction, including the vintage clause and the empty-source no-op;
2. the **classifier** (:func:`classify_plant`) — the ``cc_steam_part`` argument
   is a strict widening and is default-off;
3. the **row loop** (:func:`_rows_to_generators`) — byte-identical off, restores
   the steam part on, and NEVER reclassifies a row that already resolves (the
   1004 Edwardsport case: it matches the predicate but its technology string
   carries "coal", so it is already in the fleet as ``COAL``);
4. the **backcast wiring** — generalising the nyiso-89 guard so that EVERY
   ScenarioConfig-backed fleet-sourcing flag is forwarded at the backcast's own
   copy of the bin synthesis, not just the one flag that was pinned when the
   guard was written. (3) and (4) are the ones that matter: this session's first
   arm-B solve came back EXACTLY inert because the flag was not forwarded at
   that call site — the arm reads as "the mechanism is inert" when the truth is
   "the mechanism was never applied".
"""

from __future__ import annotations

import ast
import inspect
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from market_sim.config.plant_taxonomy import (
    CC_STEAM_PART_REPAIR_ISOS,
    classify_plant,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet.eia860 import (
    _cc_steam_part_generators,
    _rows_to_generators,
)

_OPERABLE_COLUMNS = [
    "Plant Code",
    "Generator ID",
    "Prime Mover",
    "Energy Source 1",
    "Unit Code",
    "Operating Year",
]


def _operable(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=_OPERABLE_COLUMNS)


def _write(tmp: Path, frame: pd.DataFrame) -> Path:
    frame.to_parquet(tmp / "eia860_generator_operable.parquet")
    return tmp


class TestPredicate(unittest.TestCase):
    """Each clause of the steam-part conjunction, on synthetic EIA-860 rows."""

    def _resolve(self, rows: list[tuple]) -> set[tuple[int, str]]:
        with TemporaryDirectory() as td:
            path = _write(Path(td), _operable(rows))
            _cc_steam_part_generators.cache_clear()
            try:
                return set(_cc_steam_part_generators(path))
            finally:
                _cc_steam_part_generators.cache_clear()

    def test_admits_a_duct_fired_steam_part(self) -> None:
        """The 55088 Dearborn shape: CA/BFG sharing a unit code with NG CTs."""
        got = self._resolve(
            [
                (55088, "GT 1", "CT", "NG", "SINT", 2001),
                (55088, "GT2", "CT", "NG", "SINT", 2001),
                (55088, "GTP1", "GT", "NG", None, 1999),
                (55088, "ST1", "CA", "BFG", "SINT", 2001),
            ]
        )
        self.assertEqual(got, {(55088, "ST1")})

    def test_rejects_a_steam_part_older_than_its_own_turbines(self) -> None:
        """The 50973 Motiva shape — a refinery steam header, not a CC block.

        A heat-recovery steam generator is commissioned with or after the gas
        turbines whose exhaust drives it, so a "steam part" predating every
        turbine that supposedly drives it is a plant-wide steam header sharing
        a unit-code label.
        """
        got = self._resolve(
            [
                (50973, "GN31", "CA", "OG", "BLK1", 1962),
                (50973, "GN32", "CA", "OG", "BLK1", 1957),
                (50973, "GN33", "CA", "OG", "BLK1", 1978),
                (50973, "GN35", "CT", "NG", "BLK1", 1983),
                (50973, "GN41", "CT", "NG", "BLK1", 2011),
            ]
        )
        self.assertEqual(got, set())

    def test_admits_same_year_as_its_turbines(self) -> None:
        """The clause is `not older`, not `strictly newer` — 55088 is same-year."""
        got = self._resolve(
            [
                (1, "CT1", "CT", "NG", "B1", 2001),
                (1, "ST1", "CA", "BFG", "B1", 2001),
            ]
        )
        self.assertEqual(got, {(1, "ST1")})

    def test_rejects_a_standalone_without_ng_ct_siblings(self) -> None:
        """A CA row with no NG CT sibling in its block is not a CC steam part."""
        got = self._resolve(
            [
                (2, "ST1", "CA", "LFG", "B1", 2005),
                (2, "GT1", "GT", "NG", None, 2005),  # GT, not CT, and no unit code
            ]
        )
        self.assertEqual(got, set())

    def test_rejects_a_ca_row_with_no_unit_code(self) -> None:
        got = self._resolve(
            [
                (3, "CT1", "CT", "NG", "B1", 1990),
                (3, "ST1", "CA", "OG", None, 1990),
            ]
        )
        self.assertEqual(got, set())

    def test_rejects_an_ng_coded_ca_row(self) -> None:
        """An NG-coded CA row already classes correctly and needs no repair."""
        got = self._resolve(
            [
                (4, "CT1", "CT", "NG", "B1", 1990),
                (4, "ST1", "CA", "NG", "B1", 1990),
            ]
        )
        self.assertEqual(got, set())

    def test_absent_sheet_is_a_no_op(self) -> None:
        with TemporaryDirectory() as td:
            _cc_steam_part_generators.cache_clear()
            self.assertEqual(_cc_steam_part_generators(Path(td)), frozenset())
            _cc_steam_part_generators.cache_clear()


class TestClassifier(unittest.TestCase):
    """``classify_plant``'s ``cc_steam_part`` argument."""

    def test_default_off_leaves_a_duct_fuel_row_in_other(self) -> None:
        self.assertEqual(classify_plant("BFG", "CA", False, 55088), "OTHER")

    def test_on_classes_the_steam_part_as_combined_cycle(self) -> None:
        self.assertEqual(
            classify_plant("BFG", "CA", False, 55088, cc_steam_part=True),
            "CC_REGULAR",
        )
        self.assertEqual(
            classify_plant("BFG", "CA", True, 55088, cc_steam_part=True),
            "CC_CHP",
        )

    def test_it_is_a_strict_widening_for_ng_rows(self) -> None:
        """An NG CA row lands on the same class either way."""
        for chp in (False, True):
            self.assertEqual(
                classify_plant("NG", "CA", chp, 1, cc_steam_part=False),
                classify_plant("NG", "CA", chp, 1, cc_steam_part=True),
            )

    def test_it_does_not_touch_non_ca_prime_movers(self) -> None:
        """The argument is gated on the prime mover, so a coal ST is unmoved."""
        self.assertEqual(
            classify_plant("BIT", "ST", False, 1, cc_steam_part=True),
            classify_plant("BIT", "ST", False, 1),
        )


class TestRowLoop(unittest.TestCase):
    """``_rows_to_generators``: off is byte-identical, on restores the machine."""

    def _frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "plant_id": 55088,
                    "generator_id": "GT 1",
                    "plant_name": "Dearborn",
                    "state": "MI",
                    "technology": "Natural Gas Fired Combined Cycle",
                    "energy_source": "NG",
                    "prime_mover": "CT",
                    "nameplate_capacity_mw": 157.3,
                    "net_summer_capacity_mw": 175.0,
                    "operating_year": 2001,
                    "status": "OP",
                    "heat_rate": 6.3464,
                    "chp": "Y",
                },
                {
                    "plant_id": 55088,
                    "generator_id": "ST1",
                    "plant_name": "Dearborn",
                    "state": "MI",
                    "technology": "Other Gases",
                    "energy_source": "BFG",
                    "prime_mover": "CA",
                    "nameplate_capacity_mw": 238.0,
                    "net_summer_capacity_mw": 250.0,
                    "operating_year": 2001,
                    "status": "OP",
                    "heat_rate": 6.3464,
                    "chp": "Y",
                },
                {
                    # 1004 Edwardsport: matches the predicate, but its
                    # technology string carries "coal", so _map_fuel_type
                    # already resolves it and it must NOT be re-bucketed.
                    "plant_id": 1004,
                    "generator_id": "ST",
                    "plant_name": "Edwardsport",
                    "state": "IN",
                    "technology": "Coal Integrated Gasification Combined Cycle",
                    "energy_source": "SGC",
                    "prime_mover": "CA",
                    "nameplate_capacity_mw": 331.5,
                    "net_summer_capacity_mw": 555.0,
                    "operating_year": 2013,
                    "status": "OP",
                    "heat_rate": 8.8,
                    "chp": "N",
                },
            ]
        )

    def _run(self, steam_parts: set[tuple[int, str]], flag: bool) -> list:
        import market_sim.data.fleet.eia860 as mod

        original = mod.cc_steam_part_generators
        mod.cc_steam_part_generators = lambda *a, **k: frozenset(steam_parts)
        try:
            return _rows_to_generators(
                self._frame(), "MISO", None, cc_steam_part_capacity=flag
            )
        finally:
            mod.cc_steam_part_generators = original

    def test_off_drops_the_steam_part(self) -> None:
        gens = self._run({(55088, "ST1"), (1004, "ST")}, flag=False)
        ids = {g.unit_id for g in gens}
        self.assertNotIn("55088_ST1", ids)
        self.assertIn("55088_GT 1", ids)

    def test_on_restores_it_as_cc_chp_at_the_block_heat_rate(self) -> None:
        gens = self._run({(55088, "ST1"), (1004, "ST")}, flag=True)
        by_id = {g.unit_id: g for g in gens}
        self.assertIn("55088_ST1", by_id)
        st1 = by_id["55088_ST1"]
        self.assertEqual(st1.plant_group, "CC_CHP")
        self.assertEqual(st1.fuel_type, "gas_cc")
        self.assertAlmostEqual(st1.pmax_mw, 250.0)
        # the block's rate, i.e. exactly what its CT siblings carry
        self.assertAlmostEqual(st1.heat_rate, by_id["55088_GT 1"].heat_rate)

    def test_it_never_reclassifies_an_already_represented_row(self) -> None:
        """1004 Edwardsport stays COAL whether the flag is on or off."""
        for flag in (False, True):
            by_id = {
                g.unit_id: g for g in self._run({(55088, "ST1"), (1004, "ST")}, flag)
            }
            self.assertIn("1004_ST", by_id, f"flag={flag}")
            self.assertEqual(by_id["1004_ST"].plant_group, "COAL_BIT", f"flag={flag}")
            self.assertEqual(by_id["1004_ST"].fuel_type, "coal", f"flag={flag}")

    def test_an_empty_predicate_is_byte_identical(self) -> None:
        off = self._run(set(), flag=False)
        on = self._run(set(), flag=True)
        self.assertEqual(
            [(g.unit_id, g.plant_group, g.pmax_mw, g.heat_rate) for g in off],
            [(g.unit_id, g.plant_group, g.pmax_mw, g.heat_rate) for g in on],
        )


class TestIsoScope(unittest.TestCase):
    """Rule 25 [R-ISO-SCOPE]: the repair is gated to verified ISOs only."""

    def test_only_miso_is_enrolled(self) -> None:
        self.assertEqual(CC_STEAM_PART_REPAIR_ISOS, frozenset({"MISO"}))

    def test_the_flag_defaults_off(self) -> None:
        self.assertIs(ScenarioConfig(iso="MISO").cc_steam_part_capacity, False)


class TestBackcastFleetSourcing(unittest.TestCase):
    """EVERY ScenarioConfig-backed fleet-sourcing flag must be forwarded.

    ``scripts/run_calibration.py::run_year`` does not call
    ``fleet.assembly.load_or_synthesize_bins`` — it inlines an equivalent
    ``fleet_to_bins(load_fleet_from_csv(...))`` for the non-ERCOT per-plant
    ISOs. A fleet-sourcing flag forwarded in ``assembly`` but not there is
    silently ignored by every calibration solve while ``run_config.json`` still
    records it as on: the arm comes back byte-identical to its control and
    reads as "the mechanism is inert" rather than "the mechanism was never
    applied".

    ``tests/unit/data/test_measured_ct_heat_rates.py`` pins that call site for
    ``measured_ct_heat_rates`` — the flag that hit this on nyiso-89. It did not
    stop ``cc_steam_part_capacity`` hitting exactly the same wall at miso-126,
    because a per-flag pin only protects the flag someone remembered to add.
    This is the general form: any keyword ``load_fleet_from_csv`` accepts that
    is ALSO a ``ScenarioConfig`` field is a fleet-sourcing flag, and the
    backcast must forward all of them. A new one is caught the day it lands,
    without anyone editing this test.
    """

    def test_backcast_forwards_every_fleet_sourcing_flag(self) -> None:
        from market_sim.data.fleet import load_fleet_from_csv

        cfg_fields = set(ScenarioConfig(iso="MISO").__dataclass_fields__)
        # A fleet-sourcing FLAG is a boolean-defaulted keyword of
        # load_fleet_from_csv that is also a ScenarioConfig field. The bool
        # requirement excludes the identity/locator arguments (``iso``,
        # ``iso_config``, ``data_dir``, ``year``), which are passed positionally
        # or resolved per-year and are not mechanism arming; the cfg_fields
        # requirement excludes the two loader-internal switches no scenario
        # carries (``apply_cc_summer_guard``,
        # ``apply_chp_steam_credit_correction``).
        required = {
            name
            for name, param in inspect.signature(load_fleet_from_csv).parameters.items()
            if name in cfg_fields and isinstance(param.default, bool)
        }
        self.assertTrue(
            required,
            "load_fleet_from_csv exposes no ScenarioConfig-backed flags — the "
            "guard would be vacuous",
        )

        source = Path("scripts/run_calibration.py").read_text()
        calls = [
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "load_fleet_from_csv"
        ]
        self.assertTrue(calls, "run_calibration.py no longer loads the fleet")
        for call in calls:
            forwarded = {kw.arg for kw in call.keywords}
            missing = sorted(required - forwarded)
            self.assertFalse(
                missing,
                f"scripts/run_calibration.py:{call.lineno} loads the fleet "
                f"without forwarding {missing} — the backcast would silently "
                "solve without them while run_config.json records them as on "
                "(the nyiso-89 / miso-126 regression class)",
            )


if __name__ == "__main__":
    unittest.main()
