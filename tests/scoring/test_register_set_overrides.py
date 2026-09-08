"""A ``--set``-constructed leg is self-describing from its sidecar (SCN-FIX3 item 4).

Trivial-first and LP-free: every case writes a tiny summary JSON and reads
``register_forecast_run.carry_set_overrides``, never a solve and never a
registration.

**The defect.** ``run_full_horizon`` records the generic ``--set FIELD=VALUE``
overrides it applied as the summary's own ``set_overrides`` block, and the
bundle carries the resolved value in both ``full_horizon_summary.json`` and
``run_config.json``. But ``register_forecast_baseline.build_sidecar`` copies a
FIXED list of summary keys into ``meta`` and that block is not among them, so
the key never reached the sidecar and every reader sees ``None`` —
measured on NYISO's ``ces-p60``, whose bundle correctly holds
``federal_ces_premium_usd_per_mwh: 60.0``. Nothing was mis-registered (the run
is still identified by ``meta.case`` plus its distinct ``cache_key``); what was
missing is that such a leg was not self-describing from the DASHBOARD, which is
where a reader looks first. Reported by ``SCN-WS5A-POLICY-NYISO`` §9 item 5.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts import register_forecast_run as R  # noqa: E402

#: The measured case: NYISO's ces-p60 leg, built with one --set override.
CES_P60 = {"federal_ces_premium_usd_per_mwh": 60.0}


def _carry(summary: dict | None, meta: dict | None = None) -> dict:
    """Run the carry against a temp summary; return the resulting meta."""
    sidecar = {"run_id": "nyiso-2026-2030-x", "meta": dict(meta or {})}
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "full_horizon_summary.json"
        if summary is not None:
            path.write_text(json.dumps(summary))
        R.carry_set_overrides(sidecar, path)
    return sidecar["meta"]


class SetOverridesReachTheSidecarTest(unittest.TestCase):
    """The override the solve applied is readable from the sidecar."""

    def test_the_measured_ces_p60_case(self) -> None:
        meta = _carry({"iso": "NYISO", "set_overrides": CES_P60})
        self.assertEqual(meta["set_overrides"], CES_P60)

    def test_the_block_is_copied_not_referenced(self) -> None:
        summary = {"set_overrides": CES_P60}
        meta = _carry(summary)
        meta["set_overrides"]["federal_ces_premium_usd_per_mwh"] = 999.0
        self.assertEqual(summary["set_overrides"], CES_P60)

    def test_multiple_overrides_are_all_carried(self) -> None:
        both = {"federal_ces_premium_usd_per_mwh": 60.0, "carbon_price": 25.0}
        self.assertEqual(_carry({"set_overrides": both})["set_overrides"], both)


class EmptyIsNotUnrecordedTest(unittest.TestCase):
    """``{}`` and ``None`` are different facts and stay distinguishable."""

    def test_recorded_but_empty_reads_as_empty(self) -> None:
        # The solve recorded the block; there were no overrides.
        self.assertEqual(_carry({"set_overrides": {}})["set_overrides"], {})

    def test_a_summary_predating_the_block_reads_as_none(self) -> None:
        # The bundle cannot answer -- never defaulted to {}.
        self.assertIsNone(_carry({"iso": "NYISO"})["set_overrides"])

    def test_the_two_cases_are_distinguishable(self) -> None:
        recorded = _carry({"set_overrides": {}})["set_overrides"]
        unrecorded = _carry({"iso": "NYISO"})["set_overrides"]
        self.assertIsNotNone(recorded)
        self.assertIsNone(unrecorded)

    def test_a_non_dict_block_is_refused_as_unrecorded(self) -> None:
        self.assertIsNone(_carry({"set_overrides": "60.0"})["set_overrides"])


class RobustnessAndPrecedenceTest(unittest.TestCase):
    """The carry never breaks a registration and never overwrites a claim."""

    def test_an_explicit_extra_meta_claim_wins(self) -> None:
        claim = {"carbon_price": 1.0}
        meta = _carry({"set_overrides": CES_P60}, meta={"set_overrides": claim})
        self.assertEqual(meta["set_overrides"], claim)

    def test_an_extra_meta_null_is_also_left_alone(self) -> None:
        meta = _carry({"set_overrides": CES_P60}, meta={"set_overrides": None})
        self.assertIsNone(meta["set_overrides"])

    def test_a_missing_summary_file_does_not_raise(self) -> None:
        self.assertIsNone(_carry(None)["set_overrides"])

    def test_unparseable_summary_does_not_raise(self) -> None:
        sidecar = {"meta": {}}
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "full_horizon_summary.json"
            path.write_text("{ not json")
            R.carry_set_overrides(sidecar, path)
        self.assertIsNone(sidecar["meta"]["set_overrides"])

    def test_a_sidecar_without_meta_gains_one(self) -> None:
        sidecar: dict = {"run_id": "x"}
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "s.json"
            path.write_text(json.dumps({"set_overrides": CES_P60}))
            R.carry_set_overrides(sidecar, path)
        self.assertEqual(sidecar["meta"]["set_overrides"], CES_P60)

    def test_no_other_meta_key_is_touched(self) -> None:
        before = {"case": "CES-P60", "campaign": "scn-campaign-policy-2026-09-06"}
        meta = _carry({"set_overrides": CES_P60}, meta=before)
        for k, v in before.items():
            self.assertEqual(meta[k], v)


if __name__ == "__main__":
    unittest.main()
