"""Tests for the combined-cycle STEAM-part RE-CLASS (neiso-83).

``ScenarioConfig.cc_steam_part_reclass``. The sibling of the miso-126 capacity
repair (``tests/unit/data/test_cc_steam_part_capacity.py``) on the SAME
predicate's other half, and the distinction between them is the whole point:

* the **repair** restores a ``CA`` steam part ``_map_fuel_type`` DROPS —
  ``BFG`` / ``OG`` return ``None`` — so capacity is ADDED;
* the **re-class** moves a ``CA`` steam part ``_map_fuel_type`` CARRIES under a
  NON-gas fuel taken from the row's own duct / legacy ``Energy Source 1``
  (``DFO`` → ``oil``), so capacity is UNCHANGED and what moves is the class,
  the fuel, the VOM, the CO2 rate and the forced-outage rate.

Re-classing is precisely the operation the repair's ``fuel_type is None`` gate
forbids (miso-125 §6: MISO 1004 Edwardsport's ``CA`` / ``SGC`` row matches the
predicate but is a real 555 MW IGCC machine the model carries as ``COAL``), so
the two mechanisms carry separate flags and separate ISO registries. The tests
below pin that separation from both sides.
"""

from __future__ import annotations

import unittest

import pandas as pd

from market_sim.config.plant_taxonomy import (
    CC_STEAM_PART_RECLASS_ISOS,
    CC_STEAM_PART_REPAIR_ISOS,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet.eia860 import _map_fuel_type, _rows_to_generators


def _stony_brook_frame() -> pd.DataFrame:
    """The NEISO 6081 Stony Brook block, as EIA-860 reports it.

    Three ``CT`` / ``NG`` combustion turbines and one ``CA`` steam part whose
    ``Energy Source 1`` is ``DFO`` — the shape this mechanism exists for — plus
    one of the plant's genuine standalone distillate ``GT`` peakers, which must
    never move (the plant really does host oil machines; only ``CA1`` is in
    question).
    """
    common = {
        "plant_name": "Stony Brook",
        "state": "MA",
        "operating_year": 1981,
        "status": "OP",
        "heat_rate": 10.60617891,
        "chp": "N",
    }
    return pd.DataFrame(
        [
            {
                **common,
                "plant_id": 6081,
                "generator_id": "CT1",
                "technology": "Natural Gas Fired Combined Cycle",
                "energy_source": "NG",
                "prime_mover": "CT",
                "nameplate_capacity_mw": 85.0,
                "net_summer_capacity_mw": 69.7,
            },
            {
                **common,
                "plant_id": 6081,
                "generator_id": "CT2",
                "technology": "Natural Gas Fired Combined Cycle",
                "energy_source": "NG",
                "prime_mover": "CT",
                "nameplate_capacity_mw": 85.0,
                "net_summer_capacity_mw": 69.7,
            },
            {
                **common,
                "plant_id": 6081,
                "generator_id": "CT3",
                "technology": "Natural Gas Fired Combined Cycle",
                "energy_source": "NG",
                "prime_mover": "CT",
                "nameplate_capacity_mw": 85.0,
                "net_summer_capacity_mw": 69.7,
            },
            {
                **common,
                "plant_id": 6081,
                "generator_id": "CA1",
                "technology": "Petroleum Liquids",
                "energy_source": "DFO",
                "prime_mover": "CA",
                "nameplate_capacity_mw": 105.0,
                "net_summer_capacity_mw": 96.0,
            },
            {
                # A REAL distillate peaker at the same plant. The trap this
                # mechanism must not fall into is a plant-scoped fix.
                **common,
                "plant_id": 6081,
                "generator_id": "1",
                "technology": "Petroleum Liquids",
                "energy_source": "DFO",
                "prime_mover": "GT",
                "nameplate_capacity_mw": 85.0,
                "net_summer_capacity_mw": 65.0,
                "operating_year": 1982,
            },
            {
                # 1004 Edwardsport: matches the predicate, resolves to `coal`,
                # and is a genuine 555 MW IGCC machine. It is MISO's, and MISO
                # is not in the re-class registry — but even if the predicate is
                # forced to include it here, the ISO gate must keep it COAL.
                **common,
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
            },
        ]
    )


def _run(iso: str, flag: bool, parts: set[tuple[int, str]] | None = None) -> list:
    """Build the synthetic fleet with the predicate pinned to ``parts``."""
    import market_sim.data.fleet.eia860 as mod

    resolved = {(6081, "CA1"), (1004, "ST")} if parts is None else parts
    original = mod.cc_steam_part_generators
    mod.cc_steam_part_generators = lambda *a, **k: frozenset(resolved)
    try:
        return _rows_to_generators(
            _stony_brook_frame(), iso, None, cc_steam_part_reclass=flag
        )
    finally:
        mod.cc_steam_part_generators = original


class TestFuelMapPremise(unittest.TestCase):
    """The row is CARRIED, not dropped — which is why the repair cannot reach it."""

    def test_a_dfo_coded_ca_row_resolves_to_oil(self) -> None:
        self.assertEqual(_map_fuel_type("Petroleum Liquids", "DFO", "CA"), "oil")

    def test_a_bfg_coded_ca_row_is_dropped(self) -> None:
        """The repair's population: `None` is what makes a row restorable."""
        self.assertIsNone(_map_fuel_type("Other Gases", "BFG", "CA"))

    def test_an_ng_coded_ca_row_already_resolves_to_gas_cc(self) -> None:
        """Only the energy-source code separates CA1 from an ordinary CC steam part."""
        self.assertEqual(
            _map_fuel_type("Natural Gas Fired Combined Cycle", "NG", "CA"), "gas_cc"
        )


class TestRowLoop(unittest.TestCase):
    """``_rows_to_generators``: byte-identical off, one unit moved on."""

    def test_off_carries_the_steam_part_as_oil(self) -> None:
        by_id = {g.unit_id: g for g in _run("NEISO", flag=False)}
        self.assertIn("6081_CA1", by_id)
        self.assertEqual(by_id["6081_CA1"].fuel_type, "oil")
        self.assertEqual(by_id["6081_CA1"].plant_group, "")

    def test_on_reclasses_it_onto_its_own_block(self) -> None:
        by_id = {g.unit_id: g for g in _run("NEISO", flag=True)}
        ca1 = by_id["6081_CA1"]
        self.assertEqual(ca1.fuel_type, "gas_cc")
        self.assertEqual(ca1.plant_group, "CC_REGULAR")
        # The block's own rate — exactly what its CT siblings carry, and already
        # block-denominated, so charging every block MW this rate reproduces the
        # block's total fuel burn rather than double-counting the CT-metered
        # heat input.
        self.assertAlmostEqual(ca1.heat_rate, by_id["6081_CT1"].heat_rate)

    def test_capacity_is_conserved(self) -> None:
        """Contrast the repair, which ADDS capacity. This one moves a label.

        Summed over plant 6081 only: the frame also carries MISO's Edwardsport
        row so the ISO-scope tests below can reach it, and that row's EIA-860
        summer capacity (555.0) exceeds its nameplate (331.5), so once it is
        re-classed to gas the merchant-CC summer guard reconciles it. That is
        the guard doing its job on a row this ISO's frame never really holds —
        not a capacity leak in the mechanism.
        """
        off = sum(
            float(g.pmax_mw) for g in _run("NEISO", flag=False) if g.plant_code == 6081
        )
        on = sum(
            float(g.pmax_mw) for g in _run("NEISO", flag=True) if g.plant_code == 6081
        )
        self.assertAlmostEqual(off, on)
        self.assertAlmostEqual(off, 3 * 69.7 + 96.0 + 65.0)

    def test_the_summer_guard_does_not_fire_on_the_real_block(self) -> None:
        """6081's block sums to 305.1 MW against a 360.0 MW nameplate bound."""
        by_id = {g.unit_id: g for g in _run("NEISO", flag=True)}
        self.assertAlmostEqual(by_id["6081_CA1"].pmax_mw, 96.0)
        for gid in ("6081_CT1", "6081_CT2", "6081_CT3"):
            self.assertAlmostEqual(by_id[gid].pmax_mw, 69.7)

    def test_the_plants_real_oil_peaker_never_moves(self) -> None:
        """A plant-scoped fix would destroy real distillate capacity."""
        for flag in (False, True):
            by_id = {g.unit_id: g for g in _run("NEISO", flag=flag)}
            self.assertEqual(by_id["6081_1"].fuel_type, "oil", f"flag={flag}")
            self.assertEqual(by_id["6081_1"].plant_group, "", f"flag={flag}")

    def test_the_ct_siblings_are_untouched(self) -> None:
        for flag in (False, True):
            by_id = {g.unit_id: g for g in _run("NEISO", flag=flag)}
            for gid in ("6081_CT1", "6081_CT2", "6081_CT3"):
                self.assertEqual(by_id[gid].fuel_type, "gas_cc", f"{gid} flag={flag}")
                self.assertEqual(
                    by_id[gid].plant_group, "CC_REGULAR", f"{gid} flag={flag}"
                )

    def test_an_empty_predicate_is_byte_identical(self) -> None:
        off = _run("NEISO", flag=False, parts=set())
        on = _run("NEISO", flag=True, parts=set())
        self.assertEqual(
            [(g.unit_id, g.fuel_type, g.plant_group, g.pmax_mw) for g in off],
            [(g.unit_id, g.fuel_type, g.plant_group, g.pmax_mw) for g in on],
        )


class TestIsoScope(unittest.TestCase):
    """Rule 25 [R-ISO-SCOPE]: NEISO's verdict fills nobody else's cell."""

    def test_only_neiso_is_enrolled(self) -> None:
        self.assertEqual(CC_STEAM_PART_RECLASS_ISOS, frozenset({"NEISO"}))

    def test_the_two_registries_are_disjoint(self) -> None:
        """Separate objects, separate populations, separate gates."""
        self.assertFalse(CC_STEAM_PART_RECLASS_ISOS & CC_STEAM_PART_REPAIR_ISOS)

    def test_edwardsport_stays_coal_in_miso(self) -> None:
        """MISO is not enrolled, so the armed flag cannot reach its IGCC ST."""
        for flag in (False, True):
            by_id = {g.unit_id: g for g in _run("MISO", flag=flag)}
            self.assertEqual(by_id["1004_ST"].fuel_type, "coal", f"flag={flag}")
            self.assertEqual(by_id["1004_ST"].plant_group, "COAL_BIT", f"flag={flag}")

    def test_edwardsport_stays_coal_even_in_an_enrolled_iso(self) -> None:
        """Belt and braces: the ISO gate is the guard, but the row is MISO's.

        If Edwardsport were ever mis-attributed to an enrolled ISO's frame the
        re-class WOULD move it, which is exactly why the registry — not a fuel
        allow-list — is the mechanism's gate, and why MISO is deliberately
        absent from it. This test documents the reachability rather than
        asserting a guard the code does not have.
        """
        by_id = {g.unit_id: g for g in _run("NEISO", flag=True)}
        self.assertEqual(by_id["1004_ST"].fuel_type, "gas_cc")

    def test_the_flag_defaults_off(self) -> None:
        self.assertIs(ScenarioConfig(iso="NEISO").cc_steam_part_reclass, False)


class TestRealNeisoFleet(unittest.TestCase):
    """The committed EIA-860 data: NEISO's whole population is one row."""

    def test_neiso_moves_exactly_one_unit(self) -> None:
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.fleet import load_fleet_from_csv

        cfg = get_iso_config("NEISO")
        off = {g.unit_id: g.model_dump() for g in load_fleet_from_csv("NEISO", cfg)}
        on = {
            g.unit_id: g.model_dump()
            for g in load_fleet_from_csv("NEISO", cfg, cc_steam_part_reclass=True)
        }
        self.assertEqual(set(off), set(on))
        moved = sorted(u for u in off if off[u] != on[u])
        self.assertEqual(moved, ["6081_CA1"])
        self.assertEqual(off["6081_CA1"]["fuel_type"], "oil")
        self.assertEqual(on["6081_CA1"]["fuel_type"], "gas_cc")
        self.assertAlmostEqual(off["6081_CA1"]["pmax_mw"], on["6081_CA1"]["pmax_mw"])
        self.assertAlmostEqual(
            off["6081_CA1"]["heat_rate"], on["6081_CA1"]["heat_rate"]
        )

    def test_the_other_five_isos_are_byte_identical(self) -> None:
        """Rule 25 [R-ISO-SCOPE], proven by running it rather than reading it."""
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.fleet import load_fleet_from_csv

        for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO"):
            cfg = get_iso_config(iso)
            off = {g.unit_id: g.model_dump() for g in load_fleet_from_csv(iso, cfg)}
            on = {
                g.unit_id: g.model_dump()
                for g in load_fleet_from_csv(iso, cfg, cc_steam_part_reclass=True)
            }
            self.assertEqual(off, on, f"{iso} fleet moved under a NEISO-only flag")


if __name__ == "__main__":
    unittest.main()
