"""Tests for the content-addressed shared-input store (scripts/lib/bundle_io.py)."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.lib import bundle_io
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
            self.assertEqual(bundle_input_path(run, "campd"), run / "campd.parquet")
            # Absent input -> None (caller can branch on it).
            self.assertIsNone(bundle_input_path(run, "eia930"))

    def test_content_hash_is_stable_and_order_sensitive(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        self.assertEqual(content_hash(df), content_hash(df.copy()))
        self.assertNotEqual(content_hash(df), content_hash(df[["b", "a"]]))


class TestBundlePathHelpers(unittest.TestCase):
    def test_bundles_root_under_repo(self):
        self.assertEqual(bundle_io.bundles_root(), bundle_io.BUNDLES_ROOT)
        self.assertEqual(bundle_io.bundles_root().name, "calibration")
        self.assertEqual(bundle_io.bundles_root().parent.name, "results")

    def test_dispatch_path(self):
        run = Path("/x/results/calibration/run")
        self.assertEqual(
            bundle_io.dispatch_path(run, 2024),
            run / "dispatch" / "2024_P1.parquet",
        )
        self.assertEqual(
            bundle_io.dispatch_path(run, 2023, pass_label="P0"),
            run / "dispatch" / "2023_P0.parquet",
        )

    def test_bundle_meta_reads_or_empty(self):
        with TemporaryDirectory() as t:
            run = Path(t) / "run"
            run.mkdir()
            self.assertEqual(bundle_io.bundle_meta(run), {})
            (run / "meta.json").write_text(json.dumps({"iso": "PJM"}))
            self.assertEqual(bundle_io.bundle_meta(run), {"iso": "PJM"})

    def test_resolve_bundle_existing_path(self):
        with TemporaryDirectory() as t:
            run = Path(t) / "results" / "calibration" / "run"
            run.mkdir(parents=True)
            self.assertEqual(bundle_io.resolve_bundle(run), run)
            # A path-like string that does not exist is still taken literally.
            missing = str(Path(t) / "nope" / "run")
            self.assertEqual(bundle_io.resolve_bundle(missing), Path(missing))

    def test_resolve_bundle_unknown_raises(self):
        with self.assertRaises(FileNotFoundError):
            bundle_io.resolve_bundle("definitely-not-a-real-run-id-xyz")


if __name__ == "__main__":
    unittest.main()
