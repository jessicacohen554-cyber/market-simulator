"""The dashboard payload's CHP add-back mirrors what the LP held out (nyiso-192).

``render_calibration_html`` adds a cogen's behind-the-meter host supply back
onto the MODEL series so the plant heatmap compares full plant to full CAMPD
plant. Under ``nyiso_chp_btm_measured`` the LP holds out the MEASURED per-plant
share (0 % at Sithe Independence 54547, fleet/assembly.py), so the add-back must
use the same measured share — nyiso-192 found the model-payload site falling
back to the 35 % sector default, which put +2.1 TWh/yr of flat phantom energy on
one plant and inflated the nyiso-190/191 plant-grain record 3x at its top row.
The bench side already passed the measured map; these tests pin BOTH sites.
"""

import importlib.util
import re
import unittest

from tests.helpers import REPO_ROOT

_SRC = REPO_ROOT / "scripts" / "render_calibration_html.py"


def _load(mod_name: str):
    spec = importlib.util.spec_from_file_location(mod_name, str(_SRC))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rch = _load("rch_chp_addback")


class TestBtmShareMeasuredSupersedesSector(unittest.TestCase):
    def test_measured_zero_share_is_zero_not_sector(self):
        # Sithe Independence: measured 0.0 must win over the merchant default.
        self.assertEqual(
            rch._btm_share(54547, "CC_CHP", "NYISO", measured={54547: 0.0}), 0.0
        )

    def test_measured_share_is_returned_verbatim(self):
        self.assertAlmostEqual(
            rch._btm_share(50006, "CC_CHP", "NYISO", measured={50006: 0.2221}),
            0.2221,
        )

    def test_plant_absent_from_measured_keeps_sector_default(self):
        with_map = rch._btm_share(54547, "CC_CHP", "NYISO", measured={1: 0.5})
        without = rch._btm_share(54547, "CC_CHP", "NYISO")
        self.assertEqual(with_map, without)
        self.assertGreater(without, 0.0)

    def test_non_chp_group_is_zero(self):
        self.assertEqual(
            rch._btm_share(2500, "ST_GAS", "NYISO", measured={2500: 0.9}), 0.0
        )


class TestPayloadSitesPassMeasuredMap(unittest.TestCase):
    """Source-level pin: every ``_btm_share(`` call site passes ``measured=``.

    The defect was a call-site omission, invisible to any unit test of
    ``_btm_share`` itself, so the guard reads the source: no bare call may
    survive, and the model-payload site must pass the RUN's hold-out map
    (``_btm_run_measured``), which is the measured map iff the run's
    ``nyiso_chp_btm_measured`` flag is on.
    """

    def test_every_call_site_passes_measured(self):
        src = _SRC.read_text()
        calls = [
            m
            for m in re.finditer(r"_btm_share\(", src)
            if not src[max(0, m.start() - 4) : m.start()].endswith("def ")
        ]
        self.assertGreaterEqual(len(calls), 4)
        for m in calls:
            window = src[m.start() : m.start() + 220]
            self.assertIn("measured=", window, msg=window)

    def test_model_payload_site_uses_run_holdout_map(self):
        src = _SRC.read_text()
        self.assertIn("measured=_btm_run_measured", src)
        self.assertRegex(
            src,
            r"_btm_run_measured: dict\[int, float\] \| None = \(\s*"
            r'_btm_measured if meta\.get\("nyiso_chp_btm_measured"\) else None',
        )


if __name__ == "__main__":
    unittest.main()
