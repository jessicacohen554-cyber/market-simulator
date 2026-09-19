"""Tests for the measured COAL operating-heat-rate input (nwpp-42).

The coal sibling of ``tests/unit/data/test_measured_ct_heat_rates.py``, and it
covers the same three seams because the mechanism is the same mechanism on a
different class:

1. the derive's measurement (steady-state screen, minimum-hours screen,
   gross-to-net conversion, generation weighting, physical-band flagging),
2. the artifact loader (``flag == "ok"`` only, absent-file no-op), and
3. the fleet wiring — the override reaches only ``COAL`` rows, so a coal site's
   gas-converted boilers keep their eGRID plant average, and it is a strict
   no-op while ``ScenarioConfig.measured_coal_heat_rates`` is off.

(3) is the one that matters most here, and for a sharper reason than it has on
the CT side. eGRID publishes ONE heat rate per plant, and NWPP's three
converted coal sites (Jim Bridger, Naughton, North Valmy) carry coal boilers
and gas boilers under one plant code — so an override applied by plant code
alone would price the gas-converted units at the coal rate and trade one
attribution error for another.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import measured_coal_heat_rates
from market_sim.data.fleet.eia860 import _rows_to_generators
from scripts.data.derive_campd_coal_heat_rates import (
    _HR_MAX_NET,
    _HR_MIN_NET,
    TARGET_CLASS,
    _is_coal_fuel,
    plant_table,
)


def _unit_rows() -> pd.DataFrame:
    """Return a three-plant, four-unit per-unit table for :func:`plant_table`."""
    return pd.DataFrame(
        [
            # Plant 1: two boilers, different rates and very different energy.
            # The plant value must follow the big unit, not the average.
            {
                "plant_code": 1,
                "plant_name": "Two Unit Station",
                "unit_id": "1",
                "gross_mwh": 9_000_000.0,
                "steady_hours": 20_000,
                "cap_mw": 500.0,
                "hr_gross": 10.0,
                "hr_gross_hsl": 9.8,
            },
            {
                "plant_code": 1,
                "plant_name": "Two Unit Station",
                "unit_id": "2",
                "gross_mwh": 1_000_000.0,
                "steady_hours": 4_000,
                "cap_mw": 120.0,
                "hr_gross": 14.0,
                "hr_gross_hsl": 13.5,
            },
            # Plant 2: inside the band on a net basis.
            {
                "plant_code": 2,
                "plant_name": "Single Unit Station",
                "unit_id": "1",
                "gross_mwh": 3_000_000.0,
                "steady_hours": 9_000,
                "cap_mw": 300.0,
                "hr_gross": 11.0,
                "hr_gross_hsl": 10.7,
            },
            # Plant 3: a broken meter -- above the physical band even gross.
            {
                "plant_code": 3,
                "plant_name": "Broken Meter Station",
                "unit_id": "1",
                "gross_mwh": 100_000.0,
                "steady_hours": 1_000,
                "cap_mw": 50.0,
                "hr_gross": 26.5,
                "hr_gross_hsl": 26.0,
            },
        ]
    )


class TestDerive(unittest.TestCase):
    """The plant aggregate is generation-weighted, net-converted and flagged."""

    def _table(self) -> pd.DataFrame:
        return plant_table(
            _unit_rows(),
            "FAKEISO",
            [2023, 2024, 2025],
            caps={1: 620.0, 2: 300.0, 3: 50.0},
            model_hr={1: 12.5, 2: 12.0, 3: 30.0},
            factors={},
        ).set_index("plant_code")

    def test_generation_weighting_follows_the_big_unit(self) -> None:
        """Plant 1's rate sits near its 9 GWh unit, not the 2-unit mean."""
        table = self._table()
        gross = float(table.loc[1, "heat_rate_gross"])
        # 0.9 * 10.0 + 0.1 * 14.0 == 10.4; a plain mean would give 12.0.
        self.assertAlmostEqual(gross, 10.4, places=6)
        self.assertLess(gross, 12.0)

    def test_gross_to_net_conversion_is_applied(self) -> None:
        """``heat_rate`` is the gross rate divided by the parasitic factor."""
        table = self._table()
        factor = float(table.loc[1, "parasitic_factor"])
        self.assertAlmostEqual(factor, 0.93, places=6)  # 1 - the COAL default
        self.assertAlmostEqual(
            float(table.loc[1, "heat_rate"]),
            float(table.loc[1, "heat_rate_gross"]) / factor,
            places=3,
        )
        # The conversion raises the rate: comparing a gross measurement to the
        # model's net rate would overstate the correction by ~7 %.
        self.assertGreater(
            float(table.loc[1, "heat_rate"]), float(table.loc[1, "heat_rate_gross"])
        )

    def test_physical_band_flags_the_broken_meter(self) -> None:
        table = self._table()
        self.assertEqual(table.loc[1, "flag"], "ok")
        self.assertEqual(table.loc[2, "flag"], "ok")
        self.assertEqual(table.loc[3, "flag"], "above_physical_band")
        self.assertGreater(float(table.loc[3, "heat_rate"]), _HR_MAX_NET)
        self.assertLess(_HR_MIN_NET, float(table.loc[1, "heat_rate"]))

    def test_hsl_column_is_reported_not_applied(self) -> None:
        """The near-HSL rate is carried for the reader and never applied."""
        table = self._table()
        self.assertIn("heat_rate_gross_hsl", table.columns)
        self.assertLess(
            float(table.loc[2, "heat_rate_gross_hsl"]),
            float(table.loc[2, "heat_rate_gross"]),
        )
        self.assertNotAlmostEqual(
            float(table.loc[2, "heat_rate"]),
            float(table.loc[2, "heat_rate_gross_hsl"]),
            places=3,
        )

    def test_target_class_is_coal(self) -> None:
        self.assertEqual(TARGET_CLASS, "COAL")


class TestFuelTag(unittest.TestCase):
    """``primaryFuelInfo`` separates coal units from converted gas units.

    This is the tag choice the module docstring turns on: at Jim Bridger,
    Naughton and North Valmy the coal units and the gas-converted units are
    BOTH boilers, so CAMPD's ``unitType`` maps all of them to one family and
    cannot do the separation.
    """

    def test_coal_strings_match_and_gas_does_not(self) -> None:
        s = pd.Series(
            [
                "Coal",
                "Bituminous Coal",
                "Subbituminous",
                "Coal Refuse",
                "Lignite",
                "Pipeline Natural Gas",
                "Natural Gas",
                "Diesel Oil",
                "Residual Oil",
            ]
        )
        mask = _is_coal_fuel(s).tolist()
        self.assertEqual(mask[:5], [True] * 5)
        self.assertEqual(mask[5:], [False] * 4)


class TestArtifactLoader(unittest.TestCase):
    """``measured_coal_heat_rates`` applies only clean rows, and fails soft."""

    def test_absent_artifact_is_empty(self) -> None:
        measured_coal_heat_rates.cache_clear()
        self.assertEqual(measured_coal_heat_rates("NO_SUCH_ISO"), {})

    def test_flagged_rows_excluded(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "campd_coal_heat_rates_FAKEISO.csv"
            pd.DataFrame(
                [
                    {"plant_code": 1, "heat_rate": 10.5, "flag": "ok"},
                    {"plant_code": 2, "heat_rate": 40.0, "flag": "above_physical_band"},
                    {"plant_code": 3, "heat_rate": 0.0, "flag": "ok"},
                ]
            ).to_csv(path, index=False)
            import market_sim.data.fleet.campd_bins as cb

            measured_coal_heat_rates.cache_clear()
            original = cb.PROCESSED_DIR
            try:
                cb.PROCESSED_DIR = Path(tmp)
                self.assertEqual(measured_coal_heat_rates("FAKEISO"), {1: 10.5})
            finally:
                cb.PROCESSED_DIR = original
                measured_coal_heat_rates.cache_clear()


def _converted_site_frame() -> pd.DataFrame:
    """Return an EIA-860 frame for one plant spanning COAL and ST_GAS.

    Modelled on Jim Bridger (8066): coal boilers sharing a plant code — and
    therefore a single eGRID heat rate — with the units converted to gas.
    """
    common = {
        "plant_id": 8066,
        "plant_name": "Converted Site",
        "status": "OP",
        "state": "WY",
        "operating_year": 1974,
        "operating_month": 1,
        "heat_rate": 11.2457,
        "chp": "N",
        "prime_mover": "ST",
    }
    return pd.DataFrame(
        [
            {
                **common,
                "generator_id": "3",
                "energy_source": "SUB",
                "technology": "Conventional Steam Coal",
                "nameplate_capacity_mw": 530.0,
                "net_summer_capacity_mw": 530.0,
            },
            {
                **common,
                "generator_id": "1",
                "energy_source": "NG",
                "technology": "Natural Gas Steam Turbine",
                "nameplate_capacity_mw": 535.0,
                "net_summer_capacity_mw": 535.0,
            },
        ]
    )


class TestFleetSeam(unittest.TestCase):
    """The override is class-scoped and default-off."""

    def _load(self, flag: bool) -> dict[str, tuple[str, float]]:
        gens = _rows_to_generators(
            _converted_site_frame(),
            "NWPP",
            None,
            measured_coal_heat_rates=flag,
        )
        return {g.unit_id: (g.plant_group, g.heat_rate) for g in gens}

    def test_default_off_is_a_no_op(self) -> None:
        """Both units keep the eGRID plant average while the flag is off."""
        self.assertFalse(ScenarioConfig().measured_coal_heat_rates)
        loaded = self._load(False)
        self.assertTrue(loaded)
        for _group, hr in loaded.values():
            self.assertAlmostEqual(hr, 11.2457, places=3)

    def test_only_the_coal_units_are_repriced(self) -> None:
        """The measured rate reaches COAL; the converted gas boiler is untouched."""
        measured = measured_coal_heat_rates("NWPP")
        if 8066 not in measured:
            self.skipTest("NWPP coal heat-rate artifact not built in this tree")
        loaded = self._load(True)
        coal_group, coal_hr = loaded["8066_3"]
        gas_group, gas_hr = loaded["8066_1"]
        self.assertEqual(coal_group, "COAL")
        self.assertEqual(gas_group, "ST_GAS")
        self.assertAlmostEqual(coal_hr, measured[8066], places=3)
        self.assertAlmostEqual(gas_hr, 11.2457, places=3)


class TestCacheKeyRegistration(unittest.TestCase):
    """Default-off must be byte-identical off, armed must re-key."""

    def test_default_key_is_unmoved_and_armed_key_differs(self) -> None:
        base = ScenarioConfig(iso="NWPP")
        armed = base.with_overrides(measured_coal_heat_rates=True)
        self.assertNotEqual(base.cache_key(), armed.cache_key())
        # Registered at its frozen default, so an explicitly-False config keys
        # identically to one that never named the field (no cache orphaning).
        self.assertEqual(
            base.cache_key(),
            base.with_overrides(measured_coal_heat_rates=False).cache_key(),
        )


class TestConfigPlumbing(unittest.TestCase):
    """``ScenarioConfig.measured_coal_heat_rates`` must reach the fleet loader.

    The flag is useless if it stops at the config object: the fleet is loaded
    from three places in ``fleet.assembly`` (the bin synthesis and both
    branches of the base-fleet build), and a call site that forgets to forward
    it silently solves on eGRID rates while ``run_config.json`` claims the
    measured input was on. That failure is invisible in the LP output, so it is
    asserted here rather than left to a diff review (rule 24 [R-REGISTRY]).
    """

    def test_synthesis_forwards_the_flag(self) -> None:
        from unittest import mock

        import market_sim.data.fleet as fleet_pkg
        from market_sim.data.fleet.assembly import load_or_synthesize_bins

        config = ScenarioConfig().with_overrides(
            iso="NYISO", measured_coal_heat_rates=True, use_campd_bins=True
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
        self.assertIs(seen.get("measured_coal_heat_rates"), True)

    def test_base_fleet_branches_forward_the_flag(self) -> None:
        from unittest import mock

        import market_sim.data.fleet as fleet_pkg
        from market_sim.data.fleet.assembly import build_base_fleet

        config = ScenarioConfig().with_overrides(
            iso="NYISO", measured_coal_heat_rates=True
        )
        calls: list[dict] = []

        def _spy(iso, iso_config=None, **kwargs):
            calls.append(kwargs)
            return []

        with mock.patch.object(fleet_pkg, "load_fleet_from_csv", _spy):
            with mock.patch.object(fleet_pkg, "aggregate_fleet", lambda *a, **k: []):
                # Legacy aggregate branch (campd_bins is None) -- the branch
                # NWPP itself takes, since it is absent from CAMPD_BINNING_ISOS.
                build_base_fleet(None, "NYISO", None, ["z"], config, [], [], 2023)
            with mock.patch.object(
                fleet_pkg, "bins_to_fleet", lambda *a, **k: ([], None)
            ):
                bins = pd.DataFrame({"Plant_Code": [1], "Plant_Group": ["COAL"]})
                build_base_fleet(bins, "NYISO", None, ["z"], config, [], [], 2023)

        self.assertEqual(len(calls), 2)
        for kwargs in calls:
            self.assertIs(kwargs.get("measured_coal_heat_rates"), True)


class TestBackcastFleetSourcing(unittest.TestCase):
    """The BACKCAST solve path has its own copy of the bin synthesis.

    ``scripts/run_calibration.py::run_year`` does not call
    ``fleet.assembly.load_or_synthesize_bins`` — it inlines an equivalent
    ``fleet_to_bins(load_fleet_from_csv(...))``. A fleet-sourcing flag
    forwarded in ``assembly`` but not there is silently ignored by every
    calibration solve while ``run_config.json`` still records it as on: the arm
    comes back byte-identical to its control and reads as "the mechanism is
    inert" rather than "the mechanism was never applied". That is what happened
    on the first nyiso-89 arm, so the call site is pinned by source inspection
    here — a solve is far too expensive to use as the regression test.
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
                "measured_coal_heat_rates",
                kwargs,
                "run_calibration.py:%d loads the fleet without forwarding "
                "measured_coal_heat_rates — the backcast would silently solve "
                "on eGRID heat rates" % call.lineno,
            )


if __name__ == "__main__":
    unittest.main()
