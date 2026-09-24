"""Tests for the measured ST_GAS operating-heat-rate input (soco-53e).

The gas-steam sibling of ``tests/unit/data/test_measured_coal_heat_rates.py``,
covering the same seams because the mechanism is the same mechanism on a third
class:

1. the derive's measurement (steady-state screen, gross-to-net conversion,
   generation weighting, physical-band flagging),
2. the MEMBERSHIP rule, which is where this deriver differs from both its
   siblings and is the one thing that can put an applied number on the wrong
   rows,
3. the artifact loader (``flag == "ok"`` only, absent-file no-op), and
4. the fleet wiring — the override reaches only ``ST_GAS`` rows, so a mixed
   steam station's coal boiler keeps the rate its own class assigns, and it is
   a strict no-op while ``ScenarioConfig.measured_st_heat_rates`` is off.

(2) is the sharp one. The coal sibling separates a mixed site by CAMPD
``primaryFuelInfo``, and that tag CANNOT do the job here: at SOCO's Barry
(plant 3) CAMPD files unit 4 — a 330 MW boiler — as *Pipeline Natural Gas*
while the model carries it as a 362 MW ``COAL`` row, so a fuel-tag selection
would price the model's two 80 MW ``ST_GAS`` rows off a boiler the model
dispatches as coal. ``unitType`` cannot do it either, since both machines are
boilers. The deriver therefore pairs each plant's CAMPD boiler units to that
plant's own model boiler rows by descending capacity and keeps only the units
whose partner is ``ST_GAS``.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import measured_st_heat_rates
from market_sim.data.fleet.eia860 import _rows_to_generators
from scripts.data.derive_campd_gas_st_heat_rates import (
    _HR_MAX_NET,
    _HR_MIN_NET,
    _PAIR_RATIO_MAX,
    BOILER_CLASSES,
    TARGET_CLASS,
    _is_boiler,
    pair_units_to_rows,
    plant_table,
)

#: The SOCO artifact this lane derived, pinned so a future re-derive that moves
#: a number has to say so (rule 23 [R-FROZEN-DERIVE]).
SOCO_MEASURED = {
    26: 11.0744,
    # F1 (2026-09-24): the pooled window widened 2023-2025 -> 2019-2025; only
    # 2049 carries pre-2023 steady hours, so only it moves (10.3596 -> 10.3494).
    2049: 10.3494,
    728: 10.7966,
    10: 10.2073,
    3: 13.9845,
}


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
                "pair_ratio": 1.02,
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
                "pair_ratio": 0.98,
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
                "pair_ratio": 1.00,
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
                "pair_ratio": 1.00,
                "hr_gross": 26.5,
                "hr_gross_hsl": 26.0,
            },
            # Plant 4: a sound meter behind a STRUCTURALLY WRONG pairing -- a
            # 330 MW boiler matched to an 80 MW model row (the Barry unit-4
            # shape). The rate is plausible; the attribution is not.
            {
                "plant_code": 4,
                "plant_name": "Mispaired Station",
                "unit_id": "4",
                "gross_mwh": 1_000_000.0,
                "steady_hours": 9_000,
                "cap_mw": 330.0,
                "pair_ratio": 4.125,
                "hr_gross": 10.5,
                "hr_gross_hsl": 10.2,
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
            caps={1: 620.0, 2: 300.0, 3: 50.0, 4: 80.0},
            model_hr={1: 12.5, 2: 12.0, 3: 30.0, 4: 11.0},
            factors={},
        ).set_index("plant_code")

    def test_generation_weighting_follows_the_big_unit(self) -> None:
        """Plant 1's rate sits near its 9 GWh unit, not the 2-unit mean."""
        table = self._table()
        gross = float(table.loc[1, "heat_rate_gross"])
        # 0.9 * 10.0 + 0.1 * 14.0 == 10.4; a plain mean would give 12.0.
        self.assertAlmostEqual(gross, 10.4, places=6)
        self.assertLess(gross, 12.0)

    def test_gross_to_net_uses_the_ST_GAS_class_default(self) -> None:
        """The factor is 0.95, not the CT class's 0.99.

        The basis error this pins is not hypothetical: the predecessor lane's
        scoping measurement converted SOCO's BOILERS at the CT_PEAKER factor
        0.99 and so understated every rate by 4.2 %, which is most of the
        headline it reported. SOCO's own metered net/gross over its
        unambiguous plant-years is 0.938-0.943 (EIA-923 ST/NG net over CAMPD
        gas-boiler gross), which 0.95 reproduces to 1.2 % and 0.99 does not.
        """
        table = self._table()
        factor = float(table.loc[1, "parasitic_factor"])
        self.assertAlmostEqual(factor, 0.95, places=6)  # 1 - the ST_GAS default
        self.assertAlmostEqual(
            float(table.loc[1, "heat_rate"]),
            float(table.loc[1, "heat_rate_gross"]) / factor,
            places=3,
        )
        # The conversion raises the rate: comparing a gross measurement to the
        # model's net rate would understate it by the station-service fraction.
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

    def test_pairing_band_flags_a_structurally_wrong_match(self) -> None:
        """A sound meter on the wrong row is refused, not applied."""
        table = self._table()
        self.assertEqual(table.loc[4, "flag"], "capacity_pairing_mismatch")
        self.assertGreater(float(table.loc[4, "pair_ratio_max"]), _PAIR_RATIO_MAX)
        # ...and the loader then leaves that plant on its eGRID rate.
        self.assertLess(_HR_MIN_NET, float(table.loc[4, "heat_rate"]))

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

    def test_target_and_pairing_classes(self) -> None:
        self.assertEqual(TARGET_CLASS, "ST_GAS")
        # The pairing must be offered BOTH boiler classes, or a coal boiler
        # with no coal row to pair against falls through onto a gas row.
        self.assertEqual(set(BOILER_CLASSES), {"COAL", "ST_GAS"})


class TestBoilerTag(unittest.TestCase):
    """``unitType`` separates boilers from turbines and combined-cycle blocks."""

    def test_boiler_strings_match_and_turbines_do_not(self) -> None:
        s = pd.Series(
            [
                "Tangentially-fired",
                "Dry bottom wall-fired boiler",
                "Cell burner boiler",
                "Cyclone boiler",
                "Stoker",
                "Combustion turbine",
                "Combined cycle",
                "Combined cycle (Started Jul 17, 2023)",
            ]
        )
        mask = _is_boiler(s).tolist()
        self.assertEqual(mask[:5], [True] * 5)
        self.assertEqual(mask[5:], [False] * 3)


class TestPairing(unittest.TestCase):
    """Membership is decided by the model's own class assignment.

    The Barry shape, reduced: one coal boiler, one gas-FUELLED boiler the model
    carries as COAL, and two small gas boilers the model carries as ST_GAS.
    """

    def _fixture(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        hours = pd.DataFrame(
            [
                {
                    "facilityId": 3,
                    "facilityName": "Barry",
                    "unitId": u,
                    "grossLoad": mw,
                    "heatInput": mw * 11.0,
                    "opTime": 1.0,
                    "primaryFuelInfo": fuel,
                    "unitType": "Tangentially-fired",
                }
                for u, mw, fuel in (
                    ("5", 699.0, "Coal"),
                    ("4", 330.0, "Pipeline Natural Gas"),
                    ("1", 60.0, "Pipeline Natural Gas"),
                    ("2", 60.0, "Pipeline Natural Gas"),
                )
            ]
        )
        boilers = pd.DataFrame(
            [
                {
                    "plant_code": 3,
                    "unit_id": "3_5",
                    "generator_id": "5",
                    "plant_group": "COAL",
                    "pmax_mw": 756.5,
                    "heat_rate": 12.61,
                },
                {
                    "plant_code": 3,
                    "unit_id": "3_4",
                    "generator_id": "4",
                    "plant_group": "COAL",
                    "pmax_mw": 362.0,
                    "heat_rate": 12.61,
                },
                {
                    "plant_code": 3,
                    "unit_id": "3_1",
                    "generator_id": "1",
                    "plant_group": "ST_GAS",
                    "pmax_mw": 80.0,
                    "heat_rate": 12.61,
                },
                {
                    "plant_code": 3,
                    "unit_id": "3_2",
                    "generator_id": "2",
                    "plant_group": "ST_GAS",
                    "pmax_mw": 80.0,
                    "heat_rate": 12.61,
                },
            ]
        )
        return hours, boilers

    def test_a_gas_fuelled_boiler_the_model_calls_coal_is_excluded(self) -> None:
        hours, boilers = self._fixture()
        pairs = pair_units_to_rows(hours, boilers)
        kept = set(pairs[pairs.model_group == TARGET_CLASS].unit_id)
        self.assertEqual(kept, {"1", "2"})
        # The decisive one: CAMPD calls unit 4 natural gas, and it is still out.
        row = pairs[pairs.unit_id == "4"].iloc[0]
        self.assertEqual(row.campd_fuel, "Pipeline Natural Gas")
        self.assertEqual(row.model_group, "COAL")

    def test_the_pairing_rule_does_not_change_membership(self) -> None:
        """Exact-generator-id-first selects the same gas-steam population."""
        hours, boilers = self._fixture()
        a = pair_units_to_rows(hours, boilers)
        b = pair_units_to_rows(hours, boilers, exact_id_first=True)
        self.assertEqual(
            set(a[a.model_group == TARGET_CLASS].unit_id),
            set(b[b.model_group == TARGET_CLASS].unit_id),
        )


class TestArtifactLoader(unittest.TestCase):
    """``measured_st_heat_rates`` applies only clean rows, and fails soft."""

    def test_absent_artifact_is_empty(self) -> None:
        measured_st_heat_rates.cache_clear()
        self.assertEqual(measured_st_heat_rates("NO_SUCH_ISO"), {})

    def test_flagged_rows_excluded(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "campd_st_heat_rates_FAKEISO.csv"
            pd.DataFrame(
                [
                    {"plant_code": 1, "heat_rate": 10.5, "flag": "ok"},
                    {"plant_code": 2, "heat_rate": 40.0, "flag": "above_physical_band"},
                    {
                        "plant_code": 4,
                        "heat_rate": 11.0,
                        "flag": "capacity_pairing_mismatch",
                    },
                    {"plant_code": 3, "heat_rate": 0.0, "flag": "ok"},
                ]
            ).to_csv(path, index=False)
            import market_sim.data.fleet.campd_bins as cb

            measured_st_heat_rates.cache_clear()
            original = cb.PROCESSED_DIR
            try:
                cb.PROCESSED_DIR = Path(tmp)
                self.assertEqual(measured_st_heat_rates("FAKEISO"), {1: 10.5})
            finally:
                cb.PROCESSED_DIR = original
                measured_st_heat_rates.cache_clear()

    def test_committed_soco_values(self) -> None:
        """The committed artifact carries exactly the PRECOMMIT's numbers."""
        measured_st_heat_rates.cache_clear()
        loaded = measured_st_heat_rates("SOCO")
        if not loaded:
            self.skipTest("SOCO gas-steam heat-rate artifact not built in this tree")
        self.assertEqual(set(loaded), set(SOCO_MEASURED))
        for code, expected in SOCO_MEASURED.items():
            self.assertAlmostEqual(loaded[code], expected, places=4)


def _mixed_steam_frame() -> pd.DataFrame:
    """Return an EIA-860 frame for one plant spanning COAL and ST_GAS.

    Modelled on E C Gaston (26): a coal boiler sharing a plant code — and
    therefore a single eGRID rate, AND a single eGRID prime-mover-FAMILY rate,
    since both machines are prime mover ``ST`` — with four gas boilers.
    """
    common = {
        "plant_id": 26,
        "plant_name": "Mixed Steam Station",
        "status": "OP",
        "state": "AL",
        "operating_year": 1960,
        "operating_month": 1,
        "heat_rate": 11.5505,
        "chp": "N",
        "prime_mover": "ST",
    }
    return pd.DataFrame(
        [
            {
                **common,
                "generator_id": "5",
                "energy_source": "BIT",
                "technology": "Conventional Steam Coal",
                "nameplate_capacity_mw": 880.0,
                "net_summer_capacity_mw": 832.0,
            },
            {
                **common,
                "generator_id": "1",
                "energy_source": "NG",
                "technology": "Natural Gas Steam Turbine",
                "nameplate_capacity_mw": 270.0,
                "net_summer_capacity_mw": 254.0,
            },
        ]
    )


class TestFleetSeam(unittest.TestCase):
    """The override is class-scoped and default-off."""

    def _load(self, flag: bool) -> dict[str, tuple[str, float]]:
        gens = _rows_to_generators(
            _mixed_steam_frame(),
            "SOCO",
            None,
            measured_st_heat_rates=flag,
        )
        return {g.unit_id: (g.plant_group, g.heat_rate) for g in gens}

    def test_default_off_is_a_no_op(self) -> None:
        """Both units keep the eGRID plant average while the flag is off."""
        self.assertFalse(ScenarioConfig().measured_st_heat_rates)
        loaded = self._load(False)
        self.assertTrue(loaded)
        for _group, hr in loaded.values():
            self.assertAlmostEqual(hr, 11.5505, places=3)

    def test_only_the_gas_steam_units_are_repriced(self) -> None:
        """The measured rate reaches ST_GAS; the coal boiler is untouched."""
        measured = measured_st_heat_rates("SOCO")
        if 26 not in measured:
            self.skipTest("SOCO gas-steam heat-rate artifact not built in this tree")
        loaded = self._load(True)
        coal_group, coal_hr = loaded["26_5"]
        gas_group, gas_hr = loaded["26_1"]
        self.assertEqual(coal_group, "COAL")
        self.assertEqual(gas_group, "ST_GAS")
        self.assertAlmostEqual(gas_hr, measured[26], places=3)
        self.assertAlmostEqual(coal_hr, 11.5505, places=3)
        # And the point of the whole mechanism: the two boilers no longer
        # share one number, which no eGRID construction can achieve because
        # they share a prime mover.
        self.assertNotAlmostEqual(coal_hr, gas_hr, places=3)


class TestCacheKeyRegistration(unittest.TestCase):
    """Default-off must be byte-identical off, armed must re-key."""

    def test_default_key_is_unmoved_and_armed_key_differs(self) -> None:
        # F1: backcast-default ON and coerced off outside a backcast, so the
        # "default-off" base is the explicit-False backcast (the pre-F1 key).
        base = ScenarioConfig(iso="SOCO", mode="backcast", measured_st_heat_rates=False)
        armed = base.with_overrides(measured_st_heat_rates=True)
        self.assertNotEqual(base.cache_key(), armed.cache_key())
        # Registered at its frozen default, so an explicitly-False config keys
        # identically to one that never named the field (no cache orphaning).
        self.assertEqual(
            base.cache_key(),
            base.with_overrides(measured_st_heat_rates=False).cache_key(),
        )


class TestConfigPlumbing(unittest.TestCase):
    """``ScenarioConfig.measured_st_heat_rates`` must reach the fleet loader.

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

        # NYISO, not SOCO: ``load_or_synthesize_bins`` short-circuits for an
        # ISO outside CAMPD_BINNING_ISOS, and SOCO is outside it. SOCO's own
        # fleet path is ``run_calibration.run_year``'s inline synthesis, which
        # TestBackcastFleetSourcing below pins by source inspection. The seam
        # under test here is the one the CAMPD-binning ISOs will take when
        # their own lanes arm this field.
        # F1: the flags are backcast-only (coerced off in a forecast config).
        config = ScenarioConfig(mode="backcast").with_overrides(
            iso="NYISO", measured_st_heat_rates=True, use_campd_bins=True
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
        self.assertIs(seen.get("measured_st_heat_rates"), True)

    def test_base_fleet_branches_forward_the_flag(self) -> None:
        from unittest import mock

        import market_sim.data.fleet as fleet_pkg
        from market_sim.data.fleet.assembly import build_base_fleet

        # F1: the flags are backcast-only (coerced off in a forecast config).
        config = ScenarioConfig(mode="backcast").with_overrides(
            iso="SOCO", measured_st_heat_rates=True
        )
        calls: list[dict] = []

        def _spy(iso, iso_config=None, **kwargs):
            calls.append(kwargs)
            return []

        with mock.patch.object(fleet_pkg, "load_fleet_from_csv", _spy):
            with mock.patch.object(fleet_pkg, "aggregate_fleet", lambda *a, **k: []):
                build_base_fleet(None, "SOCO", None, ["z"], config, [], [], 2023)
            with mock.patch.object(
                fleet_pkg, "bins_to_fleet", lambda *a, **k: ([], None)
            ):
                bins = pd.DataFrame({"Plant_Code": [1], "Plant_Group": ["ST_GAS"]})
                build_base_fleet(bins, "SOCO", None, ["z"], config, [], [], 2023)

        self.assertEqual(len(calls), 2)
        for kwargs in calls:
            self.assertIs(kwargs.get("measured_st_heat_rates"), True)


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
                "measured_st_heat_rates",
                kwargs,
                "run_calibration.py:%d loads the fleet without forwarding "
                "measured_st_heat_rates — the backcast would silently solve "
                "on eGRID heat rates" % call.lineno,
            )


if __name__ == "__main__":
    unittest.main()
