"""The ``scenario`` registration kind (SCN-WS0 deliverable 5).

A scenario-campaign arm is only meaningful against its campaign's reference,
so the registrar has to carry three things the other kinds do not: which
campaign an arm belongs to, which case IS the reference, and enough of the CO2
series to draw the delta the explorer shows. These tests pin all three, plus
the two ways the grouping can go wrong quietly — a campaign whose reference is
not registered, and a non-scenario run picking up campaign fields.
"""

from __future__ import annotations

import unittest

from scripts import register_forecast_run as R


def _sidecar(run_id: str, case: str, reference_case: str, co2: dict) -> dict:
    """A scenario-arm sidecar shaped like register_forecast_baseline's."""
    return {
        "run_id": run_id,
        "meta": {
            "iso": "NEISO",
            "kind": "scenario",
            "label": "scn-smoke",
            "mode": "forecast",
            "campaign": "scn-ws0-smoke",
            "case": case,
            "reference_case": reference_case,
            "start_year": min(co2),
            "end_year": max(co2),
            "solved_years": sorted(co2),
            "n_solved_years": len(co2),
            "year_summary": [{"year": y, "co2_mt": v} for y, v in sorted(co2.items())],
        },
        "score": None,
        "invariants": [],
    }


class TestClassify(unittest.TestCase):
    def test_scenario_kind_tiers_and_families_on_its_campaign(self):
        kind, tier, family = R.classify(
            "x", {"kind": "scenario", "campaign": "scn-ws0-smoke"}, False
        )
        self.assertEqual((kind, tier), ("scenario", "scenario"))
        # The family IS the campaign — that is what the explorer groups on.
        self.assertEqual(family, "scn-ws0-smoke")

    def test_a_scenario_run_without_a_campaign_still_classifies(self):
        kind, tier, family = R.classify("x", {"kind": "scenario"}, False)
        self.assertEqual((kind, tier, family), ("scenario", "scenario", "scenario"))

    def test_scenario_is_orderable_in_both_facets(self):
        self.assertIn("scenario", R._KIND_ORDER)
        self.assertIn("scenario", R._TIER_ORDER)

    def test_other_kinds_are_unchanged(self):
        self.assertEqual(R.classify("x", {"kind": "t1f"}, False)[0], "t1f")
        self.assertEqual(R.classify("x", {"kind": "crossover"}, False)[0], "t1x")
        self.assertEqual(R.classify("x", {"kind": "readiness"}, False)[0], "readiness")


class TestCampaignBlock(unittest.TestCase):
    def test_scenario_arm_carries_campaign_case_reference_and_series(self):
        entry, payload = R.build_run_artifacts(
            _sidecar("neiso-carb", "CARB", "REF", {2026: 13.6, 2027: 13.1}), {}
        )
        self.assertEqual(entry["kind"], "scenario")
        self.assertEqual(entry["campaign"], "scn-ws0-smoke")
        self.assertEqual(entry["case"], "CARB")
        self.assertEqual(entry["reference_case"], "REF")
        self.assertEqual(entry["co2_mt"], [[2026, 13.6], [2027, 13.1]])
        self.assertEqual(payload["kind"], "scenario")

    def test_non_scenario_runs_carry_the_keys_as_nulls(self):
        # One shape for every entry, so the explorer never branches on absence.
        entry, _ = R.build_run_artifacts(
            {
                "run_id": "neiso-t1f",
                "meta": {"iso": "NEISO", "kind": "t1f", "year_summary": []},
                "invariants": [],
            },
            {},
        )
        for key in ("campaign", "case", "reference_case", "co2_mt"):
            self.assertIn(key, entry)
            self.assertIsNone(entry[key], key)


class TestCampaignDeltas(unittest.TestCase):
    def _entries(self, **kw):
        arms = [
            _sidecar("neiso-ref", "REF", "REF", {2026: 16.3, 2027: 16.0}),
            _sidecar("neiso-carb", "CARB", "REF", {2026: 13.6, 2027: 13.1}),
        ]
        return [R.build_run_artifacts(a, {})[0] for a in arms]

    def test_delta_is_the_arm_minus_its_campaign_reference(self):
        entries = self._entries()
        R.attach_campaign_deltas(entries)
        by_id = {e["id"]: e for e in entries}
        self.assertEqual(
            by_id["neiso-carb"]["co2_delta_mt"], [[2026, -2.7], [2027, -2.9]]
        )

    def test_the_reference_arm_differences_to_zero_against_itself(self):
        # An explicit zero baseline, so the sparkline's zero line is drawn
        # rather than implied.
        entries = self._entries()
        R.attach_campaign_deltas(entries)
        by_id = {e["id"]: e for e in entries}
        self.assertEqual(by_id["neiso-ref"]["co2_delta_mt"], [[2026, 0.0], [2027, 0.0]])

    def test_no_reference_registered_means_no_delta_not_a_guess(self):
        arm = R.build_run_artifacts(
            _sidecar("neiso-carb", "CARB", "REF", {2026: 13.6}), {}
        )[0]
        entries = [arm]
        R.attach_campaign_deltas(entries)
        self.assertIsNone(entries[0]["co2_delta_mt"])

    def test_years_present_in_only_one_arm_are_dropped_not_zero_filled(self):
        arms = [
            R.build_run_artifacts(
                _sidecar("neiso-ref", "REF", "REF", {2026: 16.3}), {}
            )[0],
            R.build_run_artifacts(
                _sidecar("neiso-carb", "CARB", "REF", {2026: 13.6, 2027: 13.1}), {}
            )[0],
        ]
        R.attach_campaign_deltas(arms)
        by_id = {e["id"]: e for e in arms}
        self.assertEqual(by_id["neiso-carb"]["co2_delta_mt"], [[2026, -2.7]])

    def test_non_scenario_entries_get_an_explicit_null_delta(self):
        entries = [
            R.build_run_artifacts(
                {
                    "run_id": "neiso-t1f",
                    "meta": {"iso": "NEISO", "kind": "t1f"},
                    "invariants": [],
                },
                {},
            )[0]
        ]
        R.attach_campaign_deltas(entries)
        self.assertIsNone(entries[0]["co2_delta_mt"])

    def test_campaigns_do_not_cross_contaminate(self):
        a = R.build_run_artifacts(_sidecar("a-ref", "REF", "REF", {2026: 10.0}), {})[0]
        b = R.build_run_artifacts(_sidecar("b-carb", "CARB", "REF", {2026: 5.0}), {})[0]
        b["campaign"] = "other-campaign"
        entries = [a, b]
        R.attach_campaign_deltas(entries)
        # b's own campaign has no registered reference, so it gets no delta —
        # never the first campaign's reference by accident.
        self.assertIsNone(entries[1]["co2_delta_mt"])


if __name__ == "__main__":
    unittest.main()
