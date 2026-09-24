"""Tests for the measured CT_PEAKER loaded-heat-rate input (nyiso-89).

Covers the three seams the mechanism spans:

1. the derive's measurement (loaded window, minimum-hours screen, gross-to-net
   conversion, generation weighting, physical-band flagging),
2. the artifact loader (``flag == "ok"`` only, absent-file no-op), and
3. the fleet wiring — the override reaches only CT_PEAKER rows, so a mixed
   steam/CT facility's boilers keep their eGRID plant average, and it is a
   strict no-op while ``ScenarioConfig.measured_ct_heat_rates`` is off.

(3) is the one that matters most: the whole point of the input is that eGRID
publishes ONE heat rate per plant, so an override applied by plant code alone
would reprice a mixed plant's steam units with its turbines' rate and trade one
attribution error for another.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import campd
from market_sim.data.fleet import measured_ct_heat_rates
from market_sim.data.fleet.eia860 import _rows_to_generators
from scripts.data.derive_campd_ct_heat_rates import (
    _HR_MAX,
    _HR_MIN,
    TARGET_CLASS,
    plant_table,
)


def _unit_rows() -> pd.DataFrame:
    """Return a two-plant, three-unit per-unit table for :func:`plant_table`."""
    return pd.DataFrame(
        [
            # Plant 1: two turbines, different rates and very different energy.
            # The generation weighting must follow the 9,000 MWh unit.
            {
                "plant_code": 1,
                "plant_name": "Mixed Facility",
                "unit_id": "GT1",
                "gross_mwh": 9000.0,
                "loaded_hours": 500,
                "cap_mw": 100.0,
                "hr_gross": 10.0,
            },
            {
                "plant_code": 1,
                "plant_name": "Mixed Facility",
                "unit_id": "GT2",
                "gross_mwh": 1000.0,
                "loaded_hours": 200,
                "cap_mw": 100.0,
                "hr_gross": 20.0,
            },
            # Plant 2: a single unit whose measured rate is non-physical.
            {
                "plant_code": 2,
                "plant_name": "Broken Meter",
                "unit_id": "GT1",
                "gross_mwh": 5000.0,
                "loaded_hours": 300,
                "cap_mw": 50.0,
                "hr_gross": 40.0,
            },
        ]
    )


class TestPlantTable(unittest.TestCase):
    """The derive's aggregation: net basis, generation weighting, flagging."""

    def _table(self, factors: dict[int, float] | None = None) -> pd.DataFrame:
        return plant_table(
            _unit_rows(),
            "TESTISO",
            [2023, 2024, 2025],
            caps={1: 200.0, 2: 50.0},
            model_hr={1: 11.0, 2: 12.0},
            factors=factors or {},
        )

    def test_generation_weighted_not_unit_averaged(self) -> None:
        """The 9:1 energy split must dominate the plant rate, not a 15.0 mean."""
        row = self._table().set_index("plant_code").loc[1]
        # (9000*10 + 1000*20) / 10000 = 11.0 gross, /0.99 default -> 11.111.
        self.assertAlmostEqual(float(row["heat_rate_gross"]), 11.0, places=3)

    def test_gross_to_net_uses_committed_factor(self) -> None:
        """A measured parasitic factor must scale the rate up to a net basis."""
        default = 1.0 - campd.DEFAULT_PARASITIC_LOAD_PCT[TARGET_CLASS]
        bare = self._table().set_index("plant_code").loc[1]
        self.assertAlmostEqual(float(bare["heat_rate"]), 11.0 / default, places=3)
        self.assertAlmostEqual(float(bare["parasitic_factor"]), default, places=6)

        # A plant with a large measured station-service load (Bayonne's 10.2 %)
        # gets a materially higher NET heat rate than its gross meter reads.
        heavy = self._table(factors={1: 0.9}).set_index("plant_code").loc[1]
        self.assertAlmostEqual(float(heavy["heat_rate"]), 11.0 / 0.9, places=3)
        self.assertGreater(float(heavy["heat_rate"]), float(bare["heat_rate"]))

    def test_model_ratio_recorded(self) -> None:
        """The table records what it replaces, for provenance."""
        row = self._table().set_index("plant_code").loc[1]
        self.assertAlmostEqual(
            float(row["model_over_measured"]),
            11.0 / float(row["heat_rate"]),
            places=3,
        )
        self.assertAlmostEqual(float(row["model_heat_rate_egrid"]), 11.0, places=3)

    def test_non_physical_rate_is_flagged_not_applied(self) -> None:
        """A rate outside the simple-cycle band is a meter defect, not an input."""
        table = self._table().set_index("plant_code")
        self.assertEqual(table.loc[1, "flag"], "ok")
        self.assertEqual(table.loc[2, "flag"], "above_physical_band")
        self.assertGreater(float(table.loc[2, "heat_rate"]), _HR_MAX)
        self.assertLess(_HR_MIN, float(table.loc[1, "heat_rate"]))


class TestArtifactLoader(unittest.TestCase):
    """``measured_ct_heat_rates`` applies only clean rows, and fails soft."""

    def test_absent_artifact_is_empty(self) -> None:
        measured_ct_heat_rates.cache_clear()
        self.assertEqual(measured_ct_heat_rates("NO_SUCH_ISO"), {})

    def test_flagged_rows_excluded(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "campd_ct_heat_rates_FAKEISO.csv"
            pd.DataFrame(
                [
                    {"plant_code": 1, "heat_rate": 9.5, "flag": "ok"},
                    {"plant_code": 2, "heat_rate": 40.0, "flag": "above_physical_band"},
                    {"plant_code": 3, "heat_rate": 0.0, "flag": "ok"},
                ]
            ).to_csv(path, index=False)
            import market_sim.data.fleet.campd_bins as cb

            measured_ct_heat_rates.cache_clear()
            original = cb.PROCESSED_DIR
            try:
                cb.PROCESSED_DIR = Path(tmp)
                self.assertEqual(measured_ct_heat_rates("FAKEISO"), {1: 9.5})
            finally:
                cb.PROCESSED_DIR = original
                measured_ct_heat_rates.cache_clear()


def _mixed_plant_frame() -> pd.DataFrame:
    """Return an EIA-860 frame for one plant spanning CT_PEAKER and ST_GAS.

    Modelled on E F Barrett (2511): FT4 peaking turbines sharing a plant code —
    and therefore a single eGRID heat rate — with 188 MW steam boilers.
    """
    common = {
        "plant_id": 2511,
        "plant_name": "Mixed Facility",
        "status": "OP",
        "energy_source": "NG",
        "state": "NY",
        "operating_year": 1971,
        "operating_month": 1,
        "heat_rate": 11.076,
        "chp": "N",
    }
    return pd.DataFrame(
        [
            {
                **common,
                "generator_id": "GT1",
                "prime_mover": "GT",
                "technology": "Natural Gas Fired Combustion Turbine",
                "nameplate_capacity_mw": 140.0,
                "net_summer_capacity_mw": 140.0,
            },
            {
                **common,
                "generator_id": "ST1",
                "prime_mover": "ST",
                "technology": "Natural Gas Steam Turbine",
                "nameplate_capacity_mw": 188.0,
                "net_summer_capacity_mw": 188.0,
            },
        ]
    )


class TestFleetSeam(unittest.TestCase):
    """The override is class-scoped and default-off."""

    def _load(self, flag: bool) -> dict[str, tuple[str, float]]:
        gens = _rows_to_generators(
            _mixed_plant_frame(),
            "NYISO",
            None,
            measured_ct_heat_rates=flag,
        )
        return {g.unit_id: (g.plant_group, g.heat_rate) for g in gens}

    def test_default_off_is_a_no_op(self) -> None:
        """Both units keep the eGRID plant average while the flag is off."""
        self.assertFalse(ScenarioConfig().measured_ct_heat_rates)
        loaded = self._load(False)
        for group, hr in loaded.values():
            self.assertAlmostEqual(hr, 11.076, places=3)

    def test_only_the_turbines_are_repriced(self) -> None:
        """The measured rate reaches CT_PEAKER; the steam boiler is untouched."""
        measured = measured_ct_heat_rates("NYISO")
        if 2511 not in measured:
            self.skipTest("NYISO CT heat-rate artifact not built in this tree")
        loaded = self._load(True)
        groups = {g: (grp, hr) for g, (grp, hr) in loaded.items()}
        ct_group, ct_hr = groups["2511_GT1"]
        st_group, st_hr = groups["2511_ST1"]
        self.assertEqual(ct_group, "CT_PEAKER")
        self.assertEqual(st_group, "ST_GAS")
        self.assertAlmostEqual(ct_hr, measured[2511], places=3)
        self.assertAlmostEqual(st_hr, 11.076, places=3)
        self.assertNotAlmostEqual(ct_hr, st_hr, places=2)


if __name__ == "__main__":
    unittest.main()


class TestConfigPlumbing(unittest.TestCase):
    """``ScenarioConfig.measured_ct_heat_rates`` must reach the fleet loader.

    The flag is useless if it stops at the config object: the fleet is loaded
    from three places in ``fleet.assembly`` (the bin synthesis and both
    branches of the base-fleet build), and a call site that forgets to forward
    it silently solves on eGRID rates while ``run_config.json`` claims the
    measured input was on. That failure is invisible in the LP output, so it is
    asserted here rather than left to a diff review (rule 26 [R-REGISTRY]).
    """

    def test_synthesis_forwards_the_flag(self) -> None:
        from unittest import mock

        import market_sim.data.fleet as fleet_pkg
        from market_sim.data.fleet.assembly import load_or_synthesize_bins

        # F1: the flags are backcast-only (coerced off in a forecast config).
        config = ScenarioConfig(mode="backcast").with_overrides(
            iso="NYISO", measured_ct_heat_rates=True, use_campd_bins=True
        )
        seen: dict = {}

        def _spy(iso, iso_config=None, **kwargs):
            seen.update(kwargs)
            return []

        with mock.patch.object(fleet_pkg, "load_fleet_from_csv", _spy):
            with mock.patch.object(
                fleet_pkg, "fleet_to_bins", lambda *a, **k: pd.DataFrame()
            ):
                load_or_synthesize_bins(config, "NYISO", None, [])
        self.assertIs(seen.get("measured_ct_heat_rates"), True)

    def test_base_fleet_branches_forward_the_flag(self) -> None:
        from unittest import mock

        import market_sim.data.fleet as fleet_pkg
        from market_sim.data.fleet.assembly import build_base_fleet

        # F1: the flags are backcast-only (coerced off in a forecast config).
        config = ScenarioConfig(mode="backcast").with_overrides(
            iso="NYISO", measured_ct_heat_rates=True
        )
        calls: list[dict] = []

        def _spy(iso, iso_config=None, **kwargs):
            calls.append(kwargs)
            return []

        with mock.patch.object(fleet_pkg, "load_fleet_from_csv", _spy):
            with mock.patch.object(fleet_pkg, "aggregate_fleet", lambda *a, **k: []):
                # Legacy aggregate branch (campd_bins is None).
                build_base_fleet(None, "NYISO", None, ["z"], config, [], [], 2023)
            with mock.patch.object(
                fleet_pkg, "bins_to_fleet", lambda *a, **k: ([], None)
            ):
                bins = pd.DataFrame({"Plant_Code": [1], "Plant_Group": ["CT_PEAKER"]})
                build_base_fleet(bins, "NYISO", None, ["z"], config, [], [], 2023)

        self.assertEqual(len(calls), 2)
        for kwargs in calls:
            self.assertIs(kwargs.get("measured_ct_heat_rates"), True)


class TestBackcastFleetSourcing(unittest.TestCase):
    """The BACKCAST solve path has its own copy of the bin synthesis.

    ``scripts/run_calibration.py::run_year`` does not call
    ``fleet.assembly.load_or_synthesize_bins`` — it inlines an equivalent
    ``fleet_to_bins(load_fleet_from_csv(...))`` for the non-ERCOT per-plant
    ISOs. A fleet-sourcing flag forwarded in ``assembly`` but not there is
    silently ignored by every calibration solve while ``run_config.json``
    still records it as on: the arm comes back byte-identical to its control
    and reads as "the mechanism is inert" rather than "the mechanism was never
    applied". That is what happened on the first nyiso-89 arm, so the call
    site is pinned by source inspection here — a solve is far too expensive to
    use as the regression test.
    """

    def test_backcast_synthesis_forwards_fleet_flags(self) -> None:
        import ast

        source = Path("scripts/run_calibration.py").read_text()
        tree = ast.parse(source)
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "load_fleet_from_csv"
        ]
        self.assertTrue(calls, "run_calibration.py no longer loads the fleet")
        for call in calls:
            kwargs = {kw.arg for kw in call.keywords}
            self.assertIn(
                "measured_ct_heat_rates",
                kwargs,
                "run_calibration.py:%d loads the fleet without forwarding "
                "measured_ct_heat_rates — the backcast would silently solve "
                "on eGRID heat rates" % call.lineno,
            )
