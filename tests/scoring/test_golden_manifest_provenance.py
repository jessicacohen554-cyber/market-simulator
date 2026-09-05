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

and, since 2026-09-05, **R-AW** (owner ruling, verbatim *"The golden config
should be the 2024:2025 one not 2023"*;
``docs/handoffs/FINDING-y14-ercot-golden-forward-2026-09-05.md``): a
partitioned ISO's BARE key is its ``forward`` role replayed on that role's
designated span (never the composed run's whole registered span), a designated
span is never a superset of the registered span (rule 22, asserted in both
scripts and the gate), and the ``ERCOT__carveout-2023`` capture key is RETIRED
— its historical manifest entries stay as written and are reported, not
compared to the live shard.

``check_golden_manifest`` is loaded by path (it is a loose ``scripts/`` module)
and its directory constants are monkeypatched per test onto temp trees, so no
test reads or writes the real registry.
"""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPO_ROOT


def _load_script(name: str, path: Path):
    """Execute a loose ``scripts/`` module by path WITHOUT leaking its import-time
    environment into the test process.

    ``capture_keeper_goldens.py`` pins ``DETERMINISM_ENV``
    (``MARKET_SIM_HIGHS_THREADS=1``, the WARMSTART pair) into ``os.environ`` at
    import — correct for its own CLI process, where it must precede any solve.
    Executed here it leaked into the whole pytest process: every LP built
    afterwards by ``model/lp/model.py`` set ``threads=1`` against a HiGHS global
    scheduler that an earlier test had already initialized at the default, and
    HiGHS refused every one of them (``Option 'threads' is set to 1 but global
    scheduler has already been initialized to use N threads`` → status ``Not
    Set`` → ``dispatch LP has no feasible primal solution``). That is 203 of
    the tier's LP tests in a serial run and 24–79 in whichever xdist worker
    this file lands in — scheduling-dependent, so a latent CI red, and the
    reason a local count of the tier over-reads ``main`` (fast-tier repair,
    2026-09-02, ``docs/FINDING-fast-tier-repair-2026-09.md`` §4). The
    environment is snapshotted before ``exec_module`` and restored after it,
    added keys included, so the script's own pin never outlives its import.
    """
    saved = dict(os.environ)
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    return mod


cgm = _load_script(
    "check_golden_manifest", REPO_ROOT / "scripts" / "check_golden_manifest.py"
)

LIVE_MANIFEST = (
    REPO_ROOT / "results" / "regression-goldens" / "perfb-stage0" / "manifest.json"
)
LIVE_ERCOT_SHARD = (
    REPO_ROOT / "frontend" / "data" / "backcast" / "keepers" / "ERCOT.json"
)
LIVE_REGISTRY = REPO_ROOT / "frontend" / "data" / "backcast" / "registry"

# R-AW's object, spelled out once: the retired key, the role the bare key now
# resolves to, and that role's designated span.
RETIRED_KEY = "ERCOT__carveout-2023"
FORWARD_SPAN = [2024, 2025]


def _entry(
    keeper_id="2026-01-01-x-1",
    iso="PJM",
    *,
    snapshot=True,
    provenance=True,
    years=(2023, 2024, 2025),
):
    """Return a minimal well-formed schema-v2 manifest entry."""
    years = list(years)
    e = {
        "keeper_id": keeper_id,
        "bundle": "results/calibration/x_1",
        "years": years,
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
            "years": years,
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

        Two cases since R-AW (2026-09-05; replaces the Y-11 STOP that held this
        test red after the ercot-248 consolidation re-keyed both roles onto one
        run):

        * a LIVE partition key must still name the run the shard designates
          for that role — the original assertion, unchanged;
        * a RETIRED key (``check_golden_manifest.RETIRED_CAPTURE_KEYS``) is a
          historical capture record. Its ``keeper_id`` records which run's
          outputs were ACTUALLY captured, so it is never re-keyed to the live
          designation; instead it must (a) be retired by the gate's constant,
          (b) carry a ``retired`` block citing the ruling, and (c) still agree
          with the shard's PROVENANCE for that role — the consolidation kept
          the pre-consolidation run in ``source_run_id``, and that is the run
          this record captured. Stronger than a live-id equality for a record
          that, by ruling, never moves again.
        """
        shard = json.loads(LIVE_ERCOT_SHARD.read_text())
        by_role = {c["role"]: c for c in shard["config_partition"]["configs"]}
        live, retired = 0, 0
        for key, entry in self.man["keepers"].items():
            if cgm.PARTITION_KEY_SEP not in key:
                continue
            with self.subTest(key=key):
                iso, _, role = key.partition(cgm.PARTITION_KEY_SEP)
                part = entry.get("partition")
                self.assertIsInstance(
                    part, dict, f"{key}: partition entry needs a 'partition' block"
                )
                self.assertEqual(part["iso"], iso)
                self.assertEqual(part["role"], role)
                if key in cgm.RETIRED_CAPTURE_KEYS:
                    retired += 1
                    self.assertIn("R-AW", cgm.RETIRED_CAPTURE_KEYS[key])
                    ret = entry.get("retired")
                    self.assertIsInstance(ret, dict, f"{key}: needs a retired block")
                    self.assertEqual(ret["ruling"], "R-AW")
                    self.assertEqual(
                        ret["ruling_verbatim"],
                        "The golden config should be the 2024:2025 one not 2023",
                    )
                    # (c): the record still traces to the shard's provenance.
                    self.assertEqual(
                        by_role[role]["source_run_id"],
                        entry["keeper_id"],
                        f"{key}: the retired record must be the run the shard "
                        f"names as this role's source",
                    )
                    self.assertEqual(by_role[role]["source_bundle"], entry["bundle"])
                    self.assertEqual(entry["keeper_snapshot"]["id"], entry["keeper_id"])
                else:
                    live += 1
                    self.assertEqual(
                        cgm.live_keeper(key),
                        entry["keeper_id"],
                        f"{key}: shard does not designate this run for that role",
                    )
                    self.assertEqual(
                        cgm.designated_years(key), sorted(part["designated_years"])
                    )
        self.assertEqual(
            retired, 1, "expected exactly the retired ERCOT 2023 carve-out entry"
        )
        self.assertIn(RETIRED_KEY, self.man["keepers"])

    def test_the_bare_ercot_entry_is_the_forward_config_on_its_designated_span(
        self,
    ):
        """R-AW: the ERCOT stage-0 golden is the forward config on {2024, 2025}.

        Three facts, each read from the LIVE shard + registry and the
        COMMITTED manifest, so the test is green before AND after the R-AI
        re-capture (whose target this pins):

        1. the bare key resolves to the forward role, span [2024, 2025];
        2. that designated span is a strict subset of the composed run's
           registered span — rule 22, "never widened", on live data;
        3. a bare ERCOT entry that is CURRENT (i.e. the re-capture has landed)
           replays exactly that span. Today's entry is the pre-consolidation
           234 capture and reads STALE — the gate carries the same check as a
           hard failure the moment a CURRENT entry violates it.

        The retired carve-out record stays in the manifest as written
        (designated and replayed [2023] — the run's own registered span at
        capture time), and is not compared to the shard.
        """
        keepers = self.man["keepers"]
        self.assertIn("ERCOT", keepers, "the forward entry must stay in place")
        # 1.
        self.assertEqual(cgm.resolve_role("ERCOT"), ("ERCOT", cgm.FORWARD_ROLE))
        self.assertEqual(cgm.designated_years("ERCOT"), FORWARD_SPAN)
        self.assertEqual(cgm.designated_years("ERCOT__forward"), FORWARD_SPAN)
        live = cgm.live_keeper("ERCOT")
        self.assertEqual(live, cgm.live_keeper("ERCOT__forward"))
        # 2.
        reg = json.loads((LIVE_REGISTRY / f"{live}.json").read_text())
        registered = sorted(int(y) for y in reg["years"])
        self.assertLess(set(FORWARD_SPAN), set(registered))
        self.assertEqual(registered, [2023, 2024, 2025])
        # 3.
        fwd = keepers["ERCOT"]
        if fwd["keeper_id"] == live:
            self.assertEqual(sorted(fwd["years"]), FORWARD_SPAN)
            self.assertEqual(sorted(fwd["registered_years"]), registered)
            self.assertEqual(fwd["partition"]["role"], cgm.FORWARD_ROLE)
        else:
            # Pre-re-capture: STALE by id, and the span it replayed was its
            # own run's registered span — still inside rule 22.
            self.assertLessEqual(
                set(fwd["years"]), set(fwd["keeper_snapshot"]["years"])
            )
        carve = keepers[RETIRED_KEY]
        self.assertEqual(carve["partition"]["designated_years"], [2023])
        self.assertEqual(carve["years"], [2023])
        self.assertIn(RETIRED_KEY, cgm.RETIRED_CAPTURE_KEYS)
        # Every year of the training window is covered by exactly one
        # designated config (keepers/ERCOT.json coverage_invariant); the golden
        # program captures the forward one, by ruling.
        self.assertEqual(
            sorted(set(FORWARD_SPAN) | set(carve["partition"]["designated_years"])),
            registered,
        )


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
    """``live_keeper`` resolves both key forms; no regression on bare ISOs.

    The temp shard uses a hypothetical second role, ``carveout-x``, rather
    than the real ``carveout-2023``: that key is RETIRED by R-AW and takes the
    gate's historical-record branch, which has its own tests below. The
    generic partition mechanics must stay tested independently of one ruling.
    """

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
                        "role": "carveout-x",
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

    def test_bare_key_of_a_partitioned_iso_is_its_forward_role(self):
        """R-AW: the bare key IS the forward role — role, run id and span.

        When the ``keeper`` field and the forward role's ``run_id`` ever
        disagree, the role the ruling names wins, so a golden captured under
        the bare key is compared against the forward config, not against
        whatever the headline field happens to say.
        """
        self.assertEqual(cgm.resolve_role("ERCOT"), ("ERCOT", "forward"))
        self.assertEqual(cgm.designated_years("ERCOT"), [2024, 2025])
        self._write_shard(keeper="run-headline")
        self.assertEqual(cgm.live_keeper("ERCOT"), "run-forward")

    def test_partition_without_a_forward_role_falls_back_to_the_keeper_field(self):
        self._write_shard(
            config_partition={
                "configs": [{"role": "carveout-x", "run_id": "run-carveout"}]
            }
        )
        self.assertEqual(cgm.resolve_role("ERCOT"), ("ERCOT", None))
        self.assertEqual(cgm.live_keeper("ERCOT"), "run-forward")
        self.assertIsNone(cgm.designated_years("ERCOT"))

    def test_partition_key_resolves_through_config_partition(self):
        self.assertEqual(cgm.live_keeper("ERCOT__carveout-x"), "run-carveout")
        self.assertEqual(cgm.live_keeper("ERCOT__forward"), "run-forward")
        self.assertEqual(cgm.designated_years("ERCOT__carveout-x"), [2023])
        self.assertEqual(cgm.designated_years("ERCOT__forward"), [2024, 2025])

    def test_role_match_is_case_insensitive_and_iso_half_is_upcased(self):
        self.assertEqual(cgm.live_keeper("ercot__CARVEOUT-X"), "run-carveout")

    def test_unknown_role_resolves_to_none(self):
        self.assertIsNone(cgm.live_keeper("ERCOT__no-such-role"))
        self.assertIsNone(cgm.designated_years("ERCOT__no-such-role"))

    def test_iso_without_a_partition_block_resolves_only_the_bare_key(self):
        (self.keepers / "PJM.json").write_text(
            json.dumps({"iso": "PJM", "keeper": "run-pjm"})
        )
        self.assertEqual(cgm.live_keeper("PJM"), "run-pjm")
        self.assertEqual(cgm.resolve_role("PJM"), ("PJM", None))
        self.assertIsNone(cgm.designated_years("PJM"))
        self.assertIsNone(cgm.live_keeper("PJM__carveout-x"))

    def test_missing_or_unreadable_shard_resolves_to_none(self):
        self.assertIsNone(cgm.live_keeper("MISO"))
        self.assertIsNone(cgm.live_keeper("MISO__forward"))
        (self.keepers / "NYISO.json").write_text("{not json")
        self.assertIsNone(cgm.live_keeper("NYISO"))

    # --- reporting ---

    def test_current_partition_entry_reports_current(self):
        (self.registry / "run-carveout.json").write_text("{}")
        p = self._manifest(
            {
                "ERCOT__carveout-x": _entry(
                    keeper_id="run-carveout", iso="ERCOT", years=[2023]
                )
            }
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        self.assertTrue(any("golden CURRENT" in n for n in notes))
        self.assertTrue(any("ERCOT__carveout-x" in n for n in notes))

    def test_superseded_partition_member_reports_stale_with_the_live_run(self):
        self._write_shard(
            config_partition={
                "configs": [
                    {"role": "carveout-x", "run_id": "run-newer", "years": [2023]}
                ]
            }
        )
        p = self._manifest(
            {"ERCOT__carveout-x": _entry(keeper_id="run-carveout", iso="ERCOT")}
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        self.assertTrue(
            any("golden STALE (live keeper: run-newer)" in n for n in notes)
        )

    def test_undesignated_role_says_so_instead_of_live_keeper_none(self):
        """An un-ruled role must not read like an ordinary supersession."""
        self._write_shard(config_partition={"configs": []})
        p = self._manifest(
            {"ERCOT__carveout-x": _entry(keeper_id="run-carveout", iso="ERCOT")}
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        joined = " ".join(notes)
        self.assertIn("designates no config_partition role 'carveout-x'", joined)
        self.assertNotIn("live keeper: None", joined)

    def test_partition_entry_is_held_to_every_v2_invariant(self):
        """Additive means the existing enforcement applies unchanged."""
        p = self._manifest(
            {
                "ERCOT__carveout-x": _entry(
                    keeper_id="run-carveout", iso="ERCOT", snapshot=False
                )
            }
        )
        fails, _ = cgm.check_manifest(p)
        self.assertTrue(any("keeper_snapshot" in f for f in fails))
        self.assertTrue(any("ERCOT__carveout-x" in f for f in fails))

    def test_partition_entry_survives_a_pruned_sidecar_via_its_snapshot(self):
        p = self._manifest(
            {
                "ERCOT__carveout-x": _entry(
                    keeper_id="run-carveout", iso="ERCOT", years=[2023]
                )
            }
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
                "ERCOT": _entry(
                    keeper_id="run-forward", iso="ERCOT", years=[2024, 2025]
                ),
                "ERCOT__carveout-x": _entry(
                    keeper_id="run-carveout", iso="ERCOT", years=[2023]
                ),
            }
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        current = [n for n in notes if "golden CURRENT" in n]
        self.assertEqual(len(current), 2, current)

    # --- R-AW: designated span, rule-22 inclusion, retired keys ---

    def test_current_bare_entry_of_a_partitioned_iso_must_replay_the_forward_span(
        self,
    ):
        """The defect R-AW's enforcement exists to stop: a CURRENT bare golden
        that replayed the composed run's whole registered span — i.e. the
        carve-out year under the forward config."""
        (self.registry / "run-forward.json").write_text("{}")
        p = self._manifest(
            {
                "ERCOT": _entry(
                    keeper_id="run-forward", iso="ERCOT", years=[2023, 2024, 2025]
                )
            }
        )
        fails, _ = cgm.check_manifest(p)
        self.assertTrue(fails, "a whole-span forward golden must FAIL")
        joined = " ".join(fails)
        self.assertIn("designates [2024, 2025]", joined)
        self.assertIn("role 'forward'", joined)
        self.assertIn("R-AW", joined)

    def test_current_partition_key_entry_must_replay_its_designated_span(self):
        (self.registry / "run-carveout.json").write_text("{}")
        p = self._manifest(
            {
                "ERCOT__carveout-x": _entry(
                    keeper_id="run-carveout", iso="ERCOT", years=[2023, 2024]
                )
            }
        )
        fails, _ = cgm.check_manifest(p)
        self.assertTrue(any("designates [2023]" in f for f in fails))

    def test_stale_entries_are_never_held_to_the_designated_span(self):
        """Historical captures replayed what their own run registered; the
        span rule binds only what is compared as CURRENT."""
        p = self._manifest(
            {
                "ERCOT": _entry(
                    keeper_id="run-older", iso="ERCOT", years=[2023, 2024, 2025]
                )
            }
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        self.assertTrue(
            any("golden STALE (live keeper: run-forward)" in n for n in notes)
        )

    def test_non_partitioned_iso_is_unconstrained_by_the_span_rule(self):
        (self.keepers / "PJM.json").write_text(json.dumps({"keeper": "run-pjm"}))
        (self.registry / "run-pjm.json").write_text("{}")
        p = self._manifest({"PJM": _entry(keeper_id="run-pjm", iso="PJM")})
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        self.assertTrue(any("golden CURRENT" in n for n in notes))

    def test_years_must_be_inside_registered_years_when_recorded(self):
        """Rule 22 on the entry itself: the slice is never wider than the run."""
        (self.registry / "run-forward.json").write_text("{}")
        good = _entry(keeper_id="run-forward", iso="ERCOT", years=[2024, 2025])
        good["registered_years"] = [2023, 2024, 2025]
        fails, _ = cgm.check_manifest(self._manifest({"ERCOT": good}))
        self.assertEqual(fails, [])
        bad = _entry(keeper_id="run-forward", iso="ERCOT", years=[2024, 2025])
        bad["registered_years"] = [2024]
        fails, _ = cgm.check_manifest(self._manifest({"ERCOT": bad}, tag="s2"))
        self.assertTrue(any("never a superset" in f for f in fails))

    def test_retired_key_is_validated_but_not_compared_to_the_shard(self):
        """R-AW: a retired key's entry is a historical capture record.

        The shard has moved on (it designates ``run-newer`` for the role) and
        the entry's keeper_id is the run that was ACTUALLY captured; the gate
        must neither fail it nor call it STALE, only report it as retired —
        while still holding it to every v2 invariant.
        """
        self.assertIn("ERCOT__carveout-2023", cgm.RETIRED_CAPTURE_KEYS)
        self._write_shard(
            config_partition={
                "configs": [
                    {"role": "forward", "run_id": "run-forward", "years": [2024, 2025]},
                    {"role": "carveout-2023", "run_id": "run-newer", "years": [2023]},
                ]
            }
        )
        p = self._manifest(
            {
                "ERCOT__carveout-2023": _entry(
                    keeper_id="run-carveout", iso="ERCOT", years=[2023]
                )
            }
        )
        fails, notes = cgm.check_manifest(p)
        self.assertEqual(fails, [])
        joined = " ".join(notes)
        self.assertIn("capture key RETIRED (R-AW", joined)
        self.assertIn("historical capture record", joined)
        self.assertIn("carries no retired block", joined)
        self.assertNotIn("golden STALE", joined)
        self.assertNotIn("golden CURRENT", joined)
        # Still every v2 invariant: no snapshot → hard failure, retired or not.
        p = self._manifest(
            {
                "ERCOT__carveout-2023": _entry(
                    keeper_id="run-carveout", iso="ERCOT", snapshot=False
                )
            },
            tag="s2",
        )
        fails, _ = cgm.check_manifest(p)
        self.assertTrue(any("keeper_snapshot" in f for f in fails))

    def test_retired_key_with_a_retired_block_is_reported_as_marked(self):
        e = _entry(keeper_id="run-carveout", iso="ERCOT", years=[2023])
        e["retired"] = {"declared": "2026-09-05", "ruling": "R-AW"}
        fails, notes = cgm.check_manifest(self._manifest({"ERCOT__carveout-2023": e}))
        self.assertEqual(fails, [])
        joined = " ".join(notes)
        self.assertIn("capture key RETIRED", joined)
        self.assertNotIn("carries no retired block", joined)


class PartitionCaptureKeyTest(unittest.TestCase):
    """The capture tool's key algebra and partition resolution."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_script(
            "capture_keeper_goldens_partition",
            REPO_ROOT / "scripts" / "capture_keeper_goldens.py",
        )

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
        """The SHARD still designates both configs — R-AW retired the carve-out
        CAPTURE KEY, not the keeper's 2023 designation."""
        roles = [c["role"] for c in self.mod.partition_configs("ERCOT")]
        self.assertIn("forward", roles)
        self.assertIn("carveout-2023", roles)

    def test_partition_run_id_resolves_the_carveout(self):
        # 2026-09-05, re-pinned by the Y-11 fast-tier pin lane: session
        # ercot-248 executed the owner's consolidation instruction (verbatim in
        # keepers/ERCOT.json config_partition.consolidation.ruling) and re-keyed
        # BOTH partition roles onto the one composed run. This assertion reads
        # only "the shard designates X for this role", so it restates the
        # owner-ruled designation and nothing else; the per-role config
        # distinction is preserved in the shard's source_run_id / source_bundle
        # (carve-out <- 2026-08-25-236-swcap-clip-k33, forward <-
        # 2026-08-25-234-eastex-identity), which is why this is a pin refresh
        # and not a semantic change.
        m = self.mod
        self.assertEqual(
            m.partition_run_id("ERCOT", "carveout-2023"),
            "2026-09-05-ercot248-two-config-keeper",
        )
        self.assertIsNone(m.partition_run_id("ERCOT", "no-such-role"))
        self.assertEqual(self.mod.partition_configs("PJM"), [])

    def test_retired_key_is_shared_with_the_gate_and_refused(self):
        """R-AW: the ERCOT__carveout-2023 capture key is retired.

        Replaces ``test_resolve_capture_targets_reaches_the_carveout_bundle``
        (the Y-11 STOP). The capture tool reads the retired-key table FROM the
        gate, so the two cannot disagree, and refuses the key loudly with the
        ruling in the message — a new golden can never be written under it.
        """
        m = self.mod
        # (cgm is loaded by path, so a distinct module object: equality, not
        # identity, is the testable statement of "one table".)
        self.assertEqual(m.RETIRED_CAPTURE_KEYS, cgm.RETIRED_CAPTURE_KEYS)
        self.assertEqual(m.FORWARD_ROLE, cgm.FORWARD_ROLE)
        self.assertIn("ERCOT__carveout-2023", m.RETIRED_CAPTURE_KEYS)
        with self.assertRaises(KeyError) as ctx:
            m.resolve_capture_targets(["ERCOT__carveout-2023"])
        msg = str(ctx.exception)
        self.assertIn("RETIRED", msg)
        self.assertIn("R-AW", msg)
        self.assertIn("2024:2025", msg)
        # Case-normalized on the ISO half, exactly like every other key.
        with self.assertRaises(KeyError):
            m.resolve_capture_targets(["ercot__carveout-2023"])

    def test_bare_ercot_resolves_to_the_forward_config_on_its_designated_span(
        self,
    ):
        """R-AW's target, well-defined for the R-AI re-capture lane.

        The bare key is the forward role: the composed run's REGISTERED bundle
        (the only ERCOT run with a live sidecar; its meta.json is the forward
        config verbatim — ercot248 composite_provenance.json) sliced to the
        forward role's designated [2024, 2025], with the run's registered
        3-year span kept beside it. Rule 22's guard is now an inclusion, held
        on both the resolved info and the manifest entry: the designated span
        is a strict subset of the registered span, never wider.
        """
        m = self.mod
        info = m.resolve_capture_targets(["ERCOT"])["ERCOT"]
        self.assertEqual(info["iso"], "ERCOT")
        self.assertEqual(info["role"], m.FORWARD_ROLE)
        self.assertEqual(info["role"], "forward")
        self.assertEqual(info["keeper_id"], "2026-09-05-ercot248-two-config-keeper")
        self.assertEqual(
            info["keeper_id"], cgm.live_keeper("ERCOT"), "bare key = designated keeper"
        )
        self.assertEqual(
            info["bundle"], REPO_ROOT / "results/calibration/ercot248_two_config_keeper"
        )
        self.assertEqual(info["years"], [2024, 2025])
        self.assertEqual(info["registered_years"], [2023, 2024, 2025])
        self.assertLess(set(info["years"]), set(info["registered_years"]))
        self.assertEqual(info["partition_config"]["role"], "forward")
        # The gate agrees on every one of these.
        self.assertEqual(cgm.designated_years("ERCOT"), info["years"])
        self.assertEqual(cgm.resolve_role("ERCOT"), ("ERCOT", info["role"]))
        # The snapshot the entry will absorb replays the same slice and keeps
        # the sidecar's span, so the slice stays visible after the prune.
        snap = m._keeper_snapshot(info)
        self.assertEqual(snap["years"], [2024, 2025])
        self.assertEqual(snap["registered_years"], [2023, 2024, 2025])
        self.assertEqual(snap["sidecar_at_capture"], "present")
        self.assertEqual(snap["iso"], "ERCOT")

    def test_ercot_forward_key_is_the_same_capture_as_the_bare_key(self):
        m = self.mod
        bare = m.resolve_capture_targets(["ERCOT"])["ERCOT"]
        fwd = m.resolve_capture_targets(["ERCOT__forward"])["ERCOT__forward"]
        for k in ("keeper_id", "bundle", "years", "registered_years", "role"):
            self.assertEqual(bare[k], fwd[k], k)
        self.assertEqual(m._partition_block(bare), m._partition_block(fwd))

    def test_resolve_capture_targets_still_handles_a_bare_iso(self):
        """A one-config ISO is untouched: no role, no block, registered span."""
        info = self.mod.resolve_capture_targets(["NEISO"])["NEISO"]
        self.assertIsNone(info["role"])
        self.assertIsNone(info["partition_config"])
        self.assertNotIn("registered_years", info)
        self.assertEqual(
            info["keeper_id"], cgm.live_keeper("NEISO"), "bare key = designated keeper"
        )
        self.assertEqual(info["years"], [2023, 2024, 2025])

    def test_a_designated_span_is_never_a_superset_of_the_registered_span(self):
        """Rule 22 as a hard assertion in the capture tool.

        A shard edit that designated a year the run never registered (the
        way a 2022 or 2026 solve could otherwise enter through a partition)
        must fail at resolution, before any solve.
        """
        m = self.mod
        info = {"years": [2023, 2024, 2025]}
        out = m.slice_to_designated_span(dict(info), {"years": [2024, 2025]}, what="t")
        self.assertEqual(out["years"], [2024, 2025])
        self.assertEqual(out["registered_years"], [2023, 2024, 2025])
        # Identity slice is fine (a role designated the whole span).
        out = m.slice_to_designated_span(
            dict(info), {"years": [2025, 2023, 2024]}, what="t"
        )
        self.assertEqual(out["years"], [2023, 2024, 2025])
        for bad in ([2022, 2023], [2024, 2026], [2019], []):
            with self.subTest(designated=bad), self.assertRaises(ValueError) as ctx:
                m.slice_to_designated_span(dict(info), {"years": bad}, what="t")
            if bad:
                self.assertIn("never a superset", str(ctx.exception))
        # ...and through resolve_capture_targets, against the LIVE registered
        # span, with the shard's forward config widened by one year.
        real = m.partition_configs
        widened = [
            dict(c, years=[2022, 2024, 2025]) if c["role"] == "forward" else c
            for c in real("ERCOT")
        ]
        m.partition_configs = lambda iso: widened if iso == "ERCOT" else real(iso)
        try:
            with self.assertRaises(ValueError) as ctx:
                m.resolve_capture_targets(["ERCOT"])
            self.assertIn("[2022, 2024, 2025]", str(ctx.exception))
        finally:
            m.partition_configs = real

    def test_a_partitioned_shard_without_a_forward_role_fails_loud(self):
        m = self.mod
        real = m.partition_configs
        m.partition_configs = lambda iso: (
            [c for c in real(iso) if c["role"] != "forward"]
            if iso == "ERCOT"
            else real(iso)
        )
        try:
            with self.assertRaises(KeyError) as ctx:
                m.resolve_capture_targets(["ERCOT"])
            self.assertIn("no 'forward' role", str(ctx.exception))
        finally:
            m.partition_configs = real

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
        # Since R-AW the capture REPLAYS the designated span, so the two agree
        # — while the run it replays stays registered 3-year, recorded apart.
        # Conflating designated with registered is the gloss
        # FINDING-stage0-capture-neiso-ercot-2026-09 §2 warns of.
        self.assertEqual(info["years"], block["designated_years"])
        self.assertEqual(info["registered_years"], [2023, 2024, 2025])
        # The bare key carries the same block: it IS the forward role.
        bare = m.resolve_capture_targets(["ERCOT"])["ERCOT"]
        self.assertEqual(m._partition_block(bare), block)

    def test_partition_block_is_absent_for_a_bare_capture(self):
        info = self.mod.resolve_capture_targets(["NEISO"])["NEISO"]
        self.assertIsNone(self.mod._partition_block(info))


class CaptureToolSchemaTest(unittest.TestCase):
    """The capture tool can only write schema v2, and only its own entry."""

    def setUp(self):
        self.mod = _load_script(
            "capture_keeper_goldens_schema",
            REPO_ROOT / "scripts" / "capture_keeper_goldens.py",
        )
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

        # A hypothetical sibling role: write_manifest is key-agnostic (the
        # retirement of ERCOT__carveout-2023 is enforced at resolution and by
        # the gate, not here), and the property under test is additivity.
        carve = _entry(keeper_id="2026-08-25-236-swcap-clip-k33", iso="ERCOT")
        carve["partition"] = {
            "iso": "ERCOT",
            "role": "carveout-x",
            "designated_years": [2023],
        }
        p = self.mod.write_manifest("t", {"ERCOT__carveout-x": carve})

        man = json.loads(p.read_text())
        self.assertEqual(man["keepers"]["ERCOT"], before)
        self.assertEqual(man["keepers"]["ERCOT"], forward)
        self.assertEqual(
            man["keepers"]["ERCOT__carveout-x"]["keeper_id"],
            "2026-08-25-236-swcap-clip-k33",
        )
        self.assertEqual(sorted(man["keepers"]), ["ERCOT", "ERCOT__carveout-x"])

    def test_basis_sha_helper_is_origin_durable(self):
        """basis_sha must resolve in main even when git_sha is a branch commit."""
        basis = self.mod._basis_sha()
        self.assertNotEqual(basis, "unknown")
        self.assertEqual(len(basis), 40, "basis_sha must be a full sha")


if __name__ == "__main__":
    unittest.main()
