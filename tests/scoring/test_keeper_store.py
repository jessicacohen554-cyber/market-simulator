"""Tests for scripts/lib/keeper_store.py — the sharded per-ISO keeper store.

Covers the three read paths (shards, legacy monolith fallback, empty repo)
and the promotion write path (``write_keeper`` touches ONLY its ISO's shard —
the conflict-free-lanes property the 2026-07-19 sharding exists to provide).
Trivial fixtures first, per the repo testing pattern.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.lib import keeper_store


def _mk_shards(root: Path, keepers: dict[str, str], frontier: dict | None = None):
    d = root / "frontend" / "data" / "backcast" / "keepers"
    d.mkdir(parents=True)
    d.joinpath("index.json").write_text(json.dumps({"isos": list(keepers)}))
    for iso, rid in keepers.items():
        rec: dict = {"iso": iso, "keeper": rid}
        if frontier and iso in frontier:
            rec["frontier"] = frontier[iso]
        d.joinpath(f"{iso}.json").write_text(json.dumps(rec))
    return d


class ShardReadTests(unittest.TestCase):
    def test_single_shard(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _mk_shards(root, {"ERCOT": "2026-01-01-run1"})
            self.assertEqual(keeper_store.iso_list(root), ["ERCOT"])
            self.assertEqual(
                keeper_store.keeper_ids(root), {"ERCOT": "2026-01-01-run1"}
            )
            self.assertEqual(keeper_store.keeper_list(root), ["2026-01-01-run1"])

    def test_merged_matches_legacy_shape(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _mk_shards(
                root,
                {"ERCOT": "2026-01-01-a", "PJM": "2026-01-02-b"},
                frontier={"PJM": {"declared": "2026-01-03", "note": "n"}},
            )
            merged = keeper_store.load_merged(root)
            self.assertEqual(merged["ERCOT"], "2026-01-01-a")
            self.assertEqual(merged["PJM"], "2026-01-02-b")
            self.assertEqual(merged["keepers"], ["2026-01-01-a", "2026-01-02-b"])
            self.assertEqual(merged["frontier"]["PJM"]["declared"], "2026-01-03")

    def test_index_order_wins(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            d = _mk_shards(root, {"PJM": "b", "ERCOT": "a"})
            d.joinpath("index.json").write_text(json.dumps({"isos": ["PJM", "ERCOT"]}))
            self.assertEqual(keeper_store.iso_list(root), ["PJM", "ERCOT"])
            self.assertEqual(keeper_store.keeper_list(root), ["b", "a"])


class LegacyFallbackTests(unittest.TestCase):
    def test_monolith_with_iso_keys(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            data = root / "frontend" / "data" / "backcast"
            data.mkdir(parents=True)
            data.joinpath("keepers.json").write_text(
                json.dumps(
                    {
                        "ERCOT": "2026-01-01-a",
                        "keepers": ["2026-01-01-a"],
                        "frontier": {"ERCOT": {"note": "f"}},
                        "note": "legacy",
                    }
                )
            )
            self.assertEqual(keeper_store.keeper_ids(root), {"ERCOT": "2026-01-01-a"})
            self.assertEqual(
                keeper_store.load_shard("ERCOT", root)["frontier"]["note"], "f"
            )

    def test_monolith_keepers_list_only(self):
        # A fixture-style monolith carrying ONLY the keepers array (no per-ISO
        # keys) must still resolve through keeper_list (the D-2/D-9 CI path).
        with TemporaryDirectory() as td:
            root = Path(td)
            data = root / "frontend" / "data" / "backcast"
            data.mkdir(parents=True)
            data.joinpath("keepers.json").write_text(
                json.dumps({"keepers": ["2026-01-01-x"]})
            )
            self.assertEqual(keeper_store.keeper_list(root), ["2026-01-01-x"])
            self.assertEqual(
                keeper_store.load_merged(root)["keepers"], ["2026-01-01-x"]
            )

    def test_empty_repo(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            self.assertEqual(keeper_store.iso_list(root), [])
            self.assertEqual(keeper_store.keeper_list(root), [])
            self.assertEqual(keeper_store.load_merged(root)["keepers"], [])


class WriteKeeperTests(unittest.TestCase):
    def test_write_touches_only_its_lane_and_preserves_fields(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            d = _mk_shards(
                root,
                {"ERCOT": "old-e", "PJM": "old-p"},
                frontier={"ERCOT": {"note": "keepme"}},
            )
            before_pjm = d.joinpath("PJM.json").read_bytes()
            path = keeper_store.write_keeper("ERCOT", "2026-02-02-new", repo_root=root)
            self.assertEqual(path, d / "ERCOT.json")
            rec = json.loads(path.read_text())
            self.assertEqual(rec["keeper"], "2026-02-02-new")
            self.assertEqual(rec["frontier"]["note"], "keepme")  # preserved
            self.assertEqual(
                d.joinpath("PJM.json").read_bytes(), before_pjm
            )  # other lane untouched


if __name__ == "__main__":
    unittest.main()
