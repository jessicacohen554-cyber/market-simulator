"""Tests for the DECLARED-default drop rule (capx D24-R, option (b′-1)).

**The defect.** ``ScenarioConfig.cache_key()`` used to drop a
``_CACHE_KEY_OPTIONAL_FIELDS`` member when it equalled ``getattr(ScenarioConfig(),
name)`` — the LIVE default, recomputed on every call. Flip that default and a
post-flip config at the NEW default hashes exactly as the pre-flip config at the
OLD default did: one key, two postures, and the post-flip run silently reads the
pre-flip bundle. ``docs/handoffs/FINDING-capx-d24-cache-key-defect-2026-09-01.md``
measured it twice among the committed runs (§4.1 ERCOT, §4.2 NEISO).

**The repair (owner ruling Q20).** The drop compares against the FROZEN
declaration in ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS``, which a flip no longer
edits — it appends to ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`` instead. These
tests pin three things:

* the repair works — the same simulated flip that collides under the live-default
  rule separates under the declared-default rule (``FlipNoLongerCollidesTest``);
* it cost nothing to land — every frozen declaration equalled its live default
  at the re-baseline, which is why it moved 0 of 170 committed keys
  (``RebaselineIsANoOpTest``). Since capx D44 (owner ruling Q30) the ledger
  carries its first declared flip, so that equality now holds for every
  registered field EXCEPT a flipped one, whose live default deliberately
  differs — the no-op property is therefore asserted as of the pre-flip day;
* the ledger stays append-only — an EDIT to an existing entry fails loudly
  (``AppendOnlyLedgerTest``), which is what keeps the frozen values frozen.
"""

from __future__ import annotations

import contextlib
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.config import scenarios  # noqa: E402
from market_sim.config.scenarios import (  # noqa: E402
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS,
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    _CACHE_KEY_REGISTRATION_TIME_DEFAULTS,
    _CACHE_KEY_UNRESOLVED_DECLARED_DEFAULTS,
    ScenarioConfig,
    cache_key_drop_defaults,
    registration_time_default,
)
from scripts import check_cache_key_registration as G  # noqa: E402


@contextlib.contextmanager
def _drop_rule(mapping: dict):
    """Run the block with ``cache_key`` dropping fields at *mapping*.

    Models one process state: ``mapping`` is what that process believes each
    registered field's droppable value to be. The pre-repair algorithm is the
    LIVE defaults of the day; the repaired one is the frozen declarations.
    """
    prior = scenarios._CACHE_KEY_DROP_DEFAULTS
    scenarios._CACHE_KEY_DROP_DEFAULTS = mapping
    try:
        yield
    finally:
        scenarios._CACHE_KEY_DROP_DEFAULTS = prior


def _live_defaults() -> dict:
    """Every registered field at the live default — the pre-repair drop rule."""
    live = ScenarioConfig()
    return {name: getattr(live, name) for name in _CACHE_KEY_OPTIONAL_FIELDS}


class FlipNoLongerCollidesTest(unittest.TestCase):
    """The demonstrated collision, reproduced and then repaired.

    Simulated on ``retirement_rule`` because it is a real flip from the record
    (owner decision D-1, ``'legacy'`` -> ``'pipeline'``, 2026-08-03) and its
    values are distinguishable in a message. Nothing here mutates the real
    ledger — only the resolved drop mapping the algorithm reads.
    """

    def setUp(self):
        self.field = "retirement_rule"
        self.old_value = "legacy"
        self.new_value = ScenarioConfig().retirement_rule
        self.assertEqual(self.new_value, "pipeline")
        # The process BEFORE the flip: the live default was the old value, so a
        # run carrying it dropped the field and its bundle is keyed without it.
        self.before = {**_live_defaults(), self.field: self.old_value}
        # The process AFTER the flip, pre-repair: the drop follows the live
        # default wherever it goes.
        self.after_live_rule = _live_defaults()
        # The process AFTER the flip, repaired: the drop stays at the frozen
        # declaration, which the flip did not touch.
        self.after_declared_rule = self.before

    def _key(self, mapping, **overrides):
        with _drop_rule(mapping):
            return ScenarioConfig(**overrides).cache_key()

    def test_the_live_default_rule_collides_across_a_flip(self):
        # THE DEFECT. The pre-flip run at 'legacy' and the post-flip run at the
        # new 'pipeline' default hash IDENTICALLY: both dropped the field, each
        # because it was the default on its own day.
        pre_flip = self._key(self.before, retirement_rule=self.old_value)
        post_flip = self._key(self.after_live_rule)
        self.assertEqual(pre_flip, post_flip)

    def test_the_declared_default_rule_separates_them(self):
        # THE REPAIR. The frozen declaration stays at 'legacy', so the post-flip
        # config's 'pipeline' is non-default for hashing and enters the key.
        pre_flip = self._key(self.before, retirement_rule=self.old_value)
        post_flip = self._key(self.after_declared_rule)
        self.assertNotEqual(pre_flip, post_flip)

    def test_an_explicit_old_value_still_shares_the_pre_flip_key(self):
        # The useful half of the registration is untouched: a control arm pinned
        # to the superseded posture is still dropped, so it still addresses the
        # pre-flip bundle. Same posture, same bundle — which is correct.
        self.assertEqual(
            self._key(self.before, retirement_rule=self.old_value),
            self._key(self.after_declared_rule, retirement_rule=self.old_value),
        )


class RebaselineIsANoOpTest(unittest.TestCase):
    """(b′-1), not (b′-2): the re-baseline is at TODAY's declarations."""

    def test_every_registered_field_has_an_evaluable_declaration(self):
        drop_at = cache_key_drop_defaults()
        self.assertEqual(set(drop_at), set(_CACHE_KEY_OPTIONAL_FIELDS))
        self.assertEqual(_CACHE_KEY_UNRESOLVED_DECLARED_DEFAULTS, set())

    def test_declared_defaults_equal_the_live_defaults_where_no_flip_is_declared(self):
        # This equality is WHY the change moved 0 of 170 committed keys
        # (scripts/probes/capxd24r_cache_key_no_op_check.py). It holds for every
        # field with no appended flip; a field WITH one is expected to differ —
        # that difference is the repair doing its job.
        flipped = {name for _, name, _ in _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS}
        live = ScenarioConfig()
        for name, value in cache_key_drop_defaults().items():
            if name in flipped:
                continue
            self.assertEqual(getattr(live, name), value, msg=name)

    def test_the_default_keys_are_unmoved_by_the_repair(self):
        # The pinned-identity surface: hashing under the live-default rule (the
        # pre-repair algorithm) and under the shipped rule gives the same key
        # for the same config — i.e. the re-baseline itself moved nothing, which
        # is what makes (b′-1) free.
        #
        # AMENDED by capx D44 (the first declared flip, owner ruling Q30 arming
        # `fossil_announced_exits_enabled`). A field WITH a declared flip is
        # expected to hash differently under the two rules — that difference IS
        # the repair working, and asserting it away would re-introduce exactly
        # the collision (b′-1) was landed to stop. So the comparison is made as
        # of the PRE-FLIP day on both sides: the pre-repair rule is the live
        # defaults with each flipped field put back to its frozen declaration
        # (which is what "the live default" meant before the flip), and the
        # config hashed is the pre-flip bare config (same substitution). On
        # that pair the two rules must still agree — for every registered
        # field, flipped or not. Nothing here is weakened for the 229 unflipped
        # fields: their live default IS their declaration, so the substitution
        # is a no-op for them.
        frozen = {
            name: scenarios._resolve_declared_default(
                _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[name]
            )
            for _, name, _ in _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS
        }
        pre_flip_rule = {**_live_defaults(), **frozen}
        for kwargs in ({}, {"mode": "backcast"}):
            with _drop_rule(pre_flip_rule):
                before = ScenarioConfig(**kwargs, **frozen).cache_key()
            self.assertEqual(
                before,
                ScenarioConfig(**kwargs, **frozen).cache_key(),
                msg=kwargs,
            )


class RegistrationTimeDefaultTest(unittest.TestCase):
    """The absent-equivalent value the (c′) bundle check compares against."""

    def test_a_flipped_field_reports_its_ORIGINAL_default(self):
        # capx D24 §4.2's collision form turns on exactly this: the stored config
        # predates the field, and the requester carries the ARMED default. Both
        # R-A fields are declared at True today, so only the registration-time
        # record can say the absent state was False.
        self.assertFalse(registration_time_default("storage_entry_availability_gate"))
        self.assertFalse(
            registration_time_default("storage_entry_cost_normalized_rank")
        )
        self.assertEqual(registration_time_default("retirement_rule"), "legacy")

    def test_an_unflipped_registered_field_reports_its_declaration(self):
        self.assertEqual(
            registration_time_default("hindcast"), cache_key_drop_defaults()["hindcast"]
        )

    def test_an_unregistered_field_reports_its_dataclass_default(self):
        self.assertEqual(registration_time_default("iso"), ScenarioConfig().iso)

    def test_an_unknown_name_raises(self):
        with self.assertRaises(KeyError):
            registration_time_default("not_a_field_at_all")

    def test_the_registration_time_table_names_only_registered_fields(self):
        self.assertFalse(
            set(_CACHE_KEY_REGISTRATION_TIME_DEFAULTS) - set(_CACHE_KEY_OPTIONAL_FIELDS)
        )

    def test_it_does_not_key_anything(self):
        # The table is read by the bundle check alone. If it ever reached the
        # hash the change would be option (b′-2) — 98/99 forecast and 63/63
        # backcast keys — which ruling Q20 did not license.
        for name, src in _CACHE_KEY_REGISTRATION_TIME_DEFAULTS.items():
            original = scenarios._resolve_declared_default(src)
            if original != cache_key_drop_defaults()[name]:
                break
        else:  # pragma: no cover - the table would be empty or fully unmoved
            self.skipTest("no field's default has moved since registration")
        self.assertNotEqual(
            cache_key_drop_defaults()[name],
            original,
            msg=f"{name} is the moved field this test relies on",
        )
        self.assertEqual(
            cache_key_drop_defaults()[name],
            getattr(ScenarioConfig(), name),
            msg="the key still drops at the DECLARED default, never the original",
        )


def _synthetic(live: str, declared: str, flips: str = "") -> str:
    """A minimal config module carrying a registry, a ledger and a flips tuple."""
    return (
        "from dataclasses import dataclass, field\n\n"
        '_CACHE_KEY_OPTIONAL_FIELDS = (\n    "knob",\n)\n\n'
        "_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS: dict[str, str] = {\n"
        f"    'knob': {declared!r},\n"
        "}\n\n"
        "_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS: tuple[tuple[str, str, str], ...] = (\n"
        f"{flips}"
        ")\n\n"
        "_CACHE_KEY_RETIRED_FIELDS: dict[str, object] = {}\n\n\n"
        "@dataclass\nclass ScenarioConfig:\n"
        '    iso: str = "ERCOT"\n'
        f"    knob: str = {live}\n"
    )


class AppendOnlyLedgerTest(unittest.TestCase):
    """An EDIT to a frozen declaration fails; an append does not."""

    def test_editing_an_entry_is_a_breach(self):
        breaches = G.append_only_violations(
            {"knob": "'a'"}, {"knob": "'b'"}, {"knob"}, set()
        )
        self.assertEqual(len(breaches), 1)
        self.assertIn("EDITED", breaches[0])

    def test_adding_an_entry_for_a_new_field_is_not(self):
        self.assertEqual(
            G.append_only_violations(
                {"knob": "'a'"},
                {"knob": "'a'", "dial": "False"},
                {"knob", "dial"},
                set(),
            ),
            [],
        )

    def test_removing_an_entry_whose_field_still_exists_is_a_breach(self):
        breaches = G.append_only_violations({"knob": "'a'"}, {}, {"knob"}, set())
        self.assertEqual(len(breaches), 1)
        self.assertIn("REMOVED", breaches[0])

    def test_removing_an_entry_with_its_deleted_field_is_not(self):
        # Rule 26 [R-DELETE]: the field is gone and its value is parked in
        # _CACHE_KEY_RETIRED_FIELDS, which keeps every historical key stable.
        self.assertEqual(
            G.append_only_violations({"knob": "'a'"}, {}, set(), {"knob"}), []
        )

    def test_head_is_an_append_only_descendant_of_the_declared_ledger(self):
        # The real ledger against itself: a no-op comparison, but it pins the
        # parse of the live file (218 entries) through the same function CI runs.
        head = (_ROOT / "src/market_sim/config/scenarios.py").read_text()
        fields, registry, declared = G._fields_and_registry(head)
        self.assertEqual(declared.keys(), set(_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS))
        self.assertEqual(
            G.append_only_violations(declared, declared, set(fields), G._retired(head)),
            [],
        )
        self.assertEqual(set(registry), set(_CACHE_KEY_OPTIONAL_FIELDS))


class FlipDeclarationTest(unittest.TestCase):
    """Check 3 reads the appended flip, so a declared flip is clean."""

    def test_an_undeclared_flip_still_fails_check_3(self):
        source = _synthetic("'b'", "'a'")
        fields, _, declared = G._fields_and_registry(source)
        current = dict(declared)
        for name, new_default in G._declared_flips(source):
            current[name] = new_default
        self.assertNotEqual(G._norm(fields["knob"]), current["knob"])

    def test_an_appended_flip_declares_it_without_editing_the_frozen_entry(self):
        source = _synthetic(
            "'b'", "'a'", flips="    ('2026-09-02', 'knob', \"'b'\"),\n"
        )
        fields, _, declared = G._fields_and_registry(source)
        # The frozen entry — what cache_key drops at — is untouched.
        self.assertEqual(declared["knob"], "'a'")
        flips = G._declared_flips(source)
        self.assertEqual(flips, [("knob", "'b'")])
        current = {**declared, **dict(flips)}
        self.assertEqual(G._norm(fields["knob"]), current["knob"])

    def test_the_shipped_guard_passes_at_head(self):
        self.assertEqual(G.main([]), 0)


if __name__ == "__main__":
    unittest.main()
