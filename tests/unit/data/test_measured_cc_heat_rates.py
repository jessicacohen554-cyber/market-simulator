"""Tests for the measured CC_REGULAR operating-heat-rate input (soco-57).

The combined-cycle sibling of ``tests/unit/data/test_measured_coal_heat_rates.py``
and ``test_measured_ct_heat_rates.py``, covering the same three seams because
it is the same mechanism on a different class:

1. the derive's measurement (generation weighting, gross-to-net conversion,
   physical-band flagging),
2. the artifact loader (``flag == "ok"`` only, absent-file no-op), and
3. the fleet wiring — the override reaches only ``CC_REGULAR`` rows, so a CC
   site's boilers keep their own class's rate, and it is a strict no-op while
   ``ScenarioConfig.measured_cc_heat_rates`` is off.

Plus a fourth seam this mechanism has and its siblings do not: THE BOUNDARY
GUARD. At some sites CAMPD meters the combustion turbines but not the unfired
steam generator, so ``heatInput / grossLoad`` is the COMBUSTION-TURBINE rate —
roughly 1.5x the plant's true combined-cycle rate — and applying it would
price a healthy plant out of merit on a metering artifact. The guard tests
CAMPD's pooled CC gross load against EIA-923's CC net generation and refuses
any plant outside the physical band.

(3) matters here for the same reason it does on the coal side, and SOCO is the
worked example: lane SOCO-56 established that Barry (plant 3) carries three
gas-fired BOILERS and five genuine combined-cycle units behind one plant code,
so an override applied by plant code alone would reprice the boilers too.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import measured_cc_heat_rates
from market_sim.data.fleet.eia860 import _rows_to_generators
from scripts.data.derive_campd_cc_heat_rates import (
    _BOUNDARY_MAX,
    _BOUNDARY_MIN,
    _GROSS_NET_IDENTITY_MIN,
    _HR_MAX_NET,
    _HR_MIN_NET,
    TARGET_CLASS,
    _is_cc_unit,
    plant_table,
)


def _unit_rows() -> pd.DataFrame:
    """Return a four-plant per-unit table for :func:`plant_table`."""
    return pd.DataFrame(
        [
            # Plant 1: two trains, different rates and very different energy.
            # The plant value must follow the big train, not the average.
            {
                "plant_code": 1,
                "plant_name": "Two Train Station",
                "unit_id": "CT1",
                "gross_mwh": 9_000_000.0,
                "steady_hours": 20_000,
                "cap_mw": 500.0,
                "hr_gross": 6.8,
                "hr_gross_hsl": 6.6,
            },
            {
                "plant_code": 1,
                "plant_name": "Two Train Station",
                "unit_id": "CT2",
                "gross_mwh": 1_000_000.0,
                "steady_hours": 4_000,
                "cap_mw": 120.0,
                "hr_gross": 10.8,
                "hr_gross_hsl": 10.4,
            },
            # Plant 2: ordinary, inside the band on a net basis.
            {
                "plant_code": 2,
                "plant_name": "Single Train Station",
                "unit_id": "CT1",
                "gross_mwh": 3_000_000.0,
                "steady_hours": 9_000,
                "cap_mw": 300.0,
                "hr_gross": 7.1,
                "hr_gross_hsl": 6.9,
            },
            # Plant 3: a broken meter -- above the physical band even gross.
            {
                "plant_code": 3,
                "plant_name": "Broken Meter Station",
                "unit_id": "CT1",
                "gross_mwh": 100_000.0,
                "steady_hours": 1_000,
                "cap_mw": 50.0,
                "hr_gross": 24.0,
                "hr_gross_hsl": 23.5,
            },
            # Plant 4: a physically ordinary CC rate that is nonetheless the
            # CT-only rate, because the steam turbine is not in the meter.
            # Modelled on SOCO's Wansley (7946) and McWilliams (533).
            {
                "plant_code": 4,
                "plant_name": "Steam Not Metered Station",
                "unit_id": "CT1",
                "gross_mwh": 2_000_000.0,
                "steady_hours": 8_000,
                "cap_mw": 250.0,
                "hr_gross": 10.6,
                "hr_gross_hsl": 10.3,
            },
        ]
    )


_BOUNDARY = {1: 1.03, 2: 1.02, 3: 1.01, 4: 0.675}


def _table() -> pd.DataFrame:
    return plant_table(
        _unit_rows(),
        "FAKEISO",
        [2023, 2024, 2025],
        caps={1: 620.0, 2: 300.0, 3: 50.0, 4: 250.0},
        model_hr={1: 7.5, 2: 7.4, 3: 8.0, 4: 7.2},
        factors={},
        boundary=_BOUNDARY,
    ).set_index("plant_code")


class TestDerive(unittest.TestCase):
    """The plant aggregate is generation-weighted, net-converted and flagged."""

    def test_generation_weighting_follows_the_big_train(self) -> None:
        """Plant 1's rate sits near its 9 GWh train, not the 2-train mean."""
        gross = float(_table().loc[1, "heat_rate_gross"])
        # 0.9 * 6.8 + 0.1 * 10.8 == 7.2; a plain mean would give 7.8.
        self.assertAlmostEqual(gross, 7.2, places=6)
        self.assertLess(gross, 7.8)

    def test_gross_to_net_conversion_is_applied(self) -> None:
        """``heat_rate`` is the gross rate divided by the parasitic factor."""
        table = _table()
        factor = float(table.loc[1, "parasitic_factor"])
        self.assertAlmostEqual(factor, 0.975, places=6)  # 1 - the CC default
        self.assertAlmostEqual(
            float(table.loc[1, "heat_rate"]),
            float(table.loc[1, "heat_rate_gross"]) / factor,
            places=3,
        )
        # The conversion raises the rate: comparing a gross measurement to the
        # model's net rate would understate the plant's cost.
        self.assertGreater(
            float(table.loc[1, "heat_rate"]), float(table.loc[1, "heat_rate_gross"])
        )

    def test_physical_band_flags_the_broken_meter(self) -> None:
        table = _table()
        self.assertEqual(table.loc[1, "flag"], "ok")
        self.assertEqual(table.loc[2, "flag"], "ok")
        self.assertEqual(table.loc[3, "flag"], "above_physical_band")
        self.assertGreater(float(table.loc[3, "heat_rate"]), _HR_MAX_NET)
        self.assertLess(_HR_MIN_NET, float(table.loc[1, "heat_rate"]))

    def test_hsl_column_is_reported_not_applied(self) -> None:
        """The near-HSL rate is carried for the reader and never applied."""
        table = _table()
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

    def test_target_class_is_cc_regular(self) -> None:
        self.assertEqual(TARGET_CLASS, "CC_REGULAR")


class TestBoundaryGuard(unittest.TestCase):
    """A plant whose steam turbine is not metered is refused, not applied.

    This is the seam the sibling mechanisms do not have. Without it the CT-only
    rate (~1.5x the true CC rate) would be applied as if it were the plant's,
    pricing a healthy combined cycle out of merit on a metering artifact.
    """

    def test_unmetered_steam_is_refused_by_name(self) -> None:
        table = _table()
        self.assertEqual(table.loc[4, "flag"], "steam_not_metered")
        # Its measured rate is physically fine -- it is the BOUNDARY that
        # refuses it, so a band-based flag would name the wrong defect.
        self.assertLess(float(table.loc[4, "heat_rate"]), _HR_MAX_NET)
        self.assertGreater(float(table.loc[4, "heat_rate"]), _HR_MIN_NET)

    def test_boundary_precedes_the_physical_band(self) -> None:
        """Flag precedence is boundary first: no CC rate exists to be in band."""
        rows = _unit_rows()
        rows.loc[rows.plant_code == 4, "hr_gross"] = 24.0
        table = plant_table(
            rows,
            "FAKEISO",
            [2024],
            caps={4: 250.0},
            model_hr={},
            factors={},
            boundary=_BOUNDARY,
        ).set_index("plant_code")
        self.assertEqual(table.loc[4, "flag"], "steam_not_metered")

    def test_missing_comparator_is_refused(self) -> None:
        table = plant_table(
            _unit_rows(),
            "FAKEISO",
            [2024],
            caps={},
            model_hr={},
            factors={},
            boundary={1: 1.03, 2: 1.02, 3: 1.01},
        ).set_index("plant_code")
        self.assertEqual(table.loc[4, "flag"], "no_eia923_comparator")

    def test_band_sits_inside_the_measured_gap(self) -> None:
        """The band is fixed on physics, not on where SOCO's plants landed.

        SOCO's two clusters are 0.675 / 0.719 against 1.014 ... 1.116, so the
        gap (0.72, 1.01) is empty and NO threshold inside it changes the
        partition. The guard is therefore not a swept parameter.
        """
        self.assertGreater(_BOUNDARY_MIN, 0.72)
        self.assertLess(_BOUNDARY_MIN, 1.01)
        self.assertGreater(_BOUNDARY_MAX, 1.116)

    def test_gross_below_net_is_refused_by_name(self) -> None:
        """Gross < net is impossible when the whole CC is metered (R-CAISO-2).

        A ratio above the steam-missing cluster but below 1.0 means part of
        the plant's output left CAMPD's gross load (Pastoria 55656, 2020+), so
        its rate is over-stated and must not be applied.
        """
        table = plant_table(
            _unit_rows(),
            "FAKEISO",
            [2024],
            caps={},
            model_hr={},
            factors={},
            boundary={1: 1.03, 2: 0.93, 3: 1.01, 4: 0.675},
        ).set_index("plant_code")
        self.assertEqual(table.loc[2, "flag"], "gross_below_net")
        self.assertEqual(table.loc[4, "flag"], "steam_not_metered")
        self.assertEqual(table.loc[1, "flag"], "ok")

    def test_identity_floor_is_physics(self) -> None:
        """The identity floor is exactly 1.0 and sits above the steam band."""
        self.assertEqual(_GROSS_NET_IDENTITY_MIN, 1.0)
        self.assertGreater(_GROSS_NET_IDENTITY_MIN, _BOUNDARY_MIN)

    def test_boundary_ratio_is_always_reported(self) -> None:
        """Written for every plant so a refusal is legible without re-deriving."""
        table = _table()
        self.assertIn("boundary_gross_over_net", table.columns)
        self.assertAlmostEqual(float(table.loc[4, "boundary_gross_over_net"]), 0.675, 3)


class TestUnitTypeTag(unittest.TestCase):
    """``unitType`` separates combined-cycle machines from boilers.

    This is the tag choice the module docstring turns on: at Barry (SOCO-56)
    the gas boilers and the genuine CC units BOTH read "Pipeline Natural Gas"
    in ``primaryFuelInfo``, so only ``unitType`` can do the separation. The
    match is a PREFIX so CAMPD's commissioning variants are caught.
    """

    def test_cc_strings_match_and_others_do_not(self) -> None:
        s = pd.Series(
            [
                "Combined cycle",
                "combined cycle",
                "Combined cycle (Started Feb 19, 2023)",
                "Combined cycle (Started Jul 17, 2023)",
                "Tangentially-fired",
                "Combustion turbine",
                "Cell burner boiler",
                "Dry bottom wall-fired boiler",
                "Other turbine",
            ]
        )
        mask = _is_cc_unit(s).tolist()
        self.assertEqual(mask[:4], [True] * 4)
        self.assertEqual(mask[4:], [False] * 5)


class TestArtifactLoader(unittest.TestCase):
    """``measured_cc_heat_rates`` applies only clean rows, and fails soft."""

    def test_absent_artifact_is_empty(self) -> None:
        measured_cc_heat_rates.cache_clear()
        self.assertEqual(measured_cc_heat_rates("NO_SUCH_ISO"), {})

    def test_flagged_rows_excluded(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "campd_cc_heat_rates_FAKEISO.csv"
            pd.DataFrame(
                [
                    {"plant_code": 1, "heat_rate": 6.9, "flag": "ok"},
                    {"plant_code": 2, "heat_rate": 10.9, "flag": "steam_not_metered"},
                    {"plant_code": 3, "heat_rate": 30.0, "flag": "above_physical_band"},
                    {"plant_code": 4, "heat_rate": 0.0, "flag": "ok"},
                ]
            ).to_csv(path, index=False)
            import market_sim.data.fleet.campd_bins as cb

            measured_cc_heat_rates.cache_clear()
            original = cb.PROCESSED_DIR
            try:
                cb.PROCESSED_DIR = Path(tmp)
                self.assertEqual(measured_cc_heat_rates("FAKEISO"), {1: 6.9})
            finally:
                cb.PROCESSED_DIR = original
                measured_cc_heat_rates.cache_clear()


def _mixed_site_frame() -> pd.DataFrame:
    """Return an EIA-860 frame for one plant spanning CC_REGULAR and ST_GAS.

    Modelled on Barry (3): gas-fired boilers sharing a plant code — and
    therefore a single eGRID heat rate — with genuine combined-cycle units.
    """
    common = {
        "plant_id": 3,
        "plant_name": "Mixed Site",
        "status": "OP",
        "state": "AL",
        "operating_year": 2000,
        "operating_month": 1,
        "heat_rate": 7.8209,
        "chp": "N",
    }
    return pd.DataFrame(
        [
            {
                **common,
                "generator_id": "A1C1",
                "energy_source": "NG",
                "technology": "Natural Gas Fired Combined Cycle",
                "prime_mover": "CT",
                "nameplate_capacity_mw": 170.1,
                "net_summer_capacity_mw": 184.4,
            },
            {
                **common,
                "generator_id": "1",
                "energy_source": "NG",
                "technology": "Natural Gas Steam Turbine",
                "prime_mover": "ST",
                "nameplate_capacity_mw": 250.0,
                "net_summer_capacity_mw": 250.0,
            },
        ]
    )


class TestFleetSeam(unittest.TestCase):
    """The override is class-scoped and default-off."""

    def _load(self, flag: bool) -> dict[str, tuple[str, float]]:
        gens = _rows_to_generators(
            _mixed_site_frame(),
            "SOCO",
            None,
            measured_cc_heat_rates=flag,
        )
        return {g.unit_id: (g.plant_group, g.heat_rate) for g in gens}

    def test_default_off_is_a_no_op(self) -> None:
        """Both units keep the eGRID plant average while the flag is off."""
        self.assertFalse(ScenarioConfig().measured_cc_heat_rates)
        loaded = self._load(False)
        self.assertTrue(loaded)
        for _group, hr in loaded.values():
            self.assertAlmostEqual(hr, 7.8209, places=3)

    def test_only_the_cc_units_are_repriced(self) -> None:
        """The measured rate reaches CC_REGULAR; the gas boiler is untouched."""
        measured = measured_cc_heat_rates("SOCO")
        if 3 not in measured:
            self.skipTest("SOCO CC heat-rate artifact not built in this tree")
        loaded = self._load(True)
        cc_group, cc_hr = loaded["3_A1C1"]
        st_group, st_hr = loaded["3_1"]
        self.assertEqual(cc_group, "CC_REGULAR")
        self.assertEqual(st_group, "ST_GAS")
        self.assertAlmostEqual(cc_hr, measured[3], places=3)
        self.assertAlmostEqual(st_hr, 7.8209, places=3)


class TestCacheKeyRegistration(unittest.TestCase):
    """Default-off must be byte-identical off, armed must re-key."""

    def test_default_key_is_unmoved_and_armed_key_differs(self) -> None:
        # F1: backcast-default ON and coerced off outside a backcast, so the
        # "default-off" base is the explicit-False backcast (the pre-F1 key).
        base = ScenarioConfig(iso="SOCO", mode="backcast", measured_cc_heat_rates=False)
        armed = base.with_overrides(measured_cc_heat_rates=True)
        self.assertFalse(base.measured_cc_heat_rates)
        self.assertTrue(armed.measured_cc_heat_rates)
        self.assertNotEqual(base.cache_key(), armed.cache_key())


if __name__ == "__main__":
    unittest.main()
