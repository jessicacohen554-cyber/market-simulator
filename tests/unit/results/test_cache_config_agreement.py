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

The last two classes are the ones that decide (c′) is the right shape rather
than strict (c): they replay real shared-key groups and assert the rule refuses
the two true positives and permits the designed cases — strict equality refuses
14 of 14 (D24 §7).

**Where those groups come from, and why that moved.** D24 measured them live,
off ``git ls-files '*run_config.json'``. Rule 15 [R-DASHBOARD] as amended
2026-09-05 (keeper-only retention) then deleted the corpus: PR #4808 pruned 193
tracked configs to 72 and 20 shared-key groups to 7, taking one true positive's
partner with it. A census over ``results/`` is a **retention hazard** — the rule
requires that corpus to shrink, so an invariant read out of it survives only by
accident. The invariant therefore lives in
:class:`FixtureSharedKeyGroupsTest`, over a committed fixture
(``tests/fixtures/cache_shared_key_groups/``, recovered verbatim from the tree
before the prune), and :class:`CommittedSharedKeyGroupsTest` keeps the live
replay as a second, skip-when-sparse, prune-monotone pass. Cause, census and
the sweep for other tests of this shape:
``docs/handoffs/FINDING-y23-cache-agreement-fixture-2026-09-06.md``.
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


def _refusals(members, live) -> dict[tuple[str, str], list[str]]:
    """Return every refusing ``(stored, wanted)`` pair in one shared-key group.

    Runs oldest-as-stored, which is the direction a cache hit takes, and
    restricts the requesting side to fields this codebase still has — a run
    today cannot ask for a field that no longer exists, and some groups span a
    knob that was added and later deleted between their solves.

    Args:
        members: ``(timestamp, label, scenario_config)`` rows, oldest first.
        live: The field names ``ScenarioConfig`` currently declares.

    Returns:
        ``{(stored label, wanted label): differing field names}``, refusals only.
    """
    out: dict[tuple[str, str], list[str]] = {}
    for i, (_, stored_label, stored) in enumerate(members):
        for _, wanted_label, wanted in members[i + 1 :]:
            differing = cache.config_disagreements(
                stored, {k: v for k, v in wanted.items() if k in live}
            )
            if differing:
                out[(stored_label, wanted_label)] = differing
    return out


# The two true positives D24 §4.5 found among the committed configs, and the one
# pair of fields each refuses on. Both are pinned by the fixture below; the live
# corpus is checked against them only where retention still carries the group.
_TRUE_POSITIVES = ("07e416f3f8072e7c", "f061b2646bfaac8b")
_REFUSED_ON = ["storage_entry_availability_gate", "storage_entry_cost_normalized_rank"]
_FIXTURE = _ROOT / "tests/fixtures/cache_shared_key_groups"
# The designed case: 15 fields the stored config predates, every one at the value
# its absence is equivalent to. Strict (c) refuses it; (c′) serves it.
_DESIGNED = "5925e67c572a910f"


def _fixture_groups() -> dict[str, list[tuple[str, str, dict]]]:
    """Load the committed shared-key fixture, oldest member first per group.

    Returns:
        ``{cache_key: [(timestamp, label, scenario_config), ...]}``.
    """
    groups: dict[str, list[tuple[str, str, dict]]] = {}
    for group_dir in sorted(p for p in _FIXTURE.iterdir() if p.is_dir()):
        members = []
        for path in sorted(group_dir.glob("*.json")):
            record = json.loads(path.read_text())
            members.append(
                (record["timestamp"], record["source_path"], record["scenario_config"])
            )
        groups[group_dir.name] = sorted(members, key=lambda row: row[0])
    return groups


class FixtureSharedKeyGroupsTest(unittest.TestCase):
    """Replay D24 §4.5 against the COMMITTED fixture, where retention cannot reach.

    Three real shared-key pairs, recovered verbatim from the tree immediately
    before rule 15's keeper-only prune deleted them
    (``tests/fixtures/cache_shared_key_groups/README.md`` cites every source
    blob). They carry the whole D24 discrimination in miniature: strict equality
    — option (c) — refuses all three, and (c′) refuses exactly the two true
    positives, on exactly the same pair of fields.

    This is the load-bearing pass. The live-corpus replay below is a second one,
    and cannot be load-bearing: rule 15 [R-DASHBOARD] requires the committed
    ``results/`` corpus to shrink, so any invariant read out of it survives only
    by accident (see
    ``docs/handoffs/FINDING-y23-cache-agreement-fixture-2026-09-06.md``).
    """

    @classmethod
    def setUpClass(cls):
        cls.groups = _fixture_groups()
        cls.live = set(ScenarioConfig().__dataclass_fields__)

    def test_the_fixture_carries_the_three_groups_as_pairs(self):
        # An exact assertion is safe HERE and only here: the fixture lives under
        # tests/, so nothing prunes it. A silently-emptied fixture would
        # otherwise let every assertion below pass vacuously.
        self.assertEqual(
            sorted(self.groups),
            sorted([*_TRUE_POSITIVES, _DESIGNED]),
            msg=str(_FIXTURE),
        )
        self.assertTrue(all(len(v) == 2 for v in self.groups.values()))

    def test_the_refused_set_is_exactly_the_two_true_positives(self):
        refused = {k: _refusals(v, self.live) for k, v in self.groups.items()}
        self.assertEqual(
            sorted(k for k, v in refused.items() if v),
            sorted(_TRUE_POSITIVES),
            msg=str(refused),
        )

    def test_both_true_positives_are_refused_on_the_R_A_pair(self):
        for key in _TRUE_POSITIVES:
            refusals = _refusals(self.groups[key], self.live)
            self.assertEqual(len(refusals), 1, msg=key)
            self.assertEqual(next(iter(refusals.values())), _REFUSED_ON, msg=key)

    def test_the_two_true_positives_are_the_two_D24_FORMS(self):
        # Not redundant with the refusal above: the same field list is reached by
        # two different branches of the rule, and D24 demonstrated BOTH. If one
        # form regressed to the other's code path the refusals would still match.
        forms = {}
        for key in _TRUE_POSITIVES:
            (_, _, stored), (_, _, wanted) = self.groups[key]
            forms[key] = {
                field: ("absent" if field not in stored else stored[field])
                for field in _REFUSED_ON
            }
            self.assertTrue(all(wanted[field] is True for field in _REFUSED_ON), key)
        # §4.2 — the stored config predates both fields, and this one carries
        # them at a default that has since been ARMED.
        self.assertEqual(
            forms["07e416f3f8072e7c"], dict.fromkeys(_REFUSED_ON, "absent")
        )
        # §4.1 — both configs carry both fields, at different values, and the key
        # dropped each at whichever value was the default when it was hashed.
        self.assertEqual(forms["f061b2646bfaac8b"], dict.fromkeys(_REFUSED_ON, False))

    def test_the_designed_group_is_permitted_where_strict_equality_refuses(self):
        # What decides (c′) over strict (c): 15 fields the stored config predates,
        # every one of them at the value its absence is equivalent to, so the
        # bundle is the same dispatch and refusing it would cost a re-solve for
        # no protection. Strict equality refuses the moment the schema grows at
        # all — 14 of D24's 14 groups, against 2 true positives.
        (_, _, stored), (_, _, wanted) = self.groups[_DESIGNED]
        wanted = {k: v for k, v in wanted.items() if k in self.live}
        absent = [f for f in wanted if f not in stored]
        self.assertEqual(len(absent), 15, msg=str(absent))
        self.assertEqual(
            [f for f in wanted if stored.get(f, wanted[f]) != wanted[f]], []
        )
        self.assertEqual(cache.config_disagreements(stored, wanted), [])


class CommittedSharedKeyGroupsTest(unittest.TestCase):
    """Second pass: replay the LIVE committed corpus, whatever retention left of it.

    Every ``run_config.json`` tracked by git and carrying a ``cache_key`` is
    grouped by that key; each group is a set of runs that addressed ONE bundle
    directory. This catches the hazard in the wild — a registration landing two
    materially different configs at one key — which the frozen fixture cannot.

    It is SKIP-when-sparse, and every assertion is **prune-monotone**: deleting
    committed runs only removes pairs, so a prune can never turn a pass into a
    failure. Two assertions were dropped for failing that test, both retention
    hazards rather than invariants — a ``>= 14`` census floor and an exact
    refused-key set, which together required a specific pair of bundles to stay
    on disk. Rule 15 [R-DASHBOARD] keeper-only retention deleted 118 tracked
    ``run_config.json`` in PR #4808 (193 -> 72 files, 20 -> 7 shared-key groups)
    and took one true positive's partner with them. The invariant they were
    reaching for now lives in the fixture above; the census is recorded in
    ``docs/handoffs/FINDING-y23-cache-agreement-fixture-2026-09-06.md``.
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
            # `git ls-files` lists the index, not the worktree: under a sparse
            # checkout a tracked file outside the cone is absent on disk (the
            # CI fast tier reddened on shard-artifacts/ this way, Y-30). A
            # missing member is exactly a prune, which every assertion here is
            # monotone under, so it is skipped rather than read.
            if not (_ROOT / rel).is_file():
                continue
            record = json.loads((_ROOT / rel).read_text())
            payload = record.get("scenario_config")
            if record.get("cache_key") and isinstance(payload, dict):
                keyed.append(
                    (record["cache_key"], record.get("timestamp", ""), rel, payload)
                )
        if not keyed:
            raise unittest.SkipTest(
                "no keyed run_config.json checked out (a sparse checkout without "
                "results/) — nothing to replay"
            )
        grouped = collections.defaultdict(list)
        for row in keyed:
            grouped[row[0]].append(row[1:])
        cls.groups = {
            k: sorted(v, key=lambda r: r[0]) for k, v in grouped.items() if len(v) > 1
        }
        if not cls.groups:
            raise unittest.SkipTest(
                f"{len(keyed)} keyed run_config.json, but retention leaves no key "
                "with two members — nothing to replay"
            )
        cls.live = set(ScenarioConfig().__dataclass_fields__)

    def test_no_committed_group_refuses_outside_the_known_true_positives(self):
        # The live half of the invariant, and the only one a prune cannot break:
        # a NEW refusing group is a real D24 hazard in the wild — two materially
        # different configs registered at one bundle key — and this is what
        # surfaces it. Pruning only ever removes candidates.
        refused = {
            k: r for k, v in self.groups.items() if (r := _refusals(v, self.live))
        }
        self.assertLessEqual(set(refused), set(_TRUE_POSITIVES), msg=str(refused))

    def test_a_surviving_true_positive_still_refuses_on_the_R_A_pair(self):
        # Guarded on presence, so it goes vacuous rather than red when retention
        # takes a member. The non-vacuous form is on the fixture above.
        for key in _TRUE_POSITIVES:
            if key not in self.groups:
                continue
            refusals = _refusals(self.groups[key], self.live)
            self.assertTrue(refusals, msg=key)
            for pair, differing in refusals.items():
                self.assertEqual(differing, _REFUSED_ON, msg=f"{key} {pair}")


if __name__ == "__main__":
    unittest.main()
