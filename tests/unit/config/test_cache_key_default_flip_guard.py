"""Tests for the declared-default cache-key guard (FFR-3A blocker 4).

**The hazard.** ``ScenarioConfig.cache_key()`` drops a
``_CACHE_KEY_OPTIONAL_FIELDS`` member when it equals ``getattr(ScenarioConfig(),
name)`` — the LIVE default, recomputed on every call. Move that default and a
NEW-default run hashes IDENTICALLY to the OLD-default run it supersedes: a
silent same-key collision, so a flipped config re-uses the pre-flip bundle.
FFR-3A measured this happening on the D-1/D-2 flips (the default key stayed
``603c2498bf71d21d`` across a behavioral change, against a signed packet that
asserted the opposite) and closed with "it will silently recur on the next
default flip; structural, needs a decision not a patch."

These tests pin BOTH halves so neither can regress:

* the mechanism itself — a default flip really does collide, and an explicit
  old value really does stay separable (asserted on the live config, not
  described in prose);
* the guard that makes it non-silent — ``check_cache_key_registration`` check 3
  passes at HEAD, FAILS on an undeclared flip, and passes once declared.

The guard is exercised against synthetic source text (it is pure ``ast``, no
import), so these tests never mutate the real config module.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.config.scenarios import (  # noqa: E402
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS,
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from scripts import check_cache_key_registration as G  # noqa: E402


def _synthetic(live: str, declared: str) -> str:
    """A minimal config module: field default ``live``, ledger entry ``declared``.

    Both arguments are DEFAULT EXPRESSIONS in source form (``"'a'"`` is the
    string literal ``a``), matching how the real ledger stores them.
    """
    return (
        "from dataclasses import dataclass, field\n\n"
        '_CACHE_KEY_OPTIONAL_FIELDS = (\n    "knob",\n)\n\n'
        "_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS: dict[str, str] = {\n"
        f"    'knob': {declared!r},\n"
        "}\n\n\n"
        "@dataclass\nclass ScenarioConfig:\n"
        '    iso: str = "ERCOT"\n'
        f"    knob: str = {live}\n"
    )


class DeclaredLedgerCoversTheRegistryTest(unittest.TestCase):
    """Registry and ledger cover each other, and the ledger matches HEAD."""

    def test_ledger_and_registry_cover_each_other(self):
        self.assertEqual(
            set(_CACHE_KEY_OPTIONAL_FIELDS), set(_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS)
        )

    def test_guard_passes_at_head_without_a_base(self):
        # Check 3 is a HEAD-only invariant: it must fire with no --base, so it
        # runs on every CI run rather than only on the PR that adds a field.
        self.assertEqual(G.main([]), 0)

    def test_declared_defaults_parse_and_match_the_live_config(self):
        # The ledger stores SOURCE TEXT; for the plain-literal entries (the vast
        # majority) that text must evaluate to the live default value, so the
        # declaration cannot drift into being merely well-formed.
        #
        # A field with a DECLARED FLIP is the one exception, and by design: the
        # frozen entry stays at the pre-flip value (that is what the cache key
        # drops at, capx D24-R (b′-1)) while the live default moves, and the
        # flips ledger carries the new one. Compare against the newest declared
        # flip where there is one — the guard's own check 3 resolves it exactly
        # this way, so a silent drift is still caught for every field.
        current = dict(_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS)
        for _date, name, new_src in _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS:
            current[name] = new_src
        live = ScenarioConfig()
        checked = 0
        for name, src in current.items():
            try:
                want = eval(src, {"__builtins__": {}}, {})  # noqa: S307 — literals
            except Exception:  # noqa: BLE001 — field(default_factory=...) etc.
                continue
            self.assertEqual(getattr(live, name), want, msg=name)
            checked += 1
        self.assertGreater(checked, 100, "expected most entries to be plain literals")

    def test_a_declared_flip_leaves_its_frozen_entry_alone(self):
        # The other half of the same invariant: the flip is declared by an
        # APPEND, never by editing the frozen entry. A flipped field's frozen
        # declaration must therefore still differ from its live default — if
        # someone "syncs" the entry, the cache key silently re-bases and the
        # post-flip config collides with its pre-flip bundle again.
        live = ScenarioConfig()
        for _date, name, _new_src in _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS:
            frozen = eval(  # noqa: S307 — ledger literals
                _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[name], {"__builtins__": {}}, {}
            )
            self.assertNotEqual(getattr(live, name), frozen, msg=name)


class TheHazardItselfTest(unittest.TestCase):
    """The collision is real — asserted on the live config, not described."""

    def test_a_registered_field_at_its_default_is_dropped_from_the_hash(self):
        # This is what makes a default flip collide: whatever the default IS,
        # a config carrying it hashes the same as one that omits the field.
        self.assertEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(
                net_cone_forward_escalation=ScenarioConfig().net_cone_forward_escalation
            ).cache_key(),
        )

    def test_an_explicit_non_default_value_stays_separable(self):
        # The useful half: a control arm pinned to the superseded value hashes
        # distinctly, so it never collides with the flipped default.
        others = {"hold_last", "reindex_net", "reindex_gross"} - {
            ScenarioConfig().net_cone_forward_escalation
        }
        for value in sorted(others):
            self.assertNotEqual(
                ScenarioConfig().cache_key(),
                ScenarioConfig(net_cone_forward_escalation=value).cache_key(),
                msg=value,
            )


class GuardBehaviourTest(unittest.TestCase):
    """Check 3 detects a moved default, and only a moved one."""

    def _parse(self, live: str, declared: str):
        return G._fields_and_registry(_synthetic(live, declared))

    def test_matching_default_is_clean(self):
        fields, registry, declared = self._parse("'a'", "'a'")
        self.assertEqual(registry, {"knob"})
        self.assertEqual(declared, {"knob": "'a'"})
        self.assertEqual(G._norm(fields["knob"]), declared["knob"])

    def test_moved_default_is_detected(self):
        fields, _, declared = self._parse("'b'", "'a'")
        self.assertNotEqual(G._norm(fields["knob"]), declared["knob"])

    def test_formatting_churn_is_not_a_move(self):
        # Quote style / spacing must not read as a flip, or the guard would cry
        # wolf on every reformat and get muted.
        self.assertEqual(G._norm('"a"'), G._norm("'a'"))
        self.assertEqual(
            G._norm("field(default_factory=lambda: [1, 2])"),
            G._norm("field(\n    default_factory=lambda: [1, 2]\n)"),
        )

    def test_unregistered_declaration_and_undeclared_registration_are_visible(self):
        _, registry, declared = self._parse("'a'", "'a'")
        self.assertFalse(registry - set(declared))
        self.assertFalse(set(declared) - registry)


if __name__ == "__main__":
    unittest.main()
