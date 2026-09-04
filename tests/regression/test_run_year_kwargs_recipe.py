"""The ONE sanctioned fleet-only recipe reconstruction, and the pattern it retires.

Incident (caiso-243 §7.3, ``PRECOMMIT-caiso243-ADDENDUM-recipe-repair-2026-09-04.md``):
from caiso-202 to caiso-243 every zero-LP probe in the CAISO lane rebuilt a
keeper's recipe for ``run_calibration.run_year(..., fleet_only=True)`` as

    {k: v for k, v in meta.items() if k in run_year's parameter names}

A filter by parameter NAME silently drops every ``meta.json`` key whose solve
kwarg is spelled differently — above all ``coal_prb_sigmoid_overrides`` ->
``prb_overrides``, the generic override bag carrying dozens of structural flags
on EVERY ISO's keeper (36 on CAISO, 50 on ERCOT, 42 on MISO). The probes
measured a lookalike recipe (monthly-survey gas) while the keeper priced gas at
the daily spot level; a session's published ratios were voided.

caiso-244 closed it structurally: :func:`scripts.replay_keeper.run_year_kwargs`
is the strict path (``build_kwargs`` -> the ``run_year`` subset under
``solve_and_persist``'s own names), :func:`scripts.lib.bundle_fleet
.full_run_year_kwargs` delegates to it, and the tests below pin (a) the
remaps the by-name pattern loses, (b) that the two public helpers agree, (c)
that the unreachable-kwarg disclosure is complete and honest, and (d) that no
NEW probe re-introduces the by-name pattern (the pre-caiso-244 probes are the
frozen calibration record and stay on an explicit allowlist). No LP is built.
"""

from __future__ import annotations

import inspect
import re
import unittest
from pathlib import Path

from scripts import replay_keeper as rk
from scripts import run_calibration_full as rcf
from scripts.lib.bundle_fleet import full_run_year_kwargs
from scripts.run_calibration import run_year

REPO = Path(__file__).resolve().parents[2]

#: A minimal but structurally complete meta: the renamed keys the by-name
#: pattern loses, one same-name key, and provenance keys build_kwargs ignores.
META = {
    "iso": "CAISO",
    "years": [2025],
    "hours": 8760,
    "timestamp": "2026-09-04T00:00:00",
    "git_sha": "deadbeef",
    "gas_prices": {"2025": 3.0},
    "commitment": False,
    "commitment_screen_coal": True,
    "coal_prb_sigmoid_overrides": {
        "caiso_citygate_spot_level": True,
        "capacity_deliverability_limits": True,
    },
    "coal_bit_passthrough_sigmoid": True,
    "coal_bit_sigmoid_overrides": {"coal_bit_passthrough_floor": 0.65},
    "gas_offer_curve": True,
    "strict_demand_profile": False,
    "btm_backfill_year": None,
}

#: The by-name pattern, reproduced verbatim so the test states what it retires.
_BY_NAME_SKIP = {"year", "iso", "hours", "gas_price", "ttc_overrides", "fleet_only"}


def _by_name(meta: dict) -> dict:
    params = inspect.signature(run_year).parameters
    return {k: v for k, v in meta.items() if k in params and k not in _BY_NAME_SKIP}


class TestRunYearKwargs(unittest.TestCase):
    """``replay_keeper.run_year_kwargs`` semantics."""

    def test_renamed_keys_are_carried_under_run_year_names(self):
        """The three remapped override channels arrive under run_year's names."""
        kw = rk.run_year_kwargs(META)
        self.assertEqual(kw["prb_overrides"], META["coal_prb_sigmoid_overrides"])
        self.assertEqual(kw["bit_overrides"], META["coal_bit_sigmoid_overrides"])
        self.assertTrue(kw["coal_bit_sigmoid"])
        self.assertTrue(kw["commitment_screen_coal"])
        self.assertFalse(kw["commitment_enabled"])
        self.assertTrue(kw["gas_offer_curve"])

    def test_by_name_pattern_loses_the_structural_bag(self):
        """The retired pattern drops exactly the keys this helper recovers."""
        lost = set(rk.run_year_kwargs(META)) - set(_by_name(META))
        self.assertIn("prb_overrides", lost)
        self.assertIn("bit_overrides", lost)
        self.assertIn("coal_bit_sigmoid", lost)
        self.assertIn("commitment_enabled", lost)

    def test_every_key_is_a_run_year_parameter_and_none_is_plumbing(self):
        """The result splats straight into run_year after the positional four."""
        params = set(inspect.signature(run_year).parameters)
        kw = rk.run_year_kwargs(META)
        self.assertTrue(set(kw) <= params, set(kw) - params)
        self.assertFalse(set(kw) & rk.RUN_YEAR_NON_RECIPE)

    def test_remap_targets_exist_and_sources_are_solve_kwargs(self):
        """RUN_YEAR_REMAP is read off solve_and_persist's own run_year call."""
        run_params = set(inspect.signature(run_year).parameters)
        solve_params = set(inspect.signature(rcf.solve_and_persist).parameters)
        for src, dst in rk.RUN_YEAR_REMAP.items():
            with self.subTest(src=src):
                self.assertIn(src, solve_params)
                self.assertIn(dst, run_params)
                self.assertNotIn(src, run_params)

    def test_strictness_is_inherited(self):
        """An unmapped meta key still hard-errors — never a silent drop."""
        bad = dict(META, definitely_not_a_kwarg=1)
        with self.assertRaises(SystemExit):
            rk.run_year_kwargs(bad)


class TestRunYearUnreachable(unittest.TestCase):
    """The disclosure of what a fleet-only rebuild cannot carry."""

    def test_defaults_are_silent(self):
        """A key recorded at solve_and_persist's default is inert and not reported."""
        self.assertEqual(rk.run_year_unreachable(META), {})

    def test_non_default_unreachable_key_is_reported(self):
        """A post-LP overlay recorded ON is disclosed, not lost."""
        meta = dict(META, iso="ERCOT", ercot_rtordpa_overlay=True)
        unreachable = rk.run_year_unreachable(meta)
        self.assertEqual(unreachable.get("ercot_rtordpa_overlay"), True)
        self.assertNotIn("ercot_rtordpa_overlay", rk.run_year_kwargs(meta))


class TestBundleFleetDelegates(unittest.TestCase):
    """``scripts.lib.bundle_fleet.full_run_year_kwargs`` is the same mapping."""

    def test_agrees_with_replay_keeper_plus_plumbing(self):
        kw = full_run_year_kwargs(META)
        self.assertTrue(kw.pop("fleet_only"))
        self.assertEqual(kw.pop("ttc_overrides"), {})
        self.assertEqual(kw, rk.run_year_kwargs(META))


class TestNoNewByNameProbes(unittest.TestCase):
    """No probe written after caiso-244 may rebuild a recipe by parameter name."""

    #: Pre-caiso-244 probes that carry the retired pattern. They are the
    #: frozen calibration record (scripts/README.md) and are NOT rewritten;
    #: their keeper-relative numbers are read with that caveat. Adding a file
    #: here is a rule-24-class decision, not a convenience.
    FROZEN_RECORD = frozenset(
        {
            "_caiso202_marginal_rung.py",
            "_caiso216_belly_surplus.py",
            "_caiso221_surplus_design.py",
            "_caiso230_abovefloor_decomposition.py",
            "_caiso239_st_gas_committed_footprint.py",
            "_caiso240_default_hr_mult_census.py",
            "_caiso240_gstruct_presolve.py",
            "_caiso241_cell_bound.py",
            "_caiso241_gstruct_presolve.py",
        }
    )
    PATTERN = re.compile(r"k in params and k not in skip")

    def test_pattern_is_confined_to_the_frozen_record(self):
        offenders = sorted(
            p.name
            for p in (REPO / "scripts" / "probes").glob("*.py")
            if self.PATTERN.search(p.read_text())
        )
        new = sorted(set(offenders) - self.FROZEN_RECORD)
        self.assertEqual(
            new,
            [],
            "a probe rebuilds a recipe by run_year parameter NAME — use "
            "scripts.replay_keeper.run_year_kwargs (caiso-243 §7.3 / caiso-244): "
            f"{new}",
        )


if __name__ == "__main__":
    unittest.main()
