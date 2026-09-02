"""Tests for the cached-bundle config check (capx D24-R, option (c′)).

**The hazard.** ``cache_key`` drops every registered field sitting at its
default, so a run's key omits 115–215 of them
(``docs/handoffs/FINDING-capx-d24-cache-key-defect-2026-09-01.md`` §3) and a
bundle on disk at a key is NOT proof it was solved under the config asking for
it. D24 demonstrated two committed pairs at one key with different postures, in
two distinct forms — §4.1 a differing COMMON field, §4.2 a field ABSENT from one
side and armed on the other.

**The repair (owner ruling Q20, option (c′)).** Before a bundle is served, the
``config.yaml`` stored beside it must agree with the requesting config: on every
common field, and on every requester-only field whose value has moved off the
one its absence is equivalent to. Refusal is a logged cache miss, never an
exception.

The last class here is the one that decides (c′) is the right shape rather than
strict (c): it replays the committed shared-key groups (FOURTEEN at D24,
fifteen since T3-GOLDEN-2 landed a designed pair on 2026-09-01) and asserts the
rule refuses the two true positives and permits every designed case —
strict equality refuses 14 of 14 (D24 §7).
"""

from __future__ import annotations

import collections
import json
import subprocess
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

import yaml

from market_sim.config.scenarios import ScenarioConfig
from market_sim.results import cache

_ROOT = Path(__file__).resolve().parents[3]


class StoredConfigAgreementTest(unittest.TestCase):
    """``cache_config_disagreements`` at the seam, against a written bundle."""

    ISO, KEY, YEAR = "ERCOT", "0123456789abcdef", 2030

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._ctx = cache.cache_root(self._tmp.name)
        self._ctx.__enter__()
        self.addCleanup(self._ctx.__exit__, None, None, None)
        self.config = ScenarioConfig(iso=self.ISO)

    def _store(self, payload: dict) -> None:
        """Write *payload* as the bundle's ``config.yaml``."""
        path = cache.get_config_path(self.ISO, self.KEY, self.YEAR)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, sort_keys=True))

    def _check(self, config=None) -> list[str]:
        return cache.cache_config_disagreements(
            self.ISO, self.KEY, self.YEAR, config or self.config
        )

    def test_an_identical_stored_config_is_served(self):
        # Also pins that the yaml round-trip itself is not read as a difference:
        # asdict renders six fields as tuples that safe_dump/safe_load return as
        # lists, and six more carry checkout-absolute paths.
        self.config.to_yaml_full(self._make_dir() / "config.yaml")
        self.assertEqual(self._check(), [])

    def _make_dir(self) -> Path:
        path = cache.get_config_path(self.ISO, self.KEY, self.YEAR).parent
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_no_stored_config_is_not_a_disagreement(self):
        # A bundle with no config.yaml (hand-assembled, or truncated) cannot be
        # compared, so the pre-existing behaviour stands. Every bundle
        # save_result writes carries one.
        self._make_dir()
        self.assertEqual(self._check(), [])

    def test_a_differing_common_field_is_refused(self):
        # D24 §4.1 — the ERCOT d12c-armed / d4m form.
        stored = asdict(self.config)
        stored["storage_entry_availability_gate"] = not stored[
            "storage_entry_availability_gate"
        ]
        self._store(stored)
        self.assertEqual(self._check(), ["storage_entry_availability_gate"])

    def test_a_field_absent_from_the_store_and_ARMED_here_is_refused(self):
        # D24 §4.2 — the NEISO capxd14 / rcrepair form, and the nastier one: the
        # stored config predates both fields, this one carries them at a default
        # that has since been ARMED, and NEITHER value is in the key. Nothing in
        # the pair of files looks like more than schema growth.
        stored = asdict(self.config)
        del stored["storage_entry_availability_gate"]
        del stored["storage_entry_cost_normalized_rank"]
        self._store(stored)
        self.assertTrue(self.config.storage_entry_availability_gate)
        self.assertEqual(
            self._check(),
            ["storage_entry_availability_gate", "storage_entry_cost_normalized_rank"],
        )

    def test_a_field_absent_from_the_store_and_INERT_here_is_served(self):
        # The designed case, and what separates (c′) from strict (c): ordinary
        # schema growth. The stored run predates the field; this run carries it
        # at the value its absence is equivalent to, so the bundle is the same
        # dispatch.
        stored = asdict(self.config)
        del stored["hindcast"]
        self._store(stored)
        self.assertFalse(self.config.hindcast)
        self.assertEqual(self._check(), [])

    def test_a_field_absent_from_the_store_and_SET_here_is_refused(self):
        stored = asdict(self.config)
        del stored["hindcast"]
        self._store(stored)
        # The comparison is on the RESOLVED config, so it also sees what
        # ``__post_init__`` couples to the field (arming ``hindcast`` selects a
        # datacenter-load path). That is the posture the bundle would have to
        # match, so naming both is correct.
        self.assertIn(
            "hindcast", self._check(ScenarioConfig(iso=self.ISO, hindcast=True))
        )

    def test_a_field_only_the_STORED_config_has_is_ignored(self):
        # A knob deleted under rule 26 [R-DELETE]. _CACHE_KEY_RETIRED_FIELDS
        # already re-inserts its value into the key, so refusing here would
        # orphan every bundle written before the deletion for no protection.
        stored = asdict(self.config)
        stored["a_knob_this_codebase_deleted"] = True
        self._store(stored)
        self.assertEqual(self._check(), [])

    def test_several_differences_are_all_named(self):
        stored = asdict(self.config)
        stored["retirement_rule"] = "legacy"
        stored["entry_rate_limits"] = not stored["entry_rate_limits"]
        self._store(stored)
        self.assertEqual(self._check(), ["entry_rate_limits", "retirement_rule"])


class CommittedSharedKeyGroupsTest(unittest.TestCase):
    """Replay D24 §4.5: refuse the 2 true positives, permit the designed cases.

    Every committed ``run_config.json`` carrying a ``cache_key`` is grouped by
    that key; each group is a set of runs that addressed ONE bundle directory.
    The comparison runs oldest-as-stored, which is the direction a cache hit
    takes, and restricts the requesting side to fields this codebase still has —
    a run today cannot ask for a field that no longer exists, and three of the
    groups span a knob that was added and later deleted between their solves.
    """

    @classmethod
    def setUpClass(cls):
        paths = subprocess.run(
            ["git", "ls-files", "*run_config.json"],
            cwd=_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        keyed = []
        for rel in paths:
            record = json.loads((_ROOT / rel).read_text())
            payload = record.get("scenario_config")
            if record.get("cache_key") and isinstance(payload, dict):
                keyed.append(
                    (record["cache_key"], record.get("timestamp", ""), rel, payload)
                )
        if len(keyed) < 90:
            raise unittest.SkipTest(
                f"only {len(keyed)} keyed run_config.json present "
                "(a sparse checkout without results/) — nothing to replay"
            )
        grouped = collections.defaultdict(list)
        for row in keyed:
            grouped[row[0]].append(row)
        cls.groups = {
            k: sorted(v, key=lambda r: r[1]) for k, v in grouped.items() if len(v) > 1
        }
        cls.live = set(ScenarioConfig().__dataclass_fields__)

    def _refusals(self, members) -> dict[tuple[str, str], list[str]]:
        out = {}
        for i, (_, _, stored_rel, stored) in enumerate(members):
            for _, _, wanted_rel, wanted in members[i + 1 :]:
                differing = cache.config_disagreements(
                    stored, {k: v for k, v in wanted.items() if k in self.live}
                )
                if differing:
                    out[(stored_rel, wanted_rel)] = differing
        return out

    def test_fourteen_groups_split_two_and_twelve(self):
        refused = {k: self._refusals(v) for k, v in self.groups.items()}
        refused_keys = sorted(k for k, v in refused.items() if v)
        # 14 -> 15 on 2026-09-01: T3-GOLDEN-2 (`a5523fac`, `bba296ca`)
        # overwrote results/ff-t3-neiso-golden/bau/run_config.json with the
        # armed-posture golden, which now shares key 706e7ba8e6582d42 with its
        # own fc6/arms/base control — a designed (permitted) case, so the
        # refused pair below is unchanged. The count is a frozen inventory of
        # committed run_config.json files and moves whenever a registration
        # lands two configs at one key; the invariant this test guards is the
        # refused SET, asserted next. Corrected 2026-09-02 by the fast-tier
        # repair lane (the count had been red on main since 2026-09-01).
        # 15 -> 16 on 2026-09-02: capx D42 registered the verified fossil-dates
        # arm twice at key 85000b5179ddff0f — the plant-wide-derate solve
        # (`-d42-dates-plantwide`, kept as the measurement of the composition
        # artifact) and the fuel-scoped re-solve (`-d42-dates`); the derate
        # scope is code, not config, so the two run_config.json files are
        # identical by construction — a designed (permitted) case. Refused set
        # unchanged.
        #
        # DE-BRITTLED 2026-09-02 (caiso-239): the equality was a CORPUS CENSUS,
        # not an invariant — it goes red on any registration that lands a
        # config at a new key OR a second config at an existing one, which is
        # what every calibration session does, and it had already been repaired
        # in place three times in two days (14 -> 15 -> 16). The invariant this
        # test guards is the REFUSED SET, asserted immediately below and left
        # EXACT; the census is kept only as a floor, so a collapse of the
        # grouping (the failure mode worth catching) still fails while a
        # routine registration does not.
        self.assertGreaterEqual(len(self.groups), 14)
        self.assertIn("706e7ba8e6582d42", self.groups)
        self.assertEqual(
            refused_keys, ["07e416f3f8072e7c", "f061b2646bfaac8b"], msg=refused
        )

    def test_both_true_positives_are_refused_on_the_R_A_pair(self):
        for key in ("07e416f3f8072e7c", "f061b2646bfaac8b"):
            refusals = self._refusals(self.groups[key])
            self.assertEqual(len(refusals), 1, msg=key)
            self.assertEqual(
                next(iter(refusals.values())),
                [
                    "storage_entry_availability_gate",
                    "storage_entry_cost_normalized_rank",
                ],
                msg=key,
            )


if __name__ == "__main__":
    unittest.main()
