"""Tests for the content-addressed shared-input store (scripts/lib/bundle_io.py)."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.lib.bundle_io import (
    bundle_input_path,
    content_hash,
    read_bundle_input,
    write_shared_input,
)


class TestSharedInputStore(unittest.TestCase):
    def _bundle(self, root: Path, name: str = "caiso_run") -> Path:
        d = root / "results" / "calibration" / name
        d.mkdir(parents=True)
        return d

    def test_write_returns_relative_ref_and_dedupes(self):
        with TemporaryDirectory() as t:
            run = self._bundle(Path(t))
            df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
            ref = write_shared_input(df, "campd", "CAISO", run)
            # Reference is bundle-relative into the shared sibling.
            self.assertTrue(ref.startswith("../_shared/CAISO/campd-"))
            self.assertTrue(ref.endswith(".parquet"))
            # Identical content writes once (same hash -> same path).
            self.assertEqual(ref, write_shared_input(df, "campd", "CAISO", run))
            shared = run.parent / "_shared" / "CAISO"
            self.assertEqual(len(list(shared.glob("*.parquet"))), 1)

    def test_different_content_is_a_separate_file(self):
        with TemporaryDirectory() as t:
            run = self._bundle(Path(t))
            write_shared_input(pd.DataFrame({"a": [1]}), "eia923", "CAISO", run)
            write_shared_input(pd.DataFrame({"a": [2]}), "eia923", "CAISO", run)
            shared = run.parent / "_shared" / "CAISO"
            self.assertEqual(len(list(shared.glob("*.parquet"))), 2)

    def test_round_trip_via_meta(self):
        with TemporaryDirectory() as t:
            run = self._bundle(Path(t))
            df = pd.DataFrame({"v": [10, 20]})
            ref = write_shared_input(df, "eia930", "CAISO", run)
            (run / "meta.json").write_text(
                json.dumps({"iso": "CAISO", "shared_inputs": {"eia930": ref}})
            )
            resolved = bundle_input_path(run, "eia930")
            self.assertIsNotNone(resolved)
            self.assertTrue(resolved.exists())
            pd.testing.assert_frame_equal(read_bundle_input(run, "eia930"), df)

    def test_legacy_in_bundle_fallback(self):
        with TemporaryDirectory() as t:
            run = self._bundle(Path(t), "legacy_run")
            df = pd.DataFrame({"v": [1]})
            df.to_parquet(run / "campd.parquet", index=False)
            (run / "meta.json").write_text(json.dumps({"iso": "CAISO"}))
            # No shared ref -> resolves the in-bundle file.
            self.assertEqual(
                bundle_input_path(run, "campd"), run / "campd.parquet"
            )
            # Absent input -> None (caller can branch on it).
            self.assertIsNone(bundle_input_path(run, "eia930"))

    def test_content_hash_is_stable_and_order_sensitive(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        self.assertEqual(content_hash(df), content_hash(df.copy()))
        self.assertNotEqual(content_hash(df), content_hash(df[["b", "a"]]))


if __name__ == "__main__":
    unittest.main()
