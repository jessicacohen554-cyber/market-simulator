"""The composite per-year recipe map: writer, consumer, and the ERCOT keeper.

A COMPOSITE bundle spans years that solved under DIFFERENT configs, but
``meta.json`` records only ONE. For the ERCOT two-config keeper (owner ruling
2026-08-26) it records the FORWARD config, so the carve-out years'
``ercot_offer_swcap_clip=true`` and x33.0 ``offer_curve_by_group`` peak bands
appeared in NO meta.json and had no CLI flag — and a ``--replay-bundle`` of
that keeper silently solved the FORWARD config on a carve-out year and
reported it as the keeper (``RESULT-ercot259`` §4: the control replayed 2023
at ``swcap=False`` / CC_REGULAR ``peak=4.576``, C3a -39.6 %, against the
keeper's own ``peak=151.008`` / C3a -7.3 %).

These pin both halves of the ercot-260 fix:

* WRITER — ``scripts/stamp_config_partition.py`` DERIVES the map by diffing
  each leg's own committed ``run_config`` against the base, so no value is
  hand-typed, and ``--check`` re-derives it later.
* CONSUMER — ``replay_keeper.enforce_single_recipe_partition`` applies the
  recorded overlay for the requested span, and REFUSES a span that mixes
  recipes rather than solving one group's config over every year.
"""

import json
import unittest

from scripts.replay_keeper import (
    CONFIG_PARTITION_KEY,
    config_partition_overlay,
    enforce_single_recipe_partition,
    partition_years_by_recipe,
)
from scripts.stamp_config_partition import (
    YEAR_DRIVEN_FIELDS,
    build_block,
    derive_overlay,
    parse_leg,
)
from tests.helpers import REPO_ROOT

REPO = REPO_ROOT

#: The committed ERCOT two-config keeper and its three solve legs.
KEEPER = REPO / "results" / "calibration" / "ercot256_five_year_keeper"
KEEPER_LEGS = [
    "2021,2022=run_config_carveout_2021_2022.json",
    "2023=run_config_carveout_2023.json",
    "2024,2025=run_config_forward_2024_2025.json",
]

_META = {
    "iso": "ERCOT",
    "years": [2021, 2022, 2023],
    CONFIG_PARTITION_KEY: {
        "_schema": "composite-per-year-recipe/v1",
        "_why": "annotation, never a recipe key",
        "2021": {"ercot_offer_swcap_clip": True},
        "2022": {"ercot_offer_swcap_clip": True},
    },
}


class TestOverlayRead(unittest.TestCase):
    def test_recorded_year_returns_its_overlay(self):
        self.assertEqual(
            config_partition_overlay(_META, 2021), {"ercot_offer_swcap_clip": True}
        )

    def test_absent_year_is_the_base_recipe(self):
        # 2023 is not in the block: it solved the meta recipe unchanged.
        self.assertEqual(config_partition_overlay(_META, 2023), {})

    def test_annotation_keys_are_never_recipe_keys(self):
        for year in (2021, 2022, 2023):
            for key in config_partition_overlay(_META, year):
                self.assertFalse(key.startswith("_"), key)

    def test_a_bundle_with_no_block_is_unaffected(self):
        self.assertEqual(config_partition_overlay({"iso": "MISO"}, 2024), {})


class TestPartition(unittest.TestCase):
    def test_years_group_by_shared_overlay(self):
        groups = partition_years_by_recipe(_META, [2021, 2022, 2023])
        self.assertEqual(
            [(sorted(ov), ys) for ov, ys in groups],
            [(["ercot_offer_swcap_clip"], [2021, 2022]), ([], [2023])],
        )

    def test_a_single_recipe_span_is_one_group(self):
        self.assertEqual(len(partition_years_by_recipe(_META, [2021, 2022])), 1)


class TestConsumer(unittest.TestCase):
    def test_overlay_reaches_the_generic_scenario_config_channel(self):
        kwargs: dict = {}
        enforce_single_recipe_partition(_META, [2021, 2022], kwargs)
        self.assertIs(kwargs["prb_overrides"]["ercot_offer_swcap_clip"], True)

    def test_base_recipe_years_add_nothing(self):
        kwargs: dict = {"prb_overrides": {"existing": 1}}
        enforce_single_recipe_partition(_META, [2023], kwargs)
        self.assertEqual(kwargs["prb_overrides"], {"existing": 1})

    def test_a_mixed_recipe_span_is_REFUSED(self):
        # The defect itself: one solve carries one config, so replaying
        # 2021-2023 together would put one group's recipe on every year.
        with self.assertRaises(SystemExit) as ctx:
            enforce_single_recipe_partition(_META, [2021, 2022, 2023], {})
        msg = str(ctx.exception)
        self.assertIn("recipe groups", msg)
        self.assertIn("--years", msg)

    def test_an_unconsumable_key_is_a_hard_error_never_a_silent_drop(self):
        meta = {"years": [2021], CONFIG_PARTITION_KEY: {"2021": {"no_such_field": 1}}}
        with self.assertRaises(SystemExit) as ctx:
            enforce_single_recipe_partition(meta, [2021], {})
        self.assertIn("no_such_field", str(ctx.exception))

    def test_the_overlay_never_mutates_the_callers_meta(self):
        # build_kwargs binds the override bag straight off meta, so a
        # setdefault-and-mutate consumer would contaminate the BASE recipe for
        # every later group of the same span.
        meta = json.loads(json.dumps(_META))
        bag = {"keeper_key": True}
        kwargs = {"prb_overrides": bag}
        enforce_single_recipe_partition(meta, [2021], kwargs)
        self.assertEqual(bag, {"keeper_key": True})
        self.assertEqual(meta, _META)

    def test_repeated_groups_do_not_leak_across_calls(self):
        first: dict = {}
        enforce_single_recipe_partition(_META, [2021], first)
        second: dict = {}
        enforce_single_recipe_partition(_META, [2023], second)
        self.assertIn("ercot_offer_swcap_clip", first["prb_overrides"])
        # A base-recipe year must leave kwargs untouched entirely — not even an
        # empty bag — so a one-config bundle's replay stays byte-identical.
        self.assertEqual(second, {})


class TestWriterDerivation(unittest.TestCase):
    def test_year_driven_fields_are_never_recipe_keys(self):
        base = {"weather_year": 2024, "ordc_voll": 5000.0, "a": 1}
        leg = {"weather_year": 2021, "ordc_voll": 9000.0, "a": 2}
        self.assertEqual(derive_overlay(base, leg), {"a": 2})

    def test_an_identical_leg_derives_an_empty_overlay(self):
        self.assertEqual(derive_overlay({"a": 1}, {"a": 1}), {})

    def test_the_exclusion_set_is_the_documented_four(self):
        self.assertEqual(
            YEAR_DRIVEN_FIELDS,
            frozenset(
                {"weather_year", "gas_price_override", "ordc_voll", "ordc_mcl_mw"}
            ),
        )

    def test_leg_spec_parsing(self):
        self.assertEqual(parse_leg("2021,2022=rc.json"), ([2021, 2022], "rc.json"))
        with self.assertRaises(SystemExit):
            parse_leg("2021")


@unittest.skipUnless(KEEPER.is_dir(), "ERCOT two-config keeper bundle not present")
class TestErcotKeeperRoundTrip(unittest.TestCase):
    """The fix, measured on the committed keeper this defect was found on."""

    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads((KEEPER / "meta.json").read_text())
        cls.derived = build_block(
            KEEPER, [parse_leg(s) for s in KEEPER_LEGS], "run_config.json"
        )

    def test_the_stamped_block_re_derives_from_the_committed_legs(self):
        # Effective-config equivalence: a stamped key already equal to the base
        # is a redundant pin, not drift (the hand-typed block pins
        # ercot_zonal_spread_ep_referenced=True on 2021/2022, the base value).
        base = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
        stamped = self.meta[CONFIG_PARTITION_KEY]
        for year in ("2021", "2022", "2023"):
            self.assertEqual(
                {**base, **{k: v for k, v in stamped[year].items() if k[0] != "_"}},
                {**base, **self.derived[year]},
                f"{year} would replay under a different config than its run_config",
            )

    def test_the_carve_out_years_carry_the_two_keys_that_had_no_home(self):
        for year in (2021, 2022, 2023):
            overlay = config_partition_overlay(self.meta, year)
            self.assertIs(overlay["ercot_offer_swcap_clip"], True)
            self.assertAlmostEqual(
                overlay["offer_curve_by_group"]["CC_REGULAR"]["peak"], 151.008
            )

    def test_the_forward_years_are_the_base_recipe(self):
        for year in (2024, 2025):
            self.assertEqual(config_partition_overlay(self.meta, year), {})

    def test_a_2023_replay_now_solves_the_CARVE_OUT_not_the_forward_config(self):
        # The regression this closes: ercot-259's control replayed 2023 and
        # solved swcap=False / peak=4.576 (the forward config).
        kwargs: dict = {}
        enforce_single_recipe_partition(self.meta, [2023], kwargs)
        bag = kwargs["prb_overrides"]
        self.assertIs(bag["ercot_offer_swcap_clip"], True)
        self.assertAlmostEqual(
            bag["offer_curve_by_group"]["CC_REGULAR"]["peak"], 151.008
        )

    def test_the_full_span_is_refused_rather_than_silently_mis_solved(self):
        with self.assertRaises(SystemExit):
            enforce_single_recipe_partition(
                self.meta, [2021, 2022, 2023, 2024, 2025], {}
            )

    def test_the_three_legs_are_exactly_three_recipe_groups(self):
        groups = partition_years_by_recipe(self.meta, [2021, 2022, 2023, 2024, 2025])
        self.assertEqual([ys for _, ys in groups], [[2021, 2022], [2023], [2024, 2025]])


class TestBothReplayEntryPointsConsumeIt(unittest.TestCase):
    def test_run_replay_bundle_calls_the_same_consumer(self):
        # The two entry points must not diverge: a fix on one path only would
        # leave --replay-bundle (the CI-dispatchable form) still defective.
        src = (REPO / "scripts" / "run_calibration_full.py").read_text()
        self.assertIn(
            'rk.enforce_single_recipe_partition(meta, kwargs["years"], kwargs)', src
        )
        src2 = (REPO / "scripts" / "replay_keeper.py").read_text()
        self.assertIn(
            'enforce_single_recipe_partition(meta, kwargs["years"], kwargs)', src2
        )

    def test_build_kwargs_still_treats_the_block_as_provenance(self):
        from scripts.replay_keeper import build_kwargs

        kwargs = build_kwargs(
            {"iso": "ERCOT", "years": [2023], CONFIG_PARTITION_KEY: {"2023": {}}}
        )
        self.assertNotIn(CONFIG_PARTITION_KEY, kwargs)


if __name__ == "__main__":
    unittest.main()
