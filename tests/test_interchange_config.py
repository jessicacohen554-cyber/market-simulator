"""Tests for the unified InterchangeSpec system.

Verifies that ``get_interchange_spec`` + ``build_interchange_fleet`` produce
the same Generator lists as the legacy per-path builders, and that the spec
flags correctly route through the reference-price, corridor, and static-
tranche code paths.
"""

import unittest
from dataclasses import dataclass

from market_sim.config.interchange_config import (
    IMPORT_TRANCHES,
    IMPORT_ZONE,
    INTERFACE_NEIGHBORS,
    MISO_MANITOBA_FIRM_IMPORT_MW,
    MISO_MANITOBA_FIRM_IMPORT_NAME,
    MISO_MANITOBA_FIRM_IMPORT_OFFER,
    MISO_MANITOBA_FIRM_IMPORT_ZONE,
    InterchangeSpec,
    build_interchange_fleet,
    get_interchange_spec,
)


@dataclass
class _FakeConfig:
    """Minimal stand-in for ScenarioConfig."""

    reference_price_interface: bool = False
    caiso_per_hub_intertie: bool = False
    miso_firm_imports: bool = False
    nyiso_import_reconciliation: bool = False
    nyiso_forward_net_import_twh: float | None = None
    weather_year: int | None = None
    mode: str = "forecast"
    carbon_price: float = 0.0


class TestGetInterchangeSpec(unittest.TestCase):
    """``get_interchange_spec`` routes config flags to the right spec shape."""

    def test_ercot_gets_empty_spec(self):
        spec = get_interchange_spec(_FakeConfig(), "ERCOT")
        self.assertEqual(spec.iso, "ERCOT")
        self.assertEqual(spec.import_zone, "")
        self.assertEqual(build_interchange_fleet(spec), [])

    def test_pjm_static_tranches(self):
        spec = get_interchange_spec(_FakeConfig(), "PJM")
        self.assertEqual(spec.iso, "PJM")
        self.assertEqual(spec.import_zone, IMPORT_ZONE["PJM"])
        self.assertFalse(spec.use_reference_price)
        self.assertFalse(spec.use_corridors)
        self.assertGreater(len(spec.import_tranches), 0)

    def test_pjm_reference_price(self):
        cfg = _FakeConfig(reference_price_interface=True)
        spec = get_interchange_spec(cfg, "PJM")
        self.assertTrue(spec.use_reference_price)
        self.assertEqual(len(spec.import_tranches), 0)
        self.assertGreater(len(spec.neighbors), 0)

    def test_miso_firm_imports_flag(self):
        cfg = _FakeConfig(miso_firm_imports=True)
        spec = get_interchange_spec(cfg, "MISO")
        self.assertEqual(len(spec.firm_imports), 1)
        fi = spec.firm_imports[0]
        self.assertEqual(fi.name, MISO_MANITOBA_FIRM_IMPORT_NAME)
        self.assertEqual(fi.zone, MISO_MANITOBA_FIRM_IMPORT_ZONE)
        self.assertEqual(fi.capacity_mw, MISO_MANITOBA_FIRM_IMPORT_MW)
        self.assertEqual(fi.offer, MISO_MANITOBA_FIRM_IMPORT_OFFER)

    def test_miso_firm_imports_off_by_default(self):
        spec = get_interchange_spec(_FakeConfig(), "MISO")
        self.assertEqual(len(spec.firm_imports), 0)

    def test_nyiso_reconciliation(self):
        cfg = _FakeConfig(nyiso_import_reconciliation=True)
        spec = get_interchange_spec(cfg, "NYISO")
        self.assertIsNotNone(spec.monthly_reconciliation)
        self.assertEqual(spec.monthly_reconciliation.iso, "NYISO")

    def test_nyiso_reconciliation_off_for_non_nyiso(self):
        cfg = _FakeConfig(nyiso_import_reconciliation=True)
        spec = get_interchange_spec(cfg, "PJM")
        self.assertIsNone(spec.monthly_reconciliation)


class TestBuildInterchangeFleet(unittest.TestCase):
    """``build_interchange_fleet`` produces correct Generator lists."""

    def test_static_tranche_generators(self):
        spec = get_interchange_spec(_FakeConfig(), "PJM")
        gens = build_interchange_fleet(spec, border_carbon_per_mwh=0.0)
        self.assertGreater(len(gens), 0)
        import_gens = [g for g in gens if g.pmax_mw > 0]
        export_gens = [g for g in gens if g.pmin_mw < 0]
        self.assertGreater(len(import_gens), 0)
        self.assertGreater(len(export_gens), 0)
        for g in gens:
            self.assertEqual(g.fuel_type, "import")
            self.assertEqual(g.zone, IMPORT_ZONE["PJM"])

    def test_reference_price_generates_paired_import_export(self):
        cfg = _FakeConfig(reference_price_interface=True)
        spec = get_interchange_spec(cfg, "PJM")
        gens = build_interchange_fleet(spec)
        import_gens = [g for g in gens if g.pmax_mw > 0]
        export_gens = [g for g in gens if g.pmin_mw < 0]
        self.assertEqual(len(import_gens), len(export_gens))
        self.assertGreater(len(import_gens), 0)

    def test_firm_import_appended(self):
        cfg = _FakeConfig(miso_firm_imports=True)
        spec = get_interchange_spec(cfg, "MISO")
        gens = build_interchange_fleet(spec)
        firm = [g for g in gens if MISO_MANITOBA_FIRM_IMPORT_NAME in g.unit_id]
        self.assertEqual(len(firm), 1)
        self.assertEqual(firm[0].pmax_mw, MISO_MANITOBA_FIRM_IMPORT_MW)
        self.assertEqual(firm[0].vom, MISO_MANITOBA_FIRM_IMPORT_OFFER)

    def test_empty_zone_returns_no_gens(self):
        spec = InterchangeSpec(iso="ERCOT", import_zone="")
        self.assertEqual(build_interchange_fleet(spec), [])


class TestBackwardCompatReexports(unittest.TestCase):
    """Constants re-exported from constants.py still resolve."""

    def test_constants_reexports_match(self):
        from market_sim.config import constants

        self.assertIs(constants.IMPORT_TRANCHES, IMPORT_TRANCHES)
        self.assertIs(constants.INTERFACE_NEIGHBORS, INTERFACE_NEIGHBORS)
        self.assertIs(constants.IMPORT_ZONE, IMPORT_ZONE)


if __name__ == "__main__":
    unittest.main()
