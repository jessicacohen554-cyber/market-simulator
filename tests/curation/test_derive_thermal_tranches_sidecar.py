"""Tests for the thermal-tranche vintage sidecar writer (xiso-6).

``derive_thermal_tranches.write_tranche_sidecar`` stamps WHICH group sets a
deriver run was emitting into ``thermal_tranches_<ISO>.meta.json`` next to the
CSV — the record whose absence produced the xiso-5 non-monotone vintage ladder
(FINDING-xiso5-thermal-tranche-coverage-2026-08-04.md §1/§6 option 4). Trivial
synthetic CSVs only (testing pattern): no CAMPD read, no derivation — the
writer is a pure function of the on-disk CSV bytes plus its keyword record.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from tests.helpers import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))

from derive_thermal_tranches import (  # noqa: E402
    _BACKFILL_NOTE,
    _SIDECAR_SCHEMA_VERSION,
    write_tranche_sidecar,
)


def _tiny_csv(directory: Path) -> Path:
    """Two ok rows (one blank online_frac) + one eia923_cf row."""
    path = directory / "thermal_tranches_TEST.csv"
    pd.DataFrame(
        [
            {
                "plant_code": 1,
                "plant_group": "ST_GAS",
                "name": "A",
                "status": "ok",
                "committed_pct": 30.0,
                "online_frac": 0.9,
            },
            {
                "plant_code": 2,
                "plant_group": "CC_REGULAR",
                "name": "B",
                "status": "ok",
                "committed_pct": 40.0,
                "online_frac": None,
            },
            {
                "plant_code": 3,
                "plant_group": "CT_CHP",
                "name": "C",
                "status": "eia923_cf",
                "committed_pct": None,
                "online_frac": None,
            },
        ]
    ).to_csv(path, index=False)
    return path


class TestSidecarWriter(unittest.TestCase):
    """write_tranche_sidecar over a trivial synthetic artifact."""

    def test_derived_sidecar_fields(self):
        with TemporaryDirectory() as tmp:
            csv = _tiny_csv(Path(tmp))
            side = write_tranche_sidecar(
                csv,
                provenance="derived",
                groups_in_force={"online_frac_groups": ["COAL", "ST_GAS"]},
                derive_invocation={"iso": "TEST", "years": [2024]},
                note="n",
            )
            self.assertEqual(side, csv.with_suffix(".meta.json"))
            rec = json.loads(side.read_text())
            self.assertEqual(rec["sidecar_schema_version"], _SIDECAR_SCHEMA_VERSION)
            self.assertEqual(rec["artifact"], csv.name)
            self.assertEqual(
                rec["artifact_sha256"], hashlib.sha256(csv.read_bytes()).hexdigest()
            )
            self.assertEqual(rec["artifact_rows"], 3)
            self.assertEqual(
                rec["columns"][:4], ["plant_code", "plant_group", "name", "status"]
            )
            self.assertEqual(rec["provenance"], "derived")
            self.assertEqual(rec["vintage"]["online_frac_groups"], ["COAL", "ST_GAS"])
            # Group sets the caller did not pass stay honestly null.
            self.assertIsNone(rec["vintage"]["peaking_groups"])
            self.assertEqual(rec["derive_invocation"]["years"], [2024])
            self.assertEqual(rec["row_counts_by_status"], {"ok": 2, "eia923_cf": 1})

    def test_coverage_counts_ok_rows_only(self):
        with TemporaryDirectory() as tmp:
            csv = _tiny_csv(Path(tmp))
            side = write_tranche_sidecar(
                csv,
                provenance="backfill-descriptive",
                groups_in_force=None,
                derive_invocation=None,
                note=_BACKFILL_NOTE,
            )
            cov = json.loads(side.read_text())["coverage_ok_rows"]
            # Identity columns are excluded from the census.
            self.assertNotIn("plant_code", cov)
            self.assertNotIn("status", cov)
            # ok rows only: the eia923_cf CT_CHP row contributes no group.
            self.assertEqual(cov["online_frac"]["ST_GAS"], [1, 1])
            self.assertEqual(cov["online_frac"]["CC_REGULAR"], [0, 1])
            self.assertNotIn("CT_CHP", cov["online_frac"])

    def test_backfill_records_unknown_vintage(self):
        with TemporaryDirectory() as tmp:
            csv = _tiny_csv(Path(tmp))
            side = write_tranche_sidecar(
                csv,
                provenance="backfill-descriptive",
                groups_in_force=None,
                derive_invocation=None,
                note=_BACKFILL_NOTE,
            )
            rec = json.loads(side.read_text())
            self.assertEqual(rec["provenance"], "backfill-descriptive")
            self.assertIsNone(rec["derive_invocation"])
            vintage = rec["vintage"]
            for key in (
                "online_frac_groups",
                "chp_groups",
                "peaking_groups",
                "thermal_groups",
            ):
                self.assertIsNone(vintage[key], key)
            self.assertIn("UNKNOWN", vintage["note"])

    def test_csv_bytes_untouched_and_deterministic(self):
        with TemporaryDirectory() as tmp:
            csv = _tiny_csv(Path(tmp))
            before = hashlib.sha256(csv.read_bytes()).hexdigest()
            kwargs = dict(
                provenance="backfill-descriptive",
                groups_in_force=None,
                derive_invocation=None,
                note=_BACKFILL_NOTE,
            )
            first = write_tranche_sidecar(csv, **kwargs).read_bytes()
            second = write_tranche_sidecar(csv, **kwargs).read_bytes()
            self.assertEqual(before, hashlib.sha256(csv.read_bytes()).hexdigest())
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
