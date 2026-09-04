"""Tests for the eGRID prime-mover-family heat-rate input (nyiso-184).

Covers the four seams:

1. the family map (eGRID ``PRMVR`` / EIA-860 ``prime_mover`` codes -> ST / CC
   / GT; unclaimed codes -> ``None``),
2. the artifact reader (the committed NYISO artifact resolves Ravenswood's
   ST and CC families; only ``flag == "ok"`` rows; an ISO with no artifact is
   an empty no-op),
3. the frame-level apply — every row of a covered plant takes its own
   family's rate, nuclear and unclaimed rows are untouched, and the covered
   plant set is returned; a frame with no ``prime_mover`` column is returned
   unchanged,
4. the rule-19 hand-off — ``_correct_mixed_facility_steam_hr`` skips the
   plants the family construction covered and still lifts the rest — and the
   committed artifact's own invariants (Ravenswood covered on ST + CC, the
   applied vintage is the plant-grain join's, every applied rate inside the
   join's window).
"""

import unittest
from types import SimpleNamespace

import pandas as pd

from market_sim.data.fleet.eia860 import (
    _apply_egrid_family_heat_rates,
    _correct_mixed_facility_steam_hr,
    egrid_family_heat_rates_for,
)
from market_sim.data.fleet.models import (
    EGRID_PRIME_MOVER_FAMILIES,
    MIXED_FACILITY_STEAM_HR,
    egrid_prime_mover_family,
)

RAVENSWOOD = 2500


class TestFamilyMap(unittest.TestCase):
    def test_codes_resolve_to_their_family(self):
        self.assertEqual(egrid_prime_mover_family("ST"), "ST")
        for code in ("CT", "CA", "CS", "CC"):
            self.assertEqual(egrid_prime_mover_family(code), "CC")
        for code in ("GT", "IC"):
            self.assertEqual(egrid_prime_mover_family(code), "GT")
        self.assertEqual(egrid_prime_mover_family(" st "), "ST")

    def test_unclaimed_codes_are_none(self):
        for code in ("HY", "WT", "PV", "BA", "FC", "", None):
            self.assertIsNone(egrid_prime_mover_family(code))

    def test_families_are_disjoint(self):
        seen: set[str] = set()
        for codes in EGRID_PRIME_MOVER_FAMILIES.values():
            self.assertFalse(seen & codes)
            seen |= codes


class TestReader(unittest.TestCase):
    def test_nyiso_artifact_resolves_ravenswood_families(self):
        rates = egrid_family_heat_rates_for("NYISO")
        self.assertIn((RAVENSWOOD, "ST"), rates)
        self.assertIn((RAVENSWOOD, "CC"), rates)
        # The steam family sits well above the 8.80 plant blend and the 9.5
        # hand number; the CC family well below the blend.
        self.assertGreater(
            rates[(RAVENSWOOD, "ST")], MIXED_FACILITY_STEAM_HR[RAVENSWOOD]
        )
        self.assertLess(rates[(RAVENSWOOD, "CC")], 8.80)

    def test_only_ok_rows_are_applied(self):
        from market_sim.config.paths import PROCESSED_DIR

        df = pd.read_csv(PROCESSED_DIR / "egrid_family_heat_rates_NYISO.csv")
        flagged = df[df["flag"] != "ok"]
        rates = egrid_family_heat_rates_for("NYISO")
        for r in flagged.itertuples():
            self.assertNotIn((int(r.plant_id), str(r.family)), rates)

    def test_iso_without_artifact_is_empty(self):
        self.assertEqual(egrid_family_heat_rates_for("NEISO"), {})


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "plant_id": [RAVENSWOOD, RAVENSWOOD, RAVENSWOOD, RAVENSWOOD, 2516, 9999],
            "generator_id": ["1", "3", "4", "4S", "1", "N1"],
            "prime_mover": ["ST", "ST", "CT", "CA", "ST", "ST"],
            "energy_source": ["NG", "NG", "NG", "NG", "NG", "NUC"],
            "heat_rate": [8.8, 8.8, 8.8, 8.8, 10.887, 10.4],
        }
    )


class TestApply(unittest.TestCase):
    def test_each_row_takes_its_own_family_rate(self):
        rates = egrid_family_heat_rates_for("NYISO")
        out, covered = _apply_egrid_family_heat_rates(_frame(), "NYISO")
        self.assertEqual(covered, frozenset({RAVENSWOOD, 2516}))
        st, cc = rates[(RAVENSWOOD, "ST")], rates[(RAVENSWOOD, "CC")]
        self.assertAlmostEqual(out.loc[0, "heat_rate"], st)
        self.assertAlmostEqual(out.loc[1, "heat_rate"], st)
        self.assertAlmostEqual(out.loc[2, "heat_rate"], cc)
        self.assertAlmostEqual(out.loc[3, "heat_rate"], cc)
        # Northport's ST family is covered (its GT sibling is live in eGRID).
        self.assertAlmostEqual(out.loc[4, "heat_rate"], rates[(2516, "ST")])

    def test_nuclear_row_is_never_touched(self):
        out, _ = _apply_egrid_family_heat_rates(_frame(), "NYISO")
        self.assertEqual(out.loc[5, "heat_rate"], 10.4)

    def test_no_artifact_iso_is_noop(self):
        df = _frame()
        out, covered = _apply_egrid_family_heat_rates(df, "NEISO")
        self.assertEqual(covered, frozenset())
        pd.testing.assert_frame_equal(out, df)

    def test_frame_without_prime_mover_is_unchanged(self):
        df = _frame().drop(columns=["prime_mover"])
        out, covered = _apply_egrid_family_heat_rates(df, "NYISO")
        self.assertEqual(covered, frozenset())
        self.assertIs(out, df)


def _gen(plant_code: int, group: str, heat_rate: float) -> SimpleNamespace:
    return SimpleNamespace(
        plant_code=plant_code, plant_group=group, heat_rate=heat_rate
    )


class TestHandNumberHandOff(unittest.TestCase):
    """Rule 19: the hand number is superseded at covered plants, never stacked."""

    def test_skip_set_leaves_covered_plant_alone(self):
        gens = [_gen(RAVENSWOOD, "ST_GAS", 8.8), _gen(315, "ST_GAS", 8.49)]
        _correct_mixed_facility_steam_hr(gens, frozenset({RAVENSWOOD}))
        self.assertEqual(gens[0].heat_rate, 8.8)
        self.assertEqual(gens[1].heat_rate, MIXED_FACILITY_STEAM_HR[315])

    def test_default_behaviour_is_unchanged(self):
        gens = [_gen(RAVENSWOOD, "ST_GAS", 8.8), _gen(RAVENSWOOD, "CC_REGULAR", 8.8)]
        _correct_mixed_facility_steam_hr(gens)
        self.assertEqual(gens[0].heat_rate, MIXED_FACILITY_STEAM_HR[RAVENSWOOD])
        self.assertEqual(gens[1].heat_rate, 8.8)


class TestCommittedArtifact(unittest.TestCase):
    def test_invariants(self):
        from market_sim.config.paths import PROCESSED_DIR
        from scripts.data.derive_egrid_family_heat_rates import APPLIED_VINTAGE
        from scripts.data.process_eia860 import EGRID_HR_WINDOW_BTU_KWH

        df = pd.read_csv(PROCESSED_DIR / "egrid_family_heat_rates_NYISO.csv")
        self.assertTrue((df["vintage"] == APPLIED_VINTAGE).all())
        rav = df[df["plant_id"] == RAVENSWOOD]
        self.assertEqual(set(rav["family"]), {"ST", "CC", "GT"})
        self.assertTrue(
            (rav.loc[rav["family"].isin(["ST", "CC"]), "flag"] == "ok").all()
        )
        lo, hi = EGRID_HR_WINDOW_BTU_KWH
        ok = df[df["flag"] == "ok"]
        self.assertTrue(
            (
                (ok["heat_rate_mmbtu_mwh"] * 1000.0 >= lo)
                & (ok["heat_rate_mmbtu_mwh"] * 1000.0 <= hi)
            ).all()
        )
        # Every covered plant carries at least two live families.
        self.assertTrue((df.groupby("plant_id")["family"].nunique() >= 2).all())


if __name__ == "__main__":
    unittest.main()
