"""Tests for the content-addressed shared-input store (scripts/lib/bundle_io.py)."""

import json
import unittest
import unittest.mock
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


class TestDerivedSolveInputs(unittest.TestCase):
    """write_derived_solve_inputs pins outage extracts + the capdel partition."""

    def _bundle(self, root: Path) -> Path:
        d = root / "results" / "calibration" / "caiso_run"
        d.mkdir(parents=True)
        return d

    def test_captures_existing_inputs_and_skips_missing(self):
        from unittest import mock

        from market_sim.data import outages

        with TemporaryDirectory() as t:
            run = self._bundle(Path(t))
            raw = Path(t) / "raw"
            raw.mkdir()
            main_csv = raw / "campd-unit-outages-CAISO.csv"
            pd.DataFrame(
                {"facility_id": [1], "unit_id": ["a"], "outage_start": ["2025-01-01"]}
            ).to_csv(main_csv, index=False)
            layup_csv = raw / "campd-unit-outages-layup-CAISO.csv"
            pd.DataFrame({"facility_id": [2]}).to_csv(layup_csv, index=False)
            capdel = pd.DataFrame({"area": ["MIC"], "limit_mw": [16055.0]})

            with (
                mock.patch.object(
                    outages,
                    "unit_outage_csv_for_iso",
                    side_effect=lambda iso: main_csv,
                ),
                mock.patch.object(
                    outages,
                    "unit_outage_short_csv_for_iso",
                    side_effect=lambda iso: raw / "absent-short.csv",
                ),
                mock.patch.object(
                    outages,
                    "unit_partial_outage_csv_for_iso",
                    side_effect=lambda iso: raw / "absent-partial.csv",
                ),
                mock.patch.object(
                    outages,
                    "unit_outage_maxgen_csv_for_iso",
                    side_effect=lambda iso: raw / "absent-maxgen.csv",
                ),
                mock.patch(
                    "market_sim.data.capacity_deliverability._read",
                    return_value=capdel,
                ),
                mock.patch(
                    "market_sim.data.hydro_modes.load_hydro_shapeable",
                    return_value={100: True, 200: False},
                ),
            ):
                refs = bundle_io.write_derived_solve_inputs("CAISO", run)

            # Present inputs captured; absent variants skipped silently.
            self.assertIn("unit_outages", refs)
            self.assertIn("unit_outages_layup", refs)
            self.assertIn("capacity_deliverability", refs)
            self.assertIn("hydro_plant_modes", refs)
            self.assertNotIn("unit_outages_short", refs)
            self.assertNotIn("unit_outages_e923", refs)
            # Refs land in the shared store and round-trip through meta.json.
            (run / "meta.json").write_text(
                json.dumps({"iso": "CAISO", "shared_inputs": refs})
            )
            for name in ("unit_outages", "capacity_deliverability"):
                resolved = bundle_input_path(run, name)
                self.assertIsNotNone(resolved, name)
                self.assertTrue(resolved.exists(), name)
            pd.testing.assert_frame_equal(
                read_bundle_input(run, "capacity_deliverability"), capdel
            )
            # Every captured name is in the declared derived-input namespace.
            self.assertTrue(set(refs) <= set(bundle_io.DERIVED_INPUT_NAMES))

    def test_capdel_absence_records_nothing(self):
        from unittest import mock

        from market_sim.data import outages

        with TemporaryDirectory() as t:
            run = self._bundle(Path(t))
            missing = Path(t) / "nope.csv"
            with (
                mock.patch.object(
                    outages, "unit_outage_csv_for_iso", side_effect=lambda iso: missing
                ),
                mock.patch.object(
                    outages,
                    "unit_outage_short_csv_for_iso",
                    side_effect=lambda iso: missing,
                ),
                mock.patch.object(
                    outages,
                    "unit_partial_outage_csv_for_iso",
                    side_effect=lambda iso: missing,
                ),
                mock.patch.object(
                    outages,
                    "unit_outage_maxgen_csv_for_iso",
                    side_effect=lambda iso: missing,
                ),
                mock.patch(
                    "market_sim.data.capacity_deliverability._read",
                    return_value=None,
                ),
                mock.patch(
                    "market_sim.data.hydro_modes.load_hydro_shapeable",
                    return_value=None,
                ),
            ):
                refs = bundle_io.write_derived_solve_inputs("CAISO", run)
            self.assertEqual(refs, {})


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


class TestStrictBundleInputs(unittest.TestCase):
    """The shard -> register seam: a recorded input whose bytes are absent.

    The shared store is a GITIGNORED SIBLING of the bundle dir, so a shard's
    ``git add <its out-dir>`` cannot carry it (CLAUDE.md rule 34
    [R-SHARD-PROMOTABLE] (a)) and a fetched / composed / freshly-checked-out
    bundle holds the ``meta.json`` reference without the file. Before this the
    three registration-path reads passed the resulting ``None`` straight to
    ``pandas.read_parquet``, whose ``TypeError`` names neither the bundle, the
    input, nor the remedy.
    """

    def _bundle_with_missing_ref(self, root: Path) -> Path:
        run = root / "results" / "calibration" / "nwpp_run"
        run.mkdir(parents=True)
        df = pd.DataFrame({"year": [2024], "plant_id": [1], "annual_mwh": [5.0]})
        ref = write_shared_input(df, "eia923", "NWPP", run)
        (run / "meta.json").write_text(
            json.dumps(
                {"iso": "NWPP", "years": [2024], "shared_inputs": {"eia923": ref}}
            )
        )
        # Simulate the shard hand-off: the reference survives, the bytes do not.
        (run / ref).resolve().unlink()
        return run

    def test_missing_recorded_input_raises_actionable_error(self):
        with TemporaryDirectory() as t:
            run = self._bundle_with_missing_ref(Path(t))
            self.assertIsNone(bundle_input_path(run, "eia923"))
            with self.assertRaises(bundle_io.MissingBundleInput) as ctx:
                bundle_io.require_bundle_input(run, "eia923")
            msg = str(ctx.exception)
            # Names the bundle, the input, the recorded ref and the remedy.
            self.assertIn("nwpp_run", msg)
            self.assertIn("eia923", msg)
            self.assertIn("--restore-shared-inputs", msg)
            # And stays a FileNotFoundError, so existing handlers still catch it.
            self.assertIsInstance(ctx.exception, FileNotFoundError)

    def test_require_returns_path_when_present(self):
        with TemporaryDirectory() as t:
            run = Path(t) / "results" / "calibration" / "spp_run"
            run.mkdir(parents=True)
            df = pd.DataFrame({"a": [1, 2]})
            ref = write_shared_input(df, "campd", "SPP", run)
            (run / "meta.json").write_text(
                json.dumps({"iso": "SPP", "shared_inputs": {"campd": ref}})
            )
            got = bundle_io.require_bundle_input(run, "campd")
            self.assertTrue(got.exists())
            self.assertEqual(got, (run / ref).resolve())

    def test_missing_bundle_inputs_lists_only_absent_recorded_names(self):
        with TemporaryDirectory() as t:
            run = Path(t) / "results" / "calibration" / "miso_run"
            run.mkdir(parents=True)
            here = write_shared_input(pd.DataFrame({"a": [1]}), "campd", "MISO", run)
            gone = write_shared_input(pd.DataFrame({"b": [2]}), "eia923", "MISO", run)
            (run / "meta.json").write_text(
                json.dumps(
                    {"iso": "MISO", "shared_inputs": {"campd": here, "eia923": gone}}
                )
            )
            (run / gone).resolve().unlink()
            missing = bundle_io.missing_bundle_inputs(run)
            # Only the absent one; a name the bundle never recorded is not invented.
            self.assertEqual(set(missing), {"eia923"})
            self.assertEqual(missing["eia923"], gone)

    def test_unrecorded_name_is_not_reported_missing(self):
        with TemporaryDirectory() as t:
            run = Path(t) / "results" / "calibration" / "neiso_run"
            run.mkdir(parents=True)
            (run / "meta.json").write_text(
                json.dumps({"iso": "NEISO", "shared_inputs": {}})
            )
            self.assertEqual(bundle_io.missing_bundle_inputs(run), {})
            # But asking for it strictly still fails, and says it was never recorded.
            with self.assertRaises(bundle_io.MissingBundleInput) as ctx:
                bundle_io.require_bundle_input(run, "eia923")
            self.assertIn("records no shared_inputs", str(ctx.exception))

    def test_legacy_in_bundle_copy_still_satisfies_require(self):
        """Pre-store bundles keep working — the fallback is unchanged."""
        with TemporaryDirectory() as t:
            run = Path(t) / "results" / "calibration" / "old_run"
            run.mkdir(parents=True)
            pd.DataFrame({"a": [1]}).to_parquet(run / "eia923.parquet", index=False)
            self.assertEqual(
                bundle_io.require_bundle_input(run, "eia923"), run / "eia923.parquet"
            )


class TestRestoreVerification(unittest.TestCase):
    """``--restore-shared-inputs`` recovers bytes; it never re-bases a benchmark.

    The store is content-addressed, so a regenerated frame lands at the recorded
    reference IFF its bytes are what the solve read. That makes the recorded hash
    a free integrity proof, and a mismatch a bench/model basis split rather than
    something to adopt silently.
    """

    def test_regenerated_identical_frame_lands_on_the_recorded_ref(self):
        with TemporaryDirectory() as t:
            run = Path(t) / "results" / "calibration" / "run_a"
            run.mkdir(parents=True)
            df = pd.DataFrame(
                {"year": [2024, 2024], "klass": ["COAL", "GAS"], "mwh": [1.0, 2.0]}
            )
            ref = write_shared_input(df, "eia923", "NWPP", run)
            (run / ref).resolve().unlink()
            # A faithful rebuild of the SAME data reproduces the SAME reference.
            self.assertEqual(write_shared_input(df, "eia923", "NWPP", run), ref)

    def test_drifted_frame_lands_on_a_different_ref(self):
        """This inequality is what the restore path turns into a hard error."""
        with TemporaryDirectory() as t:
            run = Path(t) / "results" / "calibration" / "run_b"
            run.mkdir(parents=True)
            solved = pd.DataFrame({"year": [2024], "mwh": [1.0]})
            ref = write_shared_input(solved, "eia923", "NWPP", run)
            drifted = pd.DataFrame({"year": [2024], "mwh": [1.5]})
            self.assertNotEqual(write_shared_input(drifted, "eia923", "NWPP", run), ref)
            self.assertNotEqual(content_hash(solved), content_hash(drifted))


class TestRestoreSharedInputsGuard(unittest.TestCase):
    """``restore_shared_inputs`` refuses to adopt a drifted benchmark.

    ``--rebuild-benchmark`` re-points ``meta.json`` at whatever it produces —
    that is its purpose, adopting a benchmark-logic change. The RECOVERY path
    must not: re-pointing a scored run's benchmark against a dispatch solved on
    the old one is a bench/model basis split, which is the defect class the
    miso-253 / spp-49 recoveries inside the builder each patched one instance of.
    """

    def _bundle(self, root: Path, frame: pd.DataFrame) -> tuple[Path, str]:
        run = root / "results" / "calibration" / "guard_run"
        run.mkdir(parents=True)
        ref = write_shared_input(frame, "eia923", "NWPP", run)
        (run / "meta.json").write_text(
            json.dumps(
                {"iso": "NWPP", "years": [2024], "shared_inputs": {"eia923": ref}},
                indent=2,
            )
            + "\n"
        )
        (run / ref).resolve().unlink()  # the shard hand-off: ref without bytes
        return run, ref

    def test_matching_rebuild_restores_and_leaves_meta_untouched(self):
        import scripts.run_calibration_full as rcf

        solved = pd.DataFrame({"year": [2024], "klass": ["COAL"], "mwh": [7.0]})
        with TemporaryDirectory() as t:
            run, ref = self._bundle(Path(t), solved)
            before = (run / "meta.json").read_bytes()
            with unittest.mock.patch.object(
                rcf, "build_benchmark_frames", return_value=("NWPP", {"eia923": solved})
            ):
                restored = rcf.restore_shared_inputs(run)
            self.assertEqual(restored, {"eia923": ref})
            self.assertTrue((run / ref).resolve().exists())
            # A scored bundle's provenance file is byte-identical afterwards.
            self.assertEqual((run / "meta.json").read_bytes(), before)

    def test_drifted_rebuild_is_a_hard_error_and_re_points_nothing(self):
        import scripts.run_calibration_full as rcf

        solved = pd.DataFrame({"year": [2024], "klass": ["COAL"], "mwh": [7.0]})
        drifted = pd.DataFrame({"year": [2024], "klass": ["COAL"], "mwh": [9.5]})
        with TemporaryDirectory() as t:
            run, ref = self._bundle(Path(t), solved)
            before = (run / "meta.json").read_bytes()
            with unittest.mock.patch.object(
                rcf,
                "build_benchmark_frames",
                return_value=("NWPP", {"eia923": drifted}),
            ):
                with self.assertRaises(SystemExit) as ctx:
                    rcf.restore_shared_inputs(run)
            msg = str(ctx.exception)
            self.assertIn("DIFFERENT BYTES", msg)
            self.assertIn("--rebuild-benchmark", msg)
            # meta.json is unchanged, and the bundle still reports the input missing
            # rather than silently resolving to the drifted frame.
            self.assertEqual((run / "meta.json").read_bytes(), before)
            self.assertIsNone(bundle_input_path(run, "eia923"))

    def test_complete_bundle_is_a_no_op(self):
        import scripts.run_calibration_full as rcf

        with TemporaryDirectory() as t:
            run = Path(t) / "results" / "calibration" / "done_run"
            run.mkdir(parents=True)
            ref = write_shared_input(pd.DataFrame({"a": [1]}), "eia923", "NWPP", run)
            (run / "meta.json").write_text(
                json.dumps({"iso": "NWPP", "shared_inputs": {"eia923": ref}})
            )
            # No builder call at all — nothing is missing, so nothing is rebuilt.
            with unittest.mock.patch.object(
                rcf, "build_benchmark_frames", side_effect=AssertionError("rebuilt")
            ):
                self.assertEqual(rcf.restore_shared_inputs(run), {})
