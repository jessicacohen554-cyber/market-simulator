"""Tests for the golden-manifest per-entry provenance schema and its CI gate.

Covers the two halves of the 2026-09-01 stage-0 provenance repair
(``docs/FINDING-stage0-provenance-repair-2026-09.md``):

* **the schema** — every entry of the live ``perfb-stage0`` manifest carries its
  OWN provenance and its own keeper snapshot, and the file carries no shared
  top-level ``git_sha`` that a later capture could re-stamp;
* **the retention invariant** — ``scripts/check_golden_manifest.py`` fails an
  entry whose provenance run has been pruned from the registry and which never
  absorbed the sidecar, passes one that did, and refuses a manifest that
  reintroduces the shared-sha schema.

``check_golden_manifest`` is loaded by path (it is a loose ``scripts/`` module)
and its directory constants are monkeypatched per test onto temp trees, so no
test reads or writes the real registry.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "check_golden_manifest", str(REPO_ROOT / "scripts" / "check_golden_manifest.py")
)
cgm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cgm)

LIVE_MANIFEST = (
    REPO_ROOT / "results" / "regression-goldens" / "perfb-stage0" / "manifest.json"
)


def _entry(keeper_id="2026-01-01-x-1", iso="PJM", *, snapshot=True, provenance=True):
    """Return a minimal well-formed schema-v2 manifest entry."""
    e = {
        "keeper_id": keeper_id,
        "bundle": "results/calibration/x_1",
        "years": [2023, 2024, 2025],
        "hours": 8760,
        "content_hashes": {"system.parquet": "0" * 64},
    }
    if provenance:
        e["provenance"] = {
            "git_sha": "abc1234",
            "git_sha_full": "abc1234" + "0" * 33,
            "basis_sha": "abc1234" + "0" * 33,
            "git_dirty": False,
            "recorded_at": "2026-01-01T00:00:00Z",
            "env": {"MARKET_SIM_HIGHS_THREADS": "1"},
            "highspy_version": "unknown",
            "source": "stamped-at-capture",
        }
    if snapshot:
        e["keeper_snapshot"] = {
            "id": keeper_id,
            "iso": iso,
            "label": "x 1",
            "date": "2026-01-01",
            "shorthand": "x-1",
            "definition": "a run",
            "years": [2023, 2024, 2025],
            "bundle": "results/calibration/x_1",
            "sidecar_at_capture": "present",
        }
    return e


class GoldenManifestSchemaTest(unittest.TestCase):
    """The committed perfb-stage0 manifest conforms to schema v2."""

    @classmethod
    def setUpClass(cls):
        cls.man = json.loads(LIVE_MANIFEST.read_text())

    def test_declares_schema_v2(self):
        self.assertGreaterEqual(self.man.get("schema_version"), 2)

    def test_no_shared_top_level_provenance(self):
        """The defect itself: one sha at a scope shared by every capture."""
        for key in cgm.FORBIDDEN_TOP_LEVEL_KEYS:
            self.assertNotIn(
                key,
                self.man,
                f"top-level {key!r} is capture-specific; one capture would "
                f"re-stamp it for all six entries",
            )

    def test_every_entry_has_its_own_provenance(self):
        for iso, entry in self.man["keepers"].items():
            with self.subTest(iso=iso):
                prov = entry.get("provenance")
                self.assertIsInstance(prov, dict)
                for key in cgm.REQUIRED_PROVENANCE_KEYS:
                    self.assertIn(key, prov, f"{iso}: provenance missing {key}")

    def test_provenance_shas_are_distinct_per_capture(self):
        """Six captures at six trees must not share one sha.

        This is the property the v1 schema could not express: it is what makes a
        re-stamp detectable rather than silent.
        """
        shas = [e["provenance"]["git_sha"] for e in self.man["keepers"].values()]
        self.assertEqual(
            len(set(shas)), len(shas), f"provenance shas are not per-capture: {shas}"
        )

    def test_unknown_sha_must_carry_a_reason(self):
        """An honest 'unknown' is allowed; a bare one is not."""
        for iso, entry in self.man["keepers"].items():
            prov = entry.get("provenance", {})
            if prov.get("git_sha") == "unknown":
                with self.subTest(iso=iso):
                    self.assertTrue(
                        prov.get("provenance_note"),
                        f"{iso}: 'unknown' sha needs a one-line reason",
                    )

    def test_every_entry_is_self_contained(self):
        """Each entry carries the sidecar identity, so a prune costs nothing."""
        for iso, entry in self.man["keepers"].items():
            with self.subTest(iso=iso):
                snap = entry.get("keeper_snapshot")
                self.assertIsInstance(snap, dict)
                for key in cgm.REQUIRED_SNAPSHOT_KEYS:
                    self.assertIn(key, snap)
                self.assertEqual(snap["id"], entry["keeper_id"])
                self.assertEqual(snap["bundle"], entry["bundle"])
                self.assertEqual(snap["years"], entry["years"])

    def test_live_manifest_passes_the_gate(self):
        fails, _ = cgm.check_manifest(LIVE_MANIFEST)
        self.assertEqual(fails, [], f"live manifest fails its own gate: {fails}")


class RetentionInvariantTest(unittest.TestCase):
    """check_golden_manifest's behaviour on temp trees."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.goldens = root / "results" / "regression-goldens"
        self.registry = root / "registry"
        self.keepers = root / "keepers"
        for d in (self.goldens, self.registry, self.keepers):
            d.mkdir(parents=True)
        self._saved = (cgm.REPO, cgm.GOLDENS_ROOT, cgm.REGISTRY_DIR, cgm.KEEPERS_DIR)
        cgm.REPO = root
        cgm.GOLDENS_ROOT = self.goldens
        cgm.REGISTRY_DIR = self.registry
        cgm.KEEPERS_DIR = self.keepers

    def tearDown(self):
        cgm.REPO, cgm.GOLDENS_ROOT, cgm.REGISTRY_DIR, cgm.KEEPERS_DIR = self._saved
        self._tmp.cleanup()

    def _write(self, tag, keepers, *, version=2, extra=None):
        p = self.goldens / tag / "manifest.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        man = {"schema_version": version, "stage_tag": tag, "keepers": keepers}
        man.update(extra or {})
        p.write_text(json.dumps(man, indent=2))
        return p

    def test_pruned_sidecar_with_snapshot_passes(self):
        """The whole point: retention may prune, because the entry absorbed it."""
        p = self._write("s1", {"PJM": _entry()})
        self.assertFalse((self.registry / "2026-01-01-x-1.json").exists())
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        self.assertTrue(any("PRUNED from registry" in n for n in notes))

    def test_pruned_sidecar_without_snapshot_fails(self):
        """The orphaning that used to be silent with every gate green."""
        p = self._write("s1", {"PJM": _entry(snapshot=False)})
        fails, _ = cgm.check_manifest(p)
        self.assertTrue(fails)
        joined = " ".join(fails)
        self.assertIn("keeper_snapshot", joined)
        self.assertIn("pruned from the registry", joined.lower())

    def test_missing_snapshot_fails_even_while_the_sidecar_lives(self):
        """Absorb it BEFORE the prune, not after — after is too late."""
        (self.registry / "2026-01-01-x-1.json").write_text("{}")
        p = self._write("s1", {"PJM": _entry(snapshot=False)})
        fails, _ = cgm.check_manifest(p)
        self.assertTrue(any("keeper_snapshot" in f for f in fails))

    def test_shared_top_level_sha_is_rejected(self):
        p = self._write("s1", {"PJM": _entry()}, extra={"git_sha": "deadbee"})
        fails, _ = cgm.check_manifest(p)
        self.assertTrue(any("top-level 'git_sha'" in f for f in fails))

    def test_schema_v1_is_rejected_for_a_new_stage_tag(self):
        """The ratchet: a tag not on the legacy list must be v2."""
        p = self._write("brand-new-tag", {"PJM": _entry()}, version=1)
        fails, _ = cgm.check_manifest(p)
        self.assertTrue(any("schema_version" in f for f in fails))

    def test_legacy_tag_is_grandfathered_and_reported(self):
        tag = sorted(cgm.LEGACY_V1_MANIFESTS)[0]
        p = self._write(
            tag, {"PJM": _entry(snapshot=False, provenance=False)}, version=1
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [], "legacy manifests are grandfathered, not failed")
        self.assertTrue(any("LEGACY v1" in n for n in notes))

    def test_legacy_tag_that_opts_in_is_enforced(self):
        """Migrating a legacy manifest to v2 subjects it to the full check."""
        tag = sorted(cgm.LEGACY_V1_MANIFESTS)[0]
        p = self._write(tag, {"PJM": _entry(snapshot=False)}, version=2)
        fails, _ = cgm.check_manifest(p)
        self.assertTrue(any("keeper_snapshot" in f for f in fails))

    def test_snapshot_of_the_wrong_run_is_rejected(self):
        e = _entry()
        e["keeper_snapshot"]["id"] = "2026-01-01-someone-else"
        p = self._write("s1", {"PJM": e})
        fails, _ = cgm.check_manifest(p)
        self.assertTrue(any("keeper_snapshot.id" in f for f in fails))

    def test_stale_vs_current_is_reported_not_failed(self):
        (self.keepers / "PJM.json").write_text(
            json.dumps({"keeper": "2026-06-06-newer"})
        )
        p = self._write("s1", {"PJM": _entry()})
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        self.assertTrue(any("golden STALE" in n for n in notes))

    def test_current_keeper_is_reported_current(self):
        (self.keepers / "PJM.json").write_text(json.dumps({"keeper": "2026-01-01-x-1"}))
        (self.registry / "2026-01-01-x-1.json").write_text("{}")
        p = self._write("s1", {"PJM": _entry()})
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        self.assertTrue(any("golden CURRENT" in n for n in notes))


class CaptureToolSchemaTest(unittest.TestCase):
    """The capture tool can only write schema v2, and only its own entry."""

    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "capture_keeper_goldens_schema",
            str(REPO_ROOT / "scripts" / "capture_keeper_goldens.py"),
        )
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
        self._tmp = tempfile.TemporaryDirectory()
        self._saved_root = self.mod.GOLDENS_ROOT
        self.mod.GOLDENS_ROOT = Path(self._tmp.name)

    def tearDown(self):
        self.mod.GOLDENS_ROOT = self._saved_root
        self._tmp.cleanup()

    def test_write_manifest_emits_v2_and_no_shared_sha(self):
        p = self.mod.write_manifest("t", {"PJM": _entry()})
        man = json.loads(p.read_text())
        self.assertEqual(man["schema_version"], self.mod.MANIFEST_SCHEMA_VERSION)
        for key in cgm.FORBIDDEN_TOP_LEVEL_KEYS:
            self.assertNotIn(key, man)

    def test_a_second_capture_never_touches_the_first_entry(self):
        """The exact regression: PJM's capture re-labelled five older ones."""
        first = _entry(keeper_id="2026-01-01-a", iso="CAISO")
        first["provenance"]["git_sha"] = "aaaaaaa"
        self.mod.write_manifest("t", {"CAISO": first})

        second = _entry(keeper_id="2026-02-02-b", iso="PJM")
        second["provenance"]["git_sha"] = "bbbbbbb"
        p = self.mod.write_manifest("t", {"PJM": second})

        man = json.loads(p.read_text())
        self.assertEqual(man["keepers"]["CAISO"]["provenance"]["git_sha"], "aaaaaaa")
        self.assertEqual(man["keepers"]["PJM"]["provenance"]["git_sha"], "bbbbbbb")
        self.assertEqual(man["keepers"]["CAISO"], first)

    def test_basis_sha_helper_is_origin_durable(self):
        """basis_sha must resolve in main even when git_sha is a branch commit."""
        basis = self.mod._basis_sha()
        self.assertNotEqual(basis, "unknown")
        self.assertEqual(len(basis), 40, "basis_sha must be a full sha")


if __name__ == "__main__":
    unittest.main()
