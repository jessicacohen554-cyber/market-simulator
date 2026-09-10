"""Tests for the touchpoint attestation's declared-degradation channel.

``scripts/gen_touchpoint_attestation.py`` exists so that a touchpoint's C6 PASS
is backed by a MACHINE CHECK rather than by prose: it refuses to write an
attestation whose recipe-identity assertion does not hold. The channel added by
miso-251 (2026-09-10) admits ONE narrow class of recipe delta — an overlay a
purged upstream source makes unrunnable on a held-out year — and these tests pin
the guards that keep it from becoming a tuning knob.

The case that forced it: MISO published no ASM reserve record before 2023, so
``miso_measured_reserve_requirements`` (and its hard dependent
``miso_reserve_online_gated``) cannot solve any MISO year before 2023. Without
the channel no such year could ever be attested and the holdout ladder would be
closed by construction rather than by evidence.
"""

import importlib.util
import unittest

from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "gen_touchpoint_attestation",
    str(REPO_ROOT / "scripts" / "gen_touchpoint_attestation.py"),
)
gta = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gta)

DEFAULTS = {"measured_overlay": False, "dependent_flag": False, "some_multiplier": 1.0}


class DeclaredDegradationTests(unittest.TestCase):
    def test_disarm_to_default_is_admitted(self):
        conflicts = {"measured_overlay": {"keeper": True, "touchpoint": False}}
        ok, left = gta.classify_declared(conflicts, ("measured_overlay",), DEFAULTS)
        self.assertEqual(left, {})
        self.assertEqual(ok["measured_overlay"]["scenario_default"], False)

    def test_a_declared_key_set_to_a_NON_default_is_still_a_conflict(self):
        """The guard that stops the channel becoming a tuning knob.

        A declaration may only DISARM an overlay onto the construction a
        forecast year uses. Anything else — arming a mechanism, re-cutting a
        multiplier — stays a hard error however loudly it is declared.
        """
        conflicts = {"some_multiplier": {"keeper": 1.0, "touchpoint": 1.25}}
        ok, left = gta.classify_declared(conflicts, ("some_multiplier",), DEFAULTS)
        self.assertEqual(ok, {})
        self.assertIn("some_multiplier", left)
        self.assertIn("may only DISARM", left["some_multiplier"]["refused"])

    def test_an_undeclared_conflict_is_untouched(self):
        conflicts = {"measured_overlay": {"keeper": True, "touchpoint": False}}
        ok, left = gta.classify_declared(conflicts, (), DEFAULTS)
        self.assertEqual(ok, {})
        self.assertEqual(left["measured_overlay"]["refused"], "not declared")

    def test_it_FAILS_CLOSED_when_defaults_are_unavailable(self):
        """An unverifiable declaration is worth nothing, so it is refused."""
        conflicts = {"measured_overlay": {"keeper": True, "touchpoint": False}}
        ok, left = gta.classify_declared(conflicts, ("measured_overlay",), None)
        self.assertEqual(ok, {})
        self.assertIn("fail-closed", left["measured_overlay"]["refused"])

    def test_the_generic_override_container_admits_only_if_EVERY_field_verifies(self):
        """replay_keeper's --set writes the nested container as well.

        The container is admitted only when every field that moved inside it
        verifies on its own terms — one un-declared or non-default nested field
        and the whole container stays a conflict.
        """
        good = {
            "prb_overrides": {
                "keeper": {"measured_overlay": True, "dependent_flag": True, "x": 1},
                "touchpoint": {
                    "measured_overlay": False,
                    "dependent_flag": False,
                    "x": 1,
                },
            }
        }
        ok, left = gta.classify_declared(
            good, ("measured_overlay", "dependent_flag"), DEFAULTS
        )
        self.assertEqual(left, {})
        self.assertEqual(
            sorted(ok["prb_overrides"]["nested"]),
            ["dependent_flag", "measured_overlay"],
        )

        # One extra nested field moved that nobody declared -> refused whole.
        bad = {
            "prb_overrides": {
                "keeper": {"measured_overlay": True, "some_multiplier": 1.0},
                "touchpoint": {"measured_overlay": False, "some_multiplier": 1.25},
            }
        }
        ok, left = gta.classify_declared(bad, ("measured_overlay",), DEFAULTS)
        self.assertEqual(ok, {})
        self.assertIn("some_multiplier", left["prb_overrides"]["refused"])

    def test_a_reason_is_mandatory(self):
        """A degradation with no stated cause is the silent drift to refuse."""
        with self.assertRaises(SystemExit) as cm:
            gta.build(
                REPO_ROOT / "nonexistent",
                "run-id",
                REPO_ROOT / "nonexistent",
                None,
                ("measured_overlay",),
                None,
            )
        self.assertIn("--degradation-reason", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
