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

and, since 2026-09-02, the additive **config-partition** representation
(``docs/FINDING-golden-partition-carveout-2026-09.md``): an ISO whose keeper
shard designates more than one config (ERCOT — a forward config for
{2024, 2025} plus a 2023 carve-out) gets one sibling entry per config, keyed
``<ISO>__<role>``, and ``live_keeper`` resolves that key through
``config_partition.configs[].run_id``. The tests below pin both the key algebra
in the capture tool and the gate's staleness lookup, including the property the
whole design rests on: adding a partition entry leaves the bare-ISO entry
byte-identical.

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
        """Captures at different trees must not share one stamp.

        This is the property the v1 schema could not express: it is what makes a
        re-stamp detectable rather than silent.

        Keyed on ``(git_sha, recorded_at)`` rather than the sha alone. Since one
        ISO can hold two entries (a config partition), two configs captured in
        the SAME session legitimately share a git_sha — a v1 re-stamp, by
        contrast, would collapse the timestamps too, because it overwrote one
        shared block.
        """
        stamps = [
            (e["provenance"]["git_sha"], e["provenance"]["recorded_at"])
            for e in self.man["keepers"].values()
        ]
        self.assertEqual(
            len(set(stamps)), len(stamps), f"provenance is not per-capture: {stamps}"
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

    def test_partition_entries_agree_with_the_keeper_shard(self):
        """A ``<ISO>__<role>`` entry names a config its ISO actually designates.

        The whole point of deriving the key from the shard: the entry cannot
        drift into naming a config that was never ruled.
        """
        found = 0
        for key, entry in self.man["keepers"].items():
            if cgm.PARTITION_KEY_SEP not in key:
                continue
            found += 1
            with self.subTest(key=key):
                iso, _, role = key.partition(cgm.PARTITION_KEY_SEP)
                part = entry.get("partition")
                self.assertIsInstance(
                    part, dict, f"{key}: partition entry needs a 'partition' block"
                )
                self.assertEqual(part["iso"], iso)
                self.assertEqual(part["role"], role)
                self.assertEqual(
                    cgm.live_keeper(key),
                    entry["keeper_id"],
                    f"{key}: shard does not designate this run for that role",
                )
        self.assertGreaterEqual(
            found, 1, "expected at least the ERCOT 2023 carve-out partition entry"
        )

    def test_the_ercot_partition_covers_the_year_the_forward_entry_does_not(self):
        """Full ERCOT coverage is 7-not-6: both designated configs are captured.

        Coverage is over DESIGNATED spans (keepers/ERCOT.json coverage_invariant),
        not the runs' registered spans — the forward keeper's bundle is 3-year
        but 2023 is designated to the carve-out.
        """
        keepers = self.man["keepers"]
        self.assertIn("ERCOT", keepers, "the forward entry must stay in place")
        self.assertIn("ERCOT__carveout-2023", keepers)
        carve = keepers["ERCOT__carveout-2023"]
        self.assertEqual(carve["partition"]["designated_years"], [2023])
        # Rule 22: the capture replays the carve-out's REGISTERED span only.
        self.assertEqual(carve["years"], [2023])


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


class PartitionStalenessLookupTest(unittest.TestCase):
    """``live_keeper`` resolves both key forms; no regression on bare ISOs."""

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
        self._write_shard()

    def tearDown(self):
        cgm.REPO, cgm.GOLDENS_ROOT, cgm.REGISTRY_DIR, cgm.KEEPERS_DIR = self._saved
        self._tmp.cleanup()

    def _write_shard(self, **over):
        shard = {
            "iso": "ERCOT",
            "keeper": "run-forward",
            "config_partition": {
                "declared": "2026-08-26",
                "configs": [
                    {"role": "forward", "run_id": "run-forward", "years": [2024, 2025]},
                    {
                        "role": "carveout-2023",
                        "run_id": "run-carveout",
                        "years": [2023],
                    },
                ],
            },
        }
        shard.update(over)
        (self.keepers / "ERCOT.json").write_text(json.dumps(shard))

    def _manifest(self, keepers, tag="s1"):
        p = self.goldens / tag / "manifest.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps({"schema_version": 2, "stage_tag": tag, "keepers": keepers})
        )
        return p

    # --- resolution ---

    def test_bare_iso_still_resolves_through_the_keeper_field(self):
        """The six existing entries must be unaffected by the new key form."""
        self.assertEqual(cgm.live_keeper("ERCOT"), "run-forward")

    def test_partition_key_resolves_through_config_partition(self):
        self.assertEqual(cgm.live_keeper("ERCOT__carveout-2023"), "run-carveout")
        self.assertEqual(cgm.live_keeper("ERCOT__forward"), "run-forward")

    def test_role_match_is_case_insensitive_and_iso_half_is_upcased(self):
        self.assertEqual(cgm.live_keeper("ercot__CARVEOUT-2023"), "run-carveout")

    def test_unknown_role_resolves_to_none(self):
        self.assertIsNone(cgm.live_keeper("ERCOT__no-such-role"))

    def test_iso_without_a_partition_block_resolves_only_the_bare_key(self):
        (self.keepers / "PJM.json").write_text(
            json.dumps({"iso": "PJM", "keeper": "run-pjm"})
        )
        self.assertEqual(cgm.live_keeper("PJM"), "run-pjm")
        self.assertIsNone(cgm.live_keeper("PJM__carveout-2023"))

    def test_missing_or_unreadable_shard_resolves_to_none(self):
        self.assertIsNone(cgm.live_keeper("MISO"))
        self.assertIsNone(cgm.live_keeper("MISO__forward"))
        (self.keepers / "NYISO.json").write_text("{not json")
        self.assertIsNone(cgm.live_keeper("NYISO"))

    # --- reporting ---

    def test_current_partition_entry_reports_current(self):
        (self.registry / "run-carveout.json").write_text("{}")
        p = self._manifest(
            {"ERCOT__carveout-2023": _entry(keeper_id="run-carveout", iso="ERCOT")}
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        self.assertTrue(any("golden CURRENT" in n for n in notes))
        self.assertTrue(any("ERCOT__carveout-2023" in n for n in notes))

    def test_superseded_partition_member_reports_stale_with_the_live_run(self):
        self._write_shard(
            config_partition={
                "configs": [
                    {"role": "carveout-2023", "run_id": "run-newer", "years": [2023]}
                ]
            }
        )
        p = self._manifest(
            {"ERCOT__carveout-2023": _entry(keeper_id="run-carveout", iso="ERCOT")}
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        self.assertTrue(
            any("golden STALE (live keeper: run-newer)" in n for n in notes)
        )

    def test_retired_role_says_so_instead_of_live_keeper_none(self):
        """A retired role must not read like an ordinary supersession."""
        self._write_shard(config_partition={"configs": []})
        p = self._manifest(
            {"ERCOT__carveout-2023": _entry(keeper_id="run-carveout", iso="ERCOT")}
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        joined = " ".join(notes)
        self.assertIn("designates no config_partition role 'carveout-2023'", joined)
        self.assertNotIn("live keeper: None", joined)

    def test_partition_entry_is_held_to_every_v2_invariant(self):
        """Additive means the existing enforcement applies unchanged."""
        p = self._manifest(
            {
                "ERCOT__carveout-2023": _entry(
                    keeper_id="run-carveout", iso="ERCOT", snapshot=False
                )
            }
        )
        fails, _ = cgm.check_manifest(p)
        self.assertTrue(any("keeper_snapshot" in f for f in fails))
        self.assertTrue(any("ERCOT__carveout-2023" in f for f in fails))

    def test_partition_entry_survives_a_pruned_sidecar_via_its_snapshot(self):
        p = self._manifest(
            {"ERCOT__carveout-2023": _entry(keeper_id="run-carveout", iso="ERCOT")}
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        self.assertTrue(any("PRUNED from registry" in n for n in notes))

    def test_both_configs_of_one_iso_are_reported_side_by_side(self):
        """The coverage the bare-ISO keying could not express."""
        (self.registry / "run-forward.json").write_text("{}")
        (self.registry / "run-carveout.json").write_text("{}")
        p = self._manifest(
            {
                "ERCOT": _entry(keeper_id="run-forward", iso="ERCOT"),
                "ERCOT__carveout-2023": _entry(keeper_id="run-carveout", iso="ERCOT"),
            }
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        current = [n for n in notes if "golden CURRENT" in n]
        self.assertEqual(len(current), 2, current)


class PartitionCaptureKeyTest(unittest.TestCase):
    """The capture tool's key algebra and partition resolution."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "capture_keeper_goldens_partition",
            str(REPO_ROOT / "scripts" / "capture_keeper_goldens.py"),
        )
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def test_key_round_trip(self):
        m = self.mod
        self.assertEqual(m.parse_capture_key("NEISO"), ("NEISO", None))
        self.assertEqual(
            m.parse_capture_key("ERCOT__carveout-2023"), ("ERCOT", "carveout-2023")
        )
        self.assertEqual(m.parse_capture_key("ercot"), ("ERCOT", None))
        self.assertEqual(m.capture_key("ercot"), "ERCOT")
        self.assertEqual(
            m.capture_key("ercot", "carveout-2023"), "ERCOT__carveout-2023"
        )

    def test_partition_key_does_not_collide_with_the_bare_key(self):
        """Blocker 2/3 of the finding: golden dir and manifest key both derive
        from this string, so a collision would overwrite the forward capture."""
        m = self.mod
        self.assertNotEqual(m.capture_key("ERCOT"), m.capture_key("ERCOT", "forward"))

    def test_live_ercot_shard_declares_both_configs(self):
        roles = [c["role"] for c in self.mod.partition_configs("ERCOT")]
        self.assertIn("forward", roles)
        self.assertIn("carveout-2023", roles)

    def test_partition_run_id_resolves_the_carveout(self):
        m = self.mod
        self.assertEqual(
            m.partition_run_id("ERCOT", "carveout-2023"),
            "2026-08-25-236-swcap-clip-k33",
        )
        self.assertIsNone(m.partition_run_id("ERCOT", "no-such-role"))
        self.assertEqual(self.mod.partition_configs("PJM"), [])

    def test_resolve_capture_targets_reaches_the_carveout_bundle(self):
        """Blocker 1: the carve-out was unreachable through keeper_list()."""
        info = self.mod.resolve_capture_targets(["ERCOT__carveout-2023"])[
            "ERCOT__carveout-2023"
        ]
        self.assertEqual(info["keeper_id"], "2026-08-25-236-swcap-clip-k33")
        self.assertEqual(info["iso"], "ERCOT")
        self.assertEqual(info["role"], "carveout-2023")
        # Rule 22: the run's own REGISTERED span, never widened.
        self.assertEqual(info["years"], [2023])

    def test_resolve_capture_targets_still_handles_a_bare_iso(self):
        info = self.mod.resolve_capture_targets(["ERCOT"])["ERCOT"]
        self.assertIsNone(info["role"])
        self.assertIsNone(info["partition_config"])
        self.assertEqual(
            info["keeper_id"], cgm.live_keeper("ERCOT"), "bare key = designated keeper"
        )

    def test_an_undesignated_role_fails_loud(self):
        """A typo must never write a golden the gate then calls STALE forever."""
        with self.assertRaises(KeyError) as ctx:
            self.mod.resolve_capture_targets(["ERCOT__carvout-2023"])
        msg = str(ctx.exception)
        self.assertIn("carvout-2023", msg)
        self.assertIn("carveout-2023", msg, "the error should list the real roles")

    def test_partition_block_separates_designated_from_registered_years(self):
        m = self.mod
        info = m.resolve_capture_targets(["ERCOT__forward"])["ERCOT__forward"]
        block = m._partition_block(info)
        self.assertEqual(block["role"], "forward")
        self.assertEqual(block["designated_years"], [2024, 2025])
        # ...while the run it replays is registered 3-year. Conflating the two
        # is the gloss FINDING-stage0-capture-neiso-ercot-2026-09 §2 warns of.
        self.assertEqual(info["years"], [2023, 2024, 2025])

    def test_partition_block_is_absent_for_a_bare_capture(self):
        info = self.mod.resolve_capture_targets(["NEISO"])["NEISO"]
        self.assertIsNone(self.mod._partition_block(info))


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

    def test_a_partition_capture_leaves_the_bare_iso_entry_byte_identical(self):
        """THE additive property the whole schema decision rests on.

        Capturing ERCOT's 2023 carve-out must not move one byte of the forward
        entry — the dispatch's explicit requirement, and what makes this a
        schema EXTENSION rather than a rewrite.
        """
        forward = _entry(keeper_id="2026-08-25-234-eastex-identity", iso="ERCOT")
        self.mod.write_manifest("t", {"ERCOT": forward})
        before = json.loads(
            (self.mod.GOLDENS_ROOT / "t" / "manifest.json").read_text()
        )["keepers"]["ERCOT"]

        carve = _entry(keeper_id="2026-08-25-236-swcap-clip-k33", iso="ERCOT")
        carve["partition"] = {
            "iso": "ERCOT",
            "role": "carveout-2023",
            "designated_years": [2023],
        }
        p = self.mod.write_manifest("t", {"ERCOT__carveout-2023": carve})

        man = json.loads(p.read_text())
        self.assertEqual(man["keepers"]["ERCOT"], before)
        self.assertEqual(man["keepers"]["ERCOT"], forward)
        self.assertEqual(
            man["keepers"]["ERCOT__carveout-2023"]["keeper_id"],
            "2026-08-25-236-swcap-clip-k33",
        )
        self.assertEqual(sorted(man["keepers"]), ["ERCOT", "ERCOT__carveout-2023"])

    def test_basis_sha_helper_is_origin_durable(self):
        """basis_sha must resolve in main even when git_sha is a branch commit."""
        basis = self.mod._basis_sha()
        self.assertNotEqual(basis, "unknown")
        self.assertEqual(len(basis), 40, "basis_sha must be a full sha")


if __name__ == "__main__":
    unittest.main()
