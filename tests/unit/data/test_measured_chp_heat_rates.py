"""Tests for the measured power-only CHP heat-rate input (miso-99).

Covers the three seams the mechanism spans:

1. the derive's measurement (the credit add-back, the topping-cycle and
   physical-band gates, the basis check against the incumbent model rate),
2. the artifact loader (``flag == "ok"`` only, PAIR-keyed, absent-file no-op),
3. the fleet wiring — the swap reaches only the covered ``(plant, class)``
   pairs, exempts them from the legacy hand topping factor, and is a strict
   no-op while ``ScenarioConfig.measured_chp_heat_rates`` is off.

(3) carries the two defects this input exists to avoid: eGRID publishes ONE
rate per PLANT, so an override applied by plant code alone would reprice a
mixed facility's out-of-scope trains too; and a plant on its own measured rate
must never ALSO take the 1.8x hand factor (rule 19 [R-ONE-MECH]).
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from market_sim.config.constants import EGRID_CC_HR_PHYSICAL_CEILING
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.chp import (
    _correct_chp_steam_credit_hr,
    apply_measured_chp_heat_rates,
)
from market_sim.data.fleet import measured_chp_heat_rates
from scripts.data.derive_chp_power_only_heat_rates import (
    _MAX_THERMAL_SHARE,
    TARGET_CLASSES,
    plant_table,
)


def _egrid(rows: list[dict]) -> pd.DataFrame:
    """Return an eGRID-plant-sheet frame in :func:`plant_table`'s shape."""
    return pd.DataFrame(rows)


class TestDerive(unittest.TestCase):
    """The credit add-back, and the gates that keep it on topping cycles."""

    def _table(self, **kw) -> pd.DataFrame:
        caps = kw.pop("caps", {(1, "CC_CHP"): 500.0})
        model = kw.pop("model", {(1, "CC_CHP"): 6.0})
        # The basis gate reads the rate AT THE REPLACEMENT SEAM, not the shipped
        # rate (caiso-147). Outside CHP_STEAM_CREDIT_HR_CORRECTION_ISOS the two
        # are the same object, so defaulting basis to ``model`` keeps every
        # non-hand-factor case reading exactly as it did.
        basis = kw.pop("basis", model)
        egrid = kw.pop(
            "egrid",
            _egrid(
                [
                    {
                        "plant_code": 1,
                        "plant_name": "Topping Cogen",
                        # 6.0 credited, 25 % of the fuel on the thermal side,
                        # so the power-only rate is 6.0 / 0.75 = 8.0.
                        "heat_input_electric_mmbtu": 6_000_000.0,
                        "heat_input_thermal_mmbtu": 2_000_000.0,
                        "net_mwh": 1_000_000.0,
                        "egrid_heat_rate": 6.0,
                    }
                ]
            ),
        )
        return plant_table(
            "FAKEISO",
            2023,
            caps,
            model,
            basis,
            egrid,
            kw.pop("cems", {}),
            kw.pop("cems_dark", {}),
            **kw,
        )

    def test_credit_is_added_back_on_the_same_denominator(self) -> None:
        """``heat_rate`` is ``(PLHTIAN + CHPCHTI) / PLNGENAN`` — no g2n factor."""
        row = self._table().set_index(["plant_code", "plant_group"]).loc[(1, "CC_CHP")]
        self.assertAlmostEqual(float(row["heat_rate_credited"]), 6.0, places=4)
        self.assertAlmostEqual(float(row["heat_rate"]), 8.0, places=4)
        self.assertAlmostEqual(float(row["thermal_share"]), 0.25, places=6)
        self.assertEqual(row["flag"], "ok")

    def test_correction_only_ever_raises_the_rate(self) -> None:
        """A steam credit removed can only make the machine look less efficient."""
        row = self._table().set_index(["plant_code", "plant_group"]).loc[(1, "CC_CHP")]
        self.assertGreater(float(row["heat_rate"]), float(row["heat_rate_credited"]))
        self.assertLess(float(row["model_over_measured"]), 1.0)

    def test_no_credit_is_excluded_so_the_swap_is_a_strict_change(self) -> None:
        """A plant eGRID gives no credit has nothing to add back — not applied."""
        egrid = _egrid(
            [
                {
                    "plant_code": 1,
                    "plant_name": "No Credit",
                    "heat_input_electric_mmbtu": 6_000_000.0,
                    "heat_input_thermal_mmbtu": 0.0,
                    "net_mwh": 1_000_000.0,
                    "egrid_heat_rate": 6.0,
                }
            ]
        )
        row = (
            self._table(egrid=egrid)
            .set_index(["plant_code", "plant_group"])
            .loc[(1, "CC_CHP")]
        )
        self.assertEqual(row["flag"], "no_chp_credit")
        self.assertAlmostEqual(float(row["heat_rate"]), 6.0, places=4)

    def test_boiler_first_cogen_is_gated_out(self) -> None:
        """Past the unfired-topping envelope the fuel is process fuel, not power fuel."""
        egrid = _egrid(
            [
                {
                    "plant_code": 1,
                    "plant_name": "Back Pressure",
                    "heat_input_electric_mmbtu": 1_000_000.0,
                    "heat_input_thermal_mmbtu": 9_000_000.0,
                    "net_mwh": 1_000_000.0,
                    "egrid_heat_rate": 1.0,
                }
            ]
        )
        row = (
            self._table(egrid=egrid, model={(1, "CC_CHP"): 1.0})
            .set_index(["plant_code", "plant_group"])
            .loc[(1, "CC_CHP")]
        )
        self.assertGreater(float(row["thermal_share"]), _MAX_THERMAL_SHARE)
        self.assertEqual(row["flag"], "not_unfired_topping")

    def test_corrected_rate_past_the_physical_ceiling_is_flagged(self) -> None:
        """A CC cannot be less efficient than a bare simple-cycle GT."""
        egrid = _egrid(
            [
                {
                    "plant_code": 1,
                    "plant_name": "Boundary Defect",
                    "heat_input_electric_mmbtu": 9_000_000.0,
                    "heat_input_thermal_mmbtu": 4_000_000.0,
                    "net_mwh": 1_000_000.0,
                    "egrid_heat_rate": 9.0,
                }
            ]
        )
        row = (
            self._table(egrid=egrid, model={(1, "CC_CHP"): 9.0})
            .set_index(["plant_code", "plant_group"])
            .loc[(1, "CC_CHP")]
        )
        self.assertGreater(float(row["heat_rate"]), EGRID_CC_HR_PHYSICAL_CEILING)
        self.assertEqual(row["flag"], "above_physical_band")

    def test_incumbent_that_is_not_the_egrid_rate_is_not_swapped(self) -> None:
        """A bin fallback / boundary repair is not a clean single steam-credit delta."""
        row = (
            self._table(model={(1, "CC_CHP"): 11.5})
            .set_index(["plant_code", "plant_group"])
            .loc[(1, "CC_CHP")]
        )
        self.assertEqual(row["flag"], "basis_mismatch")

    def test_hand_factored_shipped_rate_is_gated_at_the_seam_not_the_ship(self) -> None:
        """A hand-corrected ISO's plants must not read as ``basis_mismatch``.

        In ``CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`` (CAISO, PJM) the shipped rate
        is eGRID's credited rate times an off-registry hand factor, so gating on
        it excluded precisely the population the mechanism exists to fix
        (caiso-147). The gate compares ``basis_heat_rate`` — after the eGRID join
        and boundary repairs, BEFORE the hand factor.
        """
        row = (
            # 6.0 credited, shipped at the x1.15 CC_CHP hand factor.
            self._table(model={(1, "CC_CHP"): 6.9}, basis={(1, "CC_CHP"): 6.0})
            .set_index(["plant_code", "plant_group"])
            .loc[(1, "CC_CHP")]
        )
        self.assertEqual(row["flag"], "ok")
        self.assertAlmostEqual(float(row["basis_heat_rate"]), 6.0, places=4)
        self.assertAlmostEqual(float(row["model_heat_rate"]), 6.9, places=4)

    def test_scope_is_topping_cycles_only(self) -> None:
        """``ST_CHP`` is out of scope — a boiler-first cogen's fuel is host fuel."""
        self.assertEqual(TARGET_CLASSES, ("CC_CHP", "CT_CHP"))

    def test_cems_validation_column_is_recorded(self) -> None:
        """The artifact carries its own independent check of eGRID's split."""
        row = (
            self._table(cems={1: 8_000_000.0})
            .set_index(["plant_code", "plant_group"])
            .loc[(1, "CC_CHP")]
        )
        self.assertAlmostEqual(float(row["cems_vs_egrid_total"]), 1.0, places=5)


class TestHybridCogenScopeGate(unittest.TestCase):
    """SCOPE gate 3 (miso-122) — direct-fired boiler fuel leaves the topping rate.

    The fixture is :class:`TestDerive`'s topping cogen: 6.0 credited, 25 % of
    the fuel on the thermal side, 8 000 000 MMBtu total, 1 000 000 net MWh, so
    the all-fuel rate is 8.0.
    """

    _table = TestDerive._table

    def _row(self, **kw):
        return (
            self._table(**kw)
            .set_index(["plant_code", "plant_group"])
            .loc[(1, "CC_CHP")]
        )

    def test_dark_fuel_is_removed_from_the_applied_rate(self) -> None:
        """A hybrid's boiler fuel is not charged to its power tranches."""
        row = self._row(cems={1: 8_000_000.0}, cems_dark={1: 1_600_000.0})
        self.assertAlmostEqual(float(row["dark_fuel_share"]), 0.20, places=6)
        self.assertAlmostEqual(float(row["heat_rate_all_fuel"]), 8.0, places=4)
        self.assertAlmostEqual(float(row["heat_rate"]), 6.4, places=4)
        self.assertEqual(row["flag"], "ok")

    def test_no_dark_fuel_is_byte_identical(self) -> None:
        """The gate is a strict no-op wherever the phenomenon is absent."""
        base = self._row(cems={1: 8_000_000.0})
        gated = self._row(cems={1: 8_000_000.0}, cems_dark={1: 0.0})
        self.assertAlmostEqual(float(base["heat_rate"]), 8.0, places=4)
        self.assertEqual(float(base["heat_rate"]), float(gated["heat_rate"]))
        self.assertEqual(float(base["dark_fuel_share"]), 0.0)

    def test_no_cems_coverage_leaves_the_rate_alone(self) -> None:
        """Uncovered plants keep the status quo — never a claim of zero dark fuel."""
        row = self._row()
        self.assertAlmostEqual(float(row["heat_rate"]), 8.0, places=4)
        self.assertTrue(pd.isna(row["dark_fuel_share"]))

    def test_unreconciled_meters_are_excluded_not_corrected(self) -> None:
        """CEMS that does not reproduce eGRID's total cannot be split by unit.

        The derive's own header records the failure mode: plants whose
        combustion units sit below the Part-75 threshold, where CEMS meters the
        boilers and misses the turbines. An unguarded share there runs toward
        1.0 and would drive the rate to zero.
        """
        row = self._row(cems={1: 2_000_000.0}, cems_dark={1: 1_000_000.0})
        self.assertAlmostEqual(float(row["cems_vs_egrid_total"]), 0.25, places=5)
        self.assertAlmostEqual(float(row["dark_fuel_share"]), 0.50, places=6)
        self.assertAlmostEqual(float(row["heat_rate"]), 8.0, places=4)
        self.assertEqual(row["flag"], "dark_unreconciled")

    def test_entirely_dark_plant_is_degenerate_and_not_corrected(self) -> None:
        """CEMS never saw the power train, so there is no power-train fuel."""
        row = self._row(cems={1: 8_000_000.0}, cems_dark={1: 8_000_000.0})
        self.assertAlmostEqual(float(row["heat_rate"]), 8.0, places=4)
        self.assertEqual(row["flag"], "dark_unreconciled")

    def test_correction_below_the_credited_rate_is_excluded(self) -> None:
        """Removing more fuel than eGRID's whole credit means the sources disagree.

        Measured on NYISO 2493 East River: a 37.5 % dark share against a 29.6 %
        eGRID thermal share, so the corrected rate would fall below the plant's
        own incumbent. Neither source can be preferred from this data, so the
        plant keeps the existing chain.
        """
        row = self._row(cems={1: 8_000_000.0}, cems_dark={1: 3_000_000.0})
        self.assertLess(float(row["heat_rate"]), float(row["heat_rate_credited"]))
        self.assertEqual(row["flag"], "below_credited")

    def test_the_gate_never_raises_the_rate(self) -> None:
        """It only ever removes fuel — it can never make a machine look worse."""
        for dark in (0.0, 0.05, 0.10, 0.20):
            row = self._row(cems={1: 8_000_000.0}, cems_dark={1: 8_000_000.0 * dark})
            self.assertLessEqual(float(row["heat_rate"]), 8.0)


class TestArtifactLoader(unittest.TestCase):
    """``measured_chp_heat_rates`` is PAIR-keyed, clean-rows-only, fails soft."""

    def test_absent_artifact_is_empty(self) -> None:
        measured_chp_heat_rates.cache_clear()
        self.assertEqual(measured_chp_heat_rates("NO_SUCH_ISO"), {})

    def test_flagged_rows_excluded_and_pair_keyed(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "chp_power_only_heat_rates_FAKEISO.csv"
            pd.DataFrame(
                [
                    {
                        "plant_code": 1,
                        "plant_group": "CC_CHP",
                        "heat_rate": 8.0,
                        "flag": "ok",
                    },
                    {
                        "plant_code": 1,
                        "plant_group": "CT_CHP",
                        "heat_rate": 9.5,
                        "flag": "ok",
                    },
                    {
                        "plant_code": 2,
                        "plant_group": "CC_CHP",
                        "heat_rate": 40.0,
                        "flag": "above_physical_band",
                    },
                    {
                        "plant_code": 3,
                        "plant_group": "CT_CHP",
                        "heat_rate": 7.0,
                        "flag": "not_unfired_topping",
                    },
                    {
                        "plant_code": 4,
                        "plant_group": "CC_CHP",
                        "heat_rate": 0.0,
                        "flag": "ok",
                    },
                ]
            ).to_csv(path, index=False)
            import market_sim.data.fleet.campd_bins as cb

            measured_chp_heat_rates.cache_clear()
            original = cb.PROCESSED_DIR
            try:
                cb.PROCESSED_DIR = Path(tmp)
                self.assertEqual(
                    measured_chp_heat_rates("FAKEISO"),
                    {(1, "CC_CHP"): 8.0, (1, "CT_CHP"): 9.5},
                )
            finally:
                cb.PROCESSED_DIR = original
                measured_chp_heat_rates.cache_clear()


class _Gen:
    """Minimal stand-in for :class:`Generator` in the application seam."""

    def __init__(self, plant_code: int, plant_group: str, heat_rate: float) -> None:
        self.plant_code = plant_code
        self.plant_group = plant_group
        self.heat_rate = heat_rate


class TestApplicationSeam(unittest.TestCase):
    """The swap is class-scoped and suppresses the legacy hand factor."""

    def _with_artifact(self, tmp: str) -> None:
        pd.DataFrame(
            [
                {
                    "plant_code": 7,
                    "plant_group": "CT_CHP",
                    "heat_rate": 10.5,
                    "flag": "ok",
                },
            ]
        ).to_csv(Path(tmp) / "chp_power_only_heat_rates_CAISO.csv", index=False)

    def test_only_covered_pairs_move_and_hand_factor_is_skipped(self) -> None:
        with TemporaryDirectory() as tmp:
            self._with_artifact(tmp)
            import market_sim.data.fleet.campd_bins as cb

            measured_chp_heat_rates.cache_clear()
            original = cb.PROCESSED_DIR
            try:
                cb.PROCESSED_DIR = Path(tmp)
                covered = _Gen(7, "CT_CHP", 5.5)
                sibling = _Gen(7, "ST_CHP", 5.5)
                uncovered = _Gen(8, "CT_CHP", 5.5)
                gens = [covered, sibling, uncovered]

                touched = apply_measured_chp_heat_rates(gens, "CAISO")
                self.assertEqual(covered.heat_rate, 10.5)
                self.assertEqual(sibling.heat_rate, 5.5)
                self.assertEqual(uncovered.heat_rate, 5.5)

                # CAISO is in CHP_STEAM_CREDIT_HR_CORRECTION_ISOS, so the hand
                # factor fires — on the uncovered plant only.
                _correct_chp_steam_credit_hr(gens, "CAISO", skip_ids=touched)
                self.assertEqual(covered.heat_rate, 10.5)
                self.assertAlmostEqual(uncovered.heat_rate, 5.5 * 1.8, places=6)
            finally:
                cb.PROCESSED_DIR = original
                measured_chp_heat_rates.cache_clear()

    def test_off_is_a_strict_no_op(self) -> None:
        """The default config never consults the artifact."""
        self.assertFalse(ScenarioConfig().measured_chp_heat_rates)

    def test_default_config_cache_key_is_unchanged(self) -> None:
        """Rule: the field is cache-key-optional at its default (armed differs)."""
        # F1: backcast-only; outside a backcast an armed flag is coerced off.
        base = ScenarioConfig().cache_key()
        self.assertEqual(
            base, ScenarioConfig(measured_chp_heat_rates=False).cache_key()
        )
        self.assertEqual(base, ScenarioConfig(measured_chp_heat_rates=True).cache_key())
        off = ScenarioConfig(mode="backcast", measured_chp_heat_rates=False)
        on = ScenarioConfig(mode="backcast", measured_chp_heat_rates=True)
        self.assertNotEqual(off.cache_key(), on.cache_key())


class TestRunnerForwarding(unittest.TestCase):
    """Every ``load_fleet_from_csv`` in the calibration runner forwards the flag.

    The nyiso-89 defect class: ``scripts/run_calibration.py::run_year`` inlines
    its own ``fleet_to_bins(load_fleet_from_csv(...))`` instead of calling
    ``fleet.assembly.load_or_synthesize_bins``, so a flag not forwarded there
    makes the solve silently inert while ``run_config.json`` records it as on.
    """

    def test_run_calibration_forwards_the_flag(self) -> None:
        import ast

        src = Path("scripts/run_calibration.py").read_text()
        tree = ast.parse(src)
        calls = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "load_fleet_from_csv"
        ]
        self.assertTrue(calls, "no load_fleet_from_csv call found to check")
        for call in calls:
            kws = {k.arg for k in call.keywords}
            self.assertIn(
                "measured_chp_heat_rates",
                kws,
                f"load_fleet_from_csv at line {call.lineno} does not forward "
                "measured_chp_heat_rates",
            )


if __name__ == "__main__":
    unittest.main()
