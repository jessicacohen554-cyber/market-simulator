"""Coal-passthrough counting in the DOF ledger generator (rule 21 ``[R-DOF]``).

Two gates decide how many fitted scalars ``scripts/build_dof_ledger.py`` attests
for the coal passthrough surface, and neither was covered by a test before
xiso-7:

1. **The resolve gate (caiso-236, the OVER-count half).** An armed
   ``coal_*_passthrough_sigmoid`` toggle over an ``(ISO, supply)`` pair that
   ``COAL_SIGMOID_DEFAULTS`` does not characterize engages no parameters at all —
   the solve falls back to the flat passthrough — so it must put no row in the
   ledger.
2. **The follower gate (xiso-7, the UNDER-count half).** ``prb_follower`` is the
   one tier with no toggle of its own: armed by the conjunction
   ``coal_prb_passthrough_sigmoid AND coal_prb_passthrough_tiered``, it resolves a
   SECOND four-parameter set that ``n_scalars = 4 * len(sigmoids)`` counted
   nowhere.

The load-bearing test is :meth:`TestFollowerGate.test_gate_agrees_with_the_solve`:
the ledger's gate is pinned to ``data.fuel.trajectories.coal_sigmoid_params``, the
resolver the dispatch actually calls, so the attestation cannot drift away from
what the solve consumes.

Record: ``results/calibration/FINDING-xiso7-prb-follower-dof-undercount-2026-09-02.md``.
"""

from __future__ import annotations

import unittest

from market_sim.config.scenarios import COAL_SIGMOID_DEFAULTS, ScenarioConfig
from scripts.build_dof_ledger import _prb_follower_engaged, config_entries


def _sigmoid_row(entries: list[dict]) -> dict | None:
    """Return the ``COAL_SIGMOID_DEFAULTS[*]`` entry among ``entries``, if any."""
    rows = [
        e
        for e in entries
        if str(e.get("name", "")).startswith("COAL_SIGMOID_DEFAULTS[")
    ]
    return rows[0] if rows else None


class TestResolveGate(unittest.TestCase):
    """caiso-236: an armed toggle over an uncharacterized supply attests nothing."""

    def test_armed_over_no_registry_entry_emits_no_row(self):
        # CAISO arms coal_prb_passthrough_sigmoid and COAL_SIGMOID_DEFAULTS holds
        # no ("CAISO", *) key at all -- the phantom caiso-236 removed.
        self.assertNotIn(("CAISO", "prb"), COAL_SIGMOID_DEFAULTS)
        entries = config_entries({"coal_prb_passthrough_sigmoid": True}, "CAISO")
        self.assertIsNone(_sigmoid_row(entries))

    def test_only_resolving_toggles_are_counted(self):
        # PJM characterizes bituminous and subbituminous but not prb, so arming
        # all three attests eight scalars, not twelve.
        self.assertIn(("PJM", "bituminous"), COAL_SIGMOID_DEFAULTS)
        self.assertNotIn(("PJM", "prb"), COAL_SIGMOID_DEFAULTS)
        row = _sigmoid_row(
            config_entries(
                {
                    "coal_prb_passthrough_sigmoid": True,
                    "coal_bit_passthrough_sigmoid": True,
                    "coal_sub_passthrough_sigmoid": True,
                },
                "PJM",
            )
        )
        self.assertIsNotNone(row)
        self.assertEqual(row["n_scalars"], 8)


class TestFollowerGate(unittest.TestCase):
    """xiso-7: the tiered PRB follower tier is a counted parameter set."""

    def test_tiered_adds_its_own_four_scalars(self):
        # ERCOT characterizes both ("ERCOT", "prb") and ("ERCOT", "prb_follower"),
        # with a distinct floor -- a genuinely separate fitted surface.
        self.assertNotEqual(
            COAL_SIGMOID_DEFAULTS[("ERCOT", "prb")],
            COAL_SIGMOID_DEFAULTS[("ERCOT", "prb_follower")],
        )
        baseload_only = {"coal_prb_passthrough_sigmoid": True}
        tiered = {**baseload_only, "coal_prb_passthrough_tiered": True}
        self.assertEqual(
            _sigmoid_row(config_entries(baseload_only, "ERCOT"))["n_scalars"], 4
        )
        self.assertEqual(_sigmoid_row(config_entries(tiered, "ERCOT"))["n_scalars"], 8)

    def test_tiered_names_the_follower_tier_in_its_provenance(self):
        row = _sigmoid_row(
            config_entries(
                {
                    "coal_prb_passthrough_sigmoid": True,
                    "coal_prb_passthrough_tiered": True,
                },
                "ERCOT",
            )
        )
        self.assertIn("prb_follower", row["where"])

    def test_tiered_alone_is_not_enough(self):
        # The gate is a CONJUNCTION: tiered without the prb sigmoid never reaches
        # prb_follower_passthrough_series, so it attests nothing. This is the
        # ERCOT keeper's own state (coal_perplant_offer_curves disarmed the
        # sigmoids while leaving coal_prb_passthrough_tiered armed).
        self.assertFalse(
            _prb_follower_engaged({"coal_prb_passthrough_tiered": True}, "ERCOT")
        )
        self.assertIsNone(
            _sigmoid_row(config_entries({"coal_prb_passthrough_tiered": True}, "ERCOT"))
        )

    def test_unresolved_follower_is_not_counted(self):
        # PJM arms the conjunction but has no ("PJM", "prb_follower") entry, so
        # prb_follower_passthrough_series falls back to the baseload prb curve --
        # no additional free parameters exist to attest.
        self.assertNotIn(("PJM", "prb_follower"), COAL_SIGMOID_DEFAULTS)
        row = _sigmoid_row(
            config_entries(
                {
                    "coal_bit_passthrough_sigmoid": True,
                    "coal_sub_passthrough_sigmoid": True,
                    "coal_prb_passthrough_sigmoid": True,
                    "coal_prb_passthrough_tiered": True,
                },
                "PJM",
            )
        )
        self.assertEqual(row["n_scalars"], 8)

    def test_follower_alone_still_emits_the_row(self):
        # The follower set can resolve (here: fully specified by explicit fields)
        # for an ISO whose BASELOAD prb pair does not. The tier is then live and is
        # the row's only engaged parameter set -- which is why the row's emission
        # gates on `tiers`, not on `sigmoids`.
        sc = {
            "coal_prb_passthrough_sigmoid": True,
            "coal_prb_passthrough_tiered": True,
            "coal_prb_follower_floor": 0.6,
            "coal_prb_follower_ceil": 1.1,
            "coal_prb_follower_gas_mid": 3.0,
            "coal_prb_follower_gas_slope": 2.5,
        }
        self.assertNotIn(("NYISO", "prb"), COAL_SIGMOID_DEFAULTS)
        self.assertNotIn(("NYISO", "prb_follower"), COAL_SIGMOID_DEFAULTS)
        row = _sigmoid_row(config_entries(sc, "NYISO"))
        self.assertIsNotNone(row)
        self.assertEqual(row["n_scalars"], 4)

    def test_gate_agrees_with_the_solve(self):
        """The ledger's gate must equal the resolver the dispatch actually calls.

        ``coal_sigmoid_params(cfg, "prb_follower")`` is the sole path by which the
        follower parameters reach a fleet; if the ledger's gate ever disagrees with
        it, the attestation misstates the solve's free parameters in one direction
        or the other.
        """
        from market_sim.data.fuel.trajectories import coal_sigmoid_params

        cases = [
            ("ERCOT", {}),
            ("ERCOT", {"coal_prb_follower_floor": 0.5}),
            ("MISO", {}),
            ("PJM", {}),
            ("NYISO", {}),
            (
                "NYISO",
                {
                    f"coal_prb_follower_{p}": v
                    for p, v in (
                        ("floor", 0.6),
                        ("ceil", 1.1),
                        ("gas_mid", 3.0),
                        ("gas_slope", 2.5),
                    )
                },
            ),
        ]
        for iso, overrides in cases:
            with self.subTest(iso=iso, overrides=sorted(overrides)):
                sc = {
                    "coal_prb_passthrough_sigmoid": True,
                    "coal_prb_passthrough_tiered": True,
                    **overrides,
                }
                cfg = ScenarioConfig(iso=iso, **sc)
                self.assertEqual(
                    _prb_follower_engaged(sc, iso),
                    coal_sigmoid_params(cfg, "prb_follower") is not None,
                )


if __name__ == "__main__":
    unittest.main()
