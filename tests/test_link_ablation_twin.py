"""Tests for scripts/link_ablation_twin.py (D-3 twin linkage, rule 21).

Builds a temporary registry + runs dir + twin bundle so ``link`` can load both
committed payloads and write the ``ablation_twin`` / ``ablation_delta`` /
``market_story`` fields into the keeper sidecar — no LP solve.
"""

import base64
import gzip
import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "link_ablation_twin", str(_REPO / "scripts" / "link_ablation_twin.py")
)
lat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lat)
cv = lat.cv


def _run_js(payload: dict) -> str:
    b64 = base64.b64encode(gzip.compress(json.dumps(payload).encode())).decode()
    return f'window.BC=window.BC||{{}};window.BC.runGz["x"]="{b64}";'


class LinkTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self._reg = root / "registry"
        self._runs = root / "runs"
        self._reg.mkdir()
        self._runs.mkdir()
        self._orig_reg, self._orig_runs, self._orig_repo = (
            cv.REGISTRY_DIR,
            cv.RUNS_DIR,
            cv.REPO,
        )
        self._orig_lat_repo = lat.REPO
        cv.REGISTRY_DIR, cv.RUNS_DIR, cv.REPO = self._reg, self._runs, root
        lat.REPO = root  # link() resolves the twin bundle via its own REPO

        # Keeper: CT_PEAKER at 10 TWh; twin (floors off): 6 TWh.
        (self._reg / "k.json").write_text(json.dumps({"id": "k", "iso": "ERCOT"}))
        (self._runs / "k.js").write_text(
            _run_js({"years": {"2023": {"gmModel": {"CT_PEAKER": 10.0}}}})
        )
        twin_bundle = root / "bundle-abl"
        twin_bundle.mkdir()
        (twin_bundle / "run_config.json").write_text(json.dumps({"ablation_of": "k"}))
        (self._reg / "k-ablation.json").write_text(
            json.dumps({"id": "k-ablation", "iso": "ERCOT", "bundle": "bundle-abl"})
        )
        (self._runs / "k-ablation.js").write_text(
            _run_js({"years": {"2023": {"gmModel": {"CT_PEAKER": 6.0}}}})
        )

    def tearDown(self):
        cv.REGISTRY_DIR, cv.RUNS_DIR, cv.REPO = (
            self._orig_reg,
            self._orig_runs,
            self._orig_repo,
        )
        lat.REPO = self._orig_lat_repo
        self._tmp.cleanup()

    def test_link_writes_delta_and_story(self):
        side = lat.link("k", "k-ablation", "CT holds shape; +4 TWh is unexplained.")
        self.assertEqual(side["ablation_twin"], "k-ablation")
        self.assertEqual(side["market_story"], "CT holds shape; +4 TWh is unexplained.")
        self.assertEqual(side["ablation_delta"][0]["class"], "CT_PEAKER")
        self.assertEqual(side["ablation_delta"][0]["delta_twh"], 4.0)
        # Persisted to disk.
        on_disk = json.loads((self._reg / "k.json").read_text())
        self.assertEqual(on_disk["ablation_twin"], "k-ablation")

    def test_refuses_non_ablation_twin(self):
        # A twin whose run_config has no ablation_of must not be linkable.
        (Path(self._tmp.name) / "bundle-abl" / "run_config.json").write_text(
            json.dumps({})
        )
        with self.assertRaises(SystemExit):
            lat.link("k", "k-ablation", None)

    def test_missing_twin_sidecar(self):
        with self.assertRaises(SystemExit):
            lat.link("k", "does-not-exist", None)


if __name__ == "__main__":
    unittest.main()
