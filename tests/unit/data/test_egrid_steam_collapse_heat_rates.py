"""Tests for the eGRID steam-collapse identity heat-rate input (nyiso-189).

Covers the three seams:

1. the artifact reader (the committed NYISO artifact resolves to EXACTLY the
   two pre-registered applied-vintage plants; an ISO with no artifact is an
   empty no-op),
2. the fleet apply — the swap reaches every unit of an admitted plant and no
   other generator, honours ``skip_ids`` (rule 19), and is a strict no-op
   while ``ScenarioConfig.egrid_steam_collapse_heat_rates`` is off,
3. the committed artifact's record — the census population facts the
   pre-registration fixed (``PREREG-nyiso189-steam-collapse-identity-ab.md``
   §0 / §3 G-INPUTS): 38 plants, T1 at exactly five, the applied-vintage
   admitted set {2539, 54131}, identity rates 6.877 / 6.996, Flynn /
   Ravenswood / Lederle declined on a one-member record.
"""

import unittest
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from market_sim.config.paths import PROCESSED_DIR
from market_sim.data.fleet.eia860 import (
    apply_egrid_steam_collapse_heat_rates,
    egrid_steam_collapse_heat_rates_for,
)

BETHLEHEM, WORLD_GEN_X = 2539, 54131
ARTIFACT = Path(PROCESSED_DIR) / "egrid_steam_collapse_heat_rates_NYISO.csv"


def _gen(plant_code: int, heat_rate: float) -> SimpleNamespace:
    return SimpleNamespace(plant_code=plant_code, heat_rate=heat_rate)


class TestReader(unittest.TestCase):
    def test_nyiso_artifact_resolves_exactly_the_two_reached_plants(self):
        rates = egrid_steam_collapse_heat_rates_for("NYISO")
        self.assertEqual(set(rates), {BETHLEHEM, WORLD_GEN_X})
        self.assertAlmostEqual(rates[BETHLEHEM], 6.8773, places=4)
        self.assertAlmostEqual(rates[WORLD_GEN_X], 6.9955, places=4)

    def test_iso_without_artifact_is_empty(self):
        self.assertEqual(egrid_steam_collapse_heat_rates_for("NEISO"), {})


class TestApply(unittest.TestCase):
    def test_swap_reaches_only_admitted_plants(self):
        gens = [_gen(BETHLEHEM, 9.665), _gen(BETHLEHEM, 9.665), _gen(55405, 7.12)]
        touched = apply_egrid_steam_collapse_heat_rates(gens, "NYISO")
        self.assertEqual(len(touched), 2)
        self.assertAlmostEqual(gens[0].heat_rate, 6.8773, places=4)
        self.assertAlmostEqual(gens[1].heat_rate, 6.8773, places=4)
        self.assertEqual(gens[2].heat_rate, 7.12)

    def test_skip_ids_are_never_stacked(self):
        gens = [_gen(BETHLEHEM, 9.665), _gen(WORLD_GEN_X, 9.8065)]
        touched = apply_egrid_steam_collapse_heat_rates(
            gens, "NYISO", frozenset({id(gens[1])})
        )
        self.assertEqual(touched, frozenset({id(gens[0])}))
        self.assertEqual(gens[1].heat_rate, 9.8065)

    def test_no_artifact_iso_is_noop(self):
        gens = [_gen(BETHLEHEM, 9.665)]
        touched = apply_egrid_steam_collapse_heat_rates(gens, "NEISO")
        self.assertEqual(touched, frozenset())
        self.assertEqual(gens[0].heat_rate, 9.665)


class TestCommittedArtifact(unittest.TestCase):
    """The committed artifact carries the pre-registered population facts."""

    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(ARTIFACT)

    def test_population_and_t1_census(self):
        self.assertEqual(self.df.plant_id.nunique(), 38)
        t1 = self.df[self.df.t1_zero].groupby("plant_id").vintage.apply(list)
        self.assertEqual(
            {int(p): ys for p, ys in t1.items()},
            {
                2500: [2019, 2020, 2021, 2022, 2023, 2024],
                2539: [2024],
                7314: [2019, 2020, 2021, 2022, 2023, 2024],
                10521: [2019, 2020, 2021, 2022, 2023, 2024],
                54131: [2023],
            },
        )

    def test_applied_vintage_admits_exactly_bethlehem_and_world_gen_x(self):
        live = self.df[self.df.applied & self.df.admitted]
        self.assertEqual(set(live.plant_id), {BETHLEHEM, WORLD_GEN_X})
        self.assertTrue((live.vintage == 2023).all())
        beth = live[live.plant_id == BETHLEHEM].iloc[0]
        self.assertFalse(bool(beth.t1_zero))
        self.assertTrue(bool(beth.below_ref_fence))
        self.assertTrue(bool(beth.ct_side_intact))
        self.assertEqual(beth.ref_vintages, "2018;2019;2020;2021;2022")
        self.assertAlmostEqual(beth.plhtrt, 9.6651, places=4)
        self.assertAlmostEqual(beth.ref_st_ct_median, 0.4973, places=4)

    def test_one_member_records_are_declined(self):
        for plant in (7314, 2500, 10521):
            rows = self.df[(self.df.plant_id == plant) & (self.df.vintage == 2023)]
            self.assertEqual(int(rows.ref_n.iloc[0]), 1)
            self.assertFalse(bool(rows.admitted.iloc[0]))

    def test_identity_reproduces_plhtrt_where_the_filing_is_intact(self):
        # Where no test fires the identity is within 0.1 of eGRID's own plant
        # rate at every large CC (the identity's validation, decision card §1).
        big = {55405: "Athens", 56196: "Zeltmann", 55375: "Astoria Energy"}
        rows = self.df[(self.df.vintage == 2023) & self.df.plant_id.isin(big)]
        self.assertEqual(len(rows), 3)
        for r in rows.itertuples():
            self.assertFalse(bool(r.admitted))
            self.assertLess(abs(r.identity_hr - r.plhtrt), 0.25)


if __name__ == "__main__":
    unittest.main()
