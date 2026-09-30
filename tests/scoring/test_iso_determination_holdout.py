"""Rubric v3.13 — the ISO determination covers EVERY registered year.

Owner instruction 2026-09-30, verbatim: "Shouldn't be considered calibrated if
holdout years miss." It reverses rule 30 [R-TOUCHPOINT-FOLD] (c) of 2026-09-05
("A HELD-OUT YEAR NEVER DOWNGRADES THE ISO"). ``calibration_verdict.
iso_determination`` folds the keeper's designated scopes plus every run stamped
to it via ``holdout.keeper``, worst-of, each scope on its own caveat budget
(owner card "Per run, worst-of"); a folded run solved at a different basis sha
still gates and is flagged stale (owner card "Counts; flagged stale").

The scorer's ``determine`` is stubbed and the registry is a temp dir, so these
tests never read the committed registry or solve anything.
"""

import json
import tempfile
import unittest
from pathlib import Path

from scripts import calibration_verdict as cv


def _verdict(det, fails=()):
    """A minimal determine() result: ``fails`` is ``[(criterion, year), ...]``."""
    crit: dict[str, dict] = {}
    for cid, year in fails:
        crit.setdefault(cid, {"records": []})["records"].append(
            {"criterion": cid, "year": year, "status": cv.FAIL}
        )
    reasons = [] if det == "CALIBRATED" else [f"stub reason {det}"]
    return {"determination": det, "reasons": reasons, "criteria": crit}


class IsoDeterminationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.reg = self.root / "registry"
        self.reg.mkdir()
        self._real_dir = cv.REGISTRY_DIR
        self._real_determine = cv.determine
        cv.REGISTRY_DIR = self.reg
        self.verdicts: dict[str, dict] = {}
        self.years: dict[str, list[int]] = {}

        def fake_determine(run_id, years=None):
            v = dict(self.verdicts[run_id])
            span = self.years[run_id]
            v["target_years"] = [y for y in span if years is None or y in years]
            return v

        cv.determine = fake_determine

    def tearDown(self):
        cv.REGISTRY_DIR = self._real_dir
        cv.determine = self._real_determine
        self._tmp.cleanup()

    def _run(self, run_id, iso, years, det, fails=(), keeper=None, sha="aaaaaaaa"):
        bundle = self.root / "bundles" / run_id
        bundle.mkdir(parents=True)
        (bundle / "run_config.json").write_text(json.dumps({"git": {"basis_sha": sha}}))
        side = {"id": run_id, "iso": iso, "years": years, "bundle": str(bundle)}
        if keeper:
            side["holdout"] = {"keeper": keeper, "tier": "validation"}
        (self.reg / f"{run_id}.json").write_text(json.dumps(side))
        self.verdicts[run_id] = _verdict(det, fails)
        self.years[run_id] = years

    def test_failing_folded_year_downgrades_the_iso(self):
        self._run("k", "CAISO", [2022, 2023, 2024, 2025], "CALIBRATED")
        self._run(
            "tp",
            "CAISO",
            [2019, 2020, 2021],
            "NOT-YET",
            fails=[("fuelmix", 2019), ("price_mean", 2021)],
            keeper="k",
        )
        out = cv.iso_determination("CAISO", "k")
        self.assertEqual(out["determination"], "NOT-YET")
        self.assertEqual(out["years"], [2019, 2020, 2021, 2022, 2023, 2024, 2025])
        (line,) = out["reasons"]
        self.assertIn("2019/2020/2021", line)
        self.assertIn("fuelmix 2019", line)
        self.assertIn("price_mean 2021", line)

    def test_passing_folded_year_does_not_downgrade(self):
        self._run("k", "NYISO", [2022, 2023, 2024, 2025], "CALIBRATED")
        self._run("tp", "NYISO", [2021], "CALIBRATED", keeper="k")
        out = cv.iso_determination("NYISO", "k")
        self.assertEqual(out["determination"], "CALIBRATED")
        self.assertEqual(out["reasons"], [])
        self.assertEqual([s["kind"] for s in out["scopes"]], ["keeper", "folded"])

    def test_foreign_fold_never_touches_another_isos_keeper(self):
        # A run from ANOTHER ISO stamped (wrongly) to this keeper id, and a
        # same-ISO run stamped to a DIFFERENT keeper: neither is folded.
        self._run("k", "NEISO", [2019, 2020], "CALIBRATED")
        self._run(
            "foreign", "PJM", [2021], "NOT-YET", fails=[("fuelmix", 2021)], keeper="k"
        )
        self._run("other", "NEISO", [2021], "NOT-YET", keeper="k-old")
        out = cv.iso_determination("NEISO", "k")
        self.assertEqual(out["determination"], "CALIBRATED")
        self.assertEqual([s["run_id"] for s in out["scopes"]], ["k"])

    def test_validation_tier_partition_config_now_gates(self):
        self._run("k", "MISO", [2019, 2020, 2021, 2022, 2023, 2024, 2025], "CALIBRATED")
        verdicts = {
            (2023, 2024, 2025): _verdict("CALIBRATED"),
            (2019, 2020, 2021, 2022): _verdict("NOT-YET", [("price_shape", 2021)]),
        }

        def fake_determine(run_id, years=None):
            v = dict(verdicts[tuple(years)])
            v["target_years"] = list(years)
            return v

        cv.determine = fake_determine
        cp = {
            "configs": [
                {"role": "train", "run_id": "k", "years": [2023, 2024, 2025]},
                {
                    "role": "validation",
                    "run_id": "k",
                    "years": [2019, 2020, 2021, 2022],
                    "tier": "validation",
                },
            ]
        }
        out = cv.iso_determination("MISO", "k", cp)
        self.assertEqual(out["determination"], "NOT-YET")
        self.assertIn("price_shape 2021", out["reasons"][0])

    def test_stale_folded_run_still_gates_and_is_flagged(self):
        self._run("k", "SPP", [2023, 2024, 2025], "CALIBRATED", sha="aaaaaaaa")
        self._run(
            "tp", "SPP", [2020], "CALIBRATED-WITH-CAVEATS", keeper="k", sha="bbbbbbbb"
        )
        out = cv.iso_determination("SPP", "k")
        self.assertEqual(out["determination"], "CALIBRATED-WITH-CAVEATS")
        folded = [s for s in out["scopes"] if s["kind"] == "folded"][0]
        self.assertTrue(folded["stale"])
        self.assertIn("STALE", out["reasons"][0])

    def test_matching_basis_is_not_stale(self):
        self._run("k", "SPP", [2023], "CALIBRATED")
        self._run("tp", "SPP", [2020], "CALIBRATED", keeper="k")
        folded = [
            s
            for s in cv.iso_determination("SPP", "k")["scopes"]
            if s["kind"] == "folded"
        ]
        self.assertFalse(folded[0]["stale"])


if __name__ == "__main__":
    unittest.main()
