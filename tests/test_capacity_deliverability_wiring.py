"""Tests for the capacity-deliverability reader and its model wiring.

Trivial case first: a synthetic 1-area→1-zone clean fixture in a tmp CLEAN_DIR
exercises the reader and the per-zone headroom gate; then the gate's effect on
the capacity screens (retirement / new-entry / storage) and the seam-import-limit
override are checked. The mechanism is judged on structural behaviour — a long
zone loses its capacity payment, a short zone keeps it — NOT on any backcast MAE
(repo rule #1). Flag-off no-op is asserted so keepers are unaffected.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import capacity_deliverability as capdel
from market_sim.data.fleet import Generator
from market_sim.model.capacity import (
    _zone_is_long,
    capacity_revenue_per_mw_yr,
    deliverability_headroom_by_zone,
)
from market_sim.model.storage import _deliverability_capacity_factor
from market_sim.model.transmission import (
    apply_deliverability_seam_limit,
    extend_with_import_node,
)
from scripts.lib import clean_io
from scripts.lib.clean_io import write_clean

_COLS = [
    "iso",
    "area",
    "area_type",
    "delivery_year",
    "season",
    "metric",
    "value_mw",
    "value_pu",
    "source_doc",
    "source_page",
]


def _row(iso, area, area_type, dy, metric, mw):
    return {
        "iso": iso,
        "area": area,
        "area_type": area_type,
        "delivery_year": dy,
        "season": "annual",
        "metric": metric,
        "value_mw": mw,
        "value_pu": None,
        "source_doc": "fixture",
        "source_page": "1",
    }


class TestReaderTrivial(unittest.TestCase):
    """1 area, 1 zone, 1 delivery year — the smallest real read."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self._orig = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "clean"
        # One PJM LDA (COMED ↔ PJM_ComEd) with a requirement + import_limit.
        df = pd.DataFrame(
            [
                _row("PJM", "COMED", "lda", "2024/2025", "requirement", 1000.0),
                _row("PJM", "COMED", "lda", "2024/2025", "import_limit", 400.0),
            ],
            columns=_COLS,
        )
        df["value_mw"] = df["value_mw"].astype("float64")
        df["value_pu"] = df["value_pu"].astype("float64")
        write_clean(df, "capacity-deliverability", iso="PJM")

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig
        self._tmp.cleanup()

    def test_requirement_and_import_reader(self) -> None:
        dy = capdel.resolve_delivery_year("PJM", 2024)
        self.assertEqual(dy, "2024/2025")
        self.assertEqual(capdel.requirement_by_area("PJM", dy), {"COMED": 1000.0})
        self.assertEqual(capdel.import_limit_by_area("PJM", dy), {"COMED": 400.0})
        # ERCOT has no partition → empty (energy-only, no analog).
        self.assertEqual(capdel.requirement_by_area("ERCOT", "2024"), {})

    def test_headroom_short_and_long(self) -> None:
        cfg = ScenarioConfig(iso="PJM", capacity_deliverability_limits=True)
        # Empty fleet: deliverable = 0 firm + 400 import − 1000 req = −600 (short).
        h_short = deliverability_headroom_by_zone("PJM", 2024, [], cfg)
        self.assertAlmostEqual(h_short["PJM_ComEd"], -600.0)
        self.assertFalse(_zone_is_long(h_short, "PJM_ComEd"))
        # 2 GW of firm gas in ComEd: deliverable ≫ requirement → long.
        fleet = [
            Generator(
                unit_id="g",
                name="g",
                zone="PJM_ComEd",
                fuel_type="gas_cc",
                pmax_mw=2000.0,
                pmin_mw=0.0,
                heat_rate=7.0,
                eford=0.05,
            )
        ]
        h_long = deliverability_headroom_by_zone("PJM", 2024, fleet, cfg)
        self.assertGreater(h_long["PJM_ComEd"], 0.0)
        self.assertTrue(_zone_is_long(h_long, "PJM_ComEd"))

    def test_flag_off_is_noop(self) -> None:
        cfg = ScenarioConfig(iso="PJM", capacity_deliverability_limits=False)
        self.assertEqual(deliverability_headroom_by_zone("PJM", 2024, [], cfg), {})


class TestGateBehaviour(unittest.TestCase):
    """The gate must collapse capacity value only where a zone is long."""

    def test_zone_is_long_predicate(self) -> None:
        self.assertFalse(_zone_is_long(None, "Z"))  # flag off
        self.assertFalse(_zone_is_long({}, "Z"))
        self.assertFalse(_zone_is_long({"Z": -10.0}, "Z"))  # short
        self.assertTrue(_zone_is_long({"Z": 10.0}, "Z"))  # long
        self.assertFalse(_zone_is_long({"Z": 10.0}, "OTHER"))  # zone absent

    def test_capacity_payment_positive_in_capacity_market(self) -> None:
        # Sanity: the payment being gated is non-zero for a capacity-market ISO,
        # so zeroing it in a long zone is a real effect.
        self.assertGreater(capacity_revenue_per_mw_yr("PJM", "gas_cc", 0.05), 0.0)

    def test_storage_factor_short_full_long_derated(self) -> None:
        iso_config = get_iso_config("PJM")
        # No headroom → full credit (no-op).
        self.assertEqual(_deliverability_capacity_factor(iso_config, None), 1.0)
        self.assertEqual(_deliverability_capacity_factor(iso_config, {}), 1.0)
        # Every requirement-carrying zone long → factor 0 (unlisted zones treated
        # as unconstrained; here list ALL load zones as long).
        all_long = {z.name: 5000.0 for z in iso_config.zones if z.load_share > 0}
        self.assertEqual(_deliverability_capacity_factor(iso_config, all_long), 0.0)
        # A short zone restores a positive share of the credit.
        mixed = dict(all_long)
        big = max(iso_config.zones, key=lambda z: z.load_share)
        mixed[big.name] = -1000.0
        f = _deliverability_capacity_factor(iso_config, mixed)
        self.assertTrue(0.0 < f <= 1.0)


class TestSeamImportOverride(unittest.TestCase):
    """Part A: per-area seam import limit replaces the simultaneous scalar."""

    def test_caiso_seam_override(self) -> None:
        iso_config = get_iso_config("CAISO")
        # Baked-in WECC_import_simultaneous cap.
        orig = next(
            lim.cap_mw
            for lim in iso_config.interface_limits
            if lim.name == "WECC_import_simultaneous"
        )
        updated = apply_deliverability_seam_limit(iso_config, "CAISO", orig + 5000.0)
        new_cap = next(
            lim.cap_mw
            for lim in updated.interface_limits
            if lim.name == "WECC_import_simultaneous"
        )
        self.assertEqual(new_cap, orig + 5000.0)

    def test_noop_paths(self) -> None:
        iso_config = get_iso_config("CAISO")
        self.assertIs(
            apply_deliverability_seam_limit(iso_config, "CAISO", None), iso_config
        )
        self.assertIs(
            apply_deliverability_seam_limit(iso_config, "CAISO", 0.0), iso_config
        )
        # PJM without an extended import node has no import-origin interface limit.
        pjm = get_iso_config("PJM")
        self.assertIs(apply_deliverability_seam_limit(pjm, "PJM", 9999.0), pjm)

    def test_pjm_extended_node_override(self) -> None:
        # After extend_with_import_node, PJM has a PJM_simultaneous_import limit
        # whose links all originate at the import node → override applies.
        pjm = extend_with_import_node(get_iso_config("PJM"))
        updated = apply_deliverability_seam_limit(pjm, "PJM", 12345.0)
        caps = {lim.name: lim.cap_mw for lim in updated.interface_limits}
        self.assertEqual(caps.get("PJM_simultaneous_import"), 12345.0)


if __name__ == "__main__":
    unittest.main()
