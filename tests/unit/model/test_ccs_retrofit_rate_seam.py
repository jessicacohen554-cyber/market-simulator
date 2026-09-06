"""capx D77 — the CCS retrofit's capture must survive the measured-rate restoration.

A retrofit writes four things onto a generator in
:func:`market_sim.model.capacity.apply_ccs_retrofit` (``heat_rate``, ``vom``,
``emission_rate_co2``, ``fuel_type``, plus the D77 ``ccs_capture_fraction``
stamp). Three of them are never touched again. The CO2 rate is, because
:func:`market_sim.data.fleet.apply_plant_emission_rates_v2` re-books each
plant's **measured** CAMPD rate over it on every dispatch build
(``build_dispatch_fleet``, which the runner calls after ``evolve_fleet`` in
every forecast year) — and it matches on ``(plant_code, coarse fuel class)``,
where ``fuel_class("gas_cc_ccs") == "gas"``, so a converted unit still matches
its own uncaptured host row.

Before D77 that silently restored every retrofitted unit to its host's
uncaptured intensity: measured on NEISO by SCN-WS2b, one unit read 0.3745 →
0.3745 t/MWh across its own 2028 retrofit while its heat rate rose 7.5101 →
8.4113, and the ISO's 47-unit / 9.0 GW ``gas_cc_ccs`` class dispatched, priced
its RGGI carbon adder and was accounted at 0.4149 t/MWh against unabated
gas_cc's 0.4663. This module is the seam test that table implies: a unit's rate
**across its retrofit year, through the restoration**.

``docs/handoffs/FINDING-capx-d77-2026-09-06.md``
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.emission_rates import fuel_class
from market_sim.data.fleet import (
    Generator,
    apply_plant_emission_rates,
    apply_plant_emission_rates_v2,
)
from market_sim.model.capacity import apply_ccs_retrofit

PLANT = 55041  # a real NEISO gas CC plant code; the artifact below is synthetic
HOST_RATE = 0.3745  # t/MWh net — the WS2b unit's measured host rate
CAPTURE = 0.90  # ScenarioConfig.ccs_retrofit_capture_rate default
HR_PENALTY = 0.12  # ScenarioConfig.ccs_retrofit_hr_penalty default
HIGH_PRICES = np.full((1, 24), 60.0)  # deep in merit, so the screen fires


def _v2_artifact(tmp: Path, rate_t_per_mwh: float = HOST_RATE) -> Path:
    """One NEISO gas plant, three CAMPD years, all at ``rate_t_per_mwh``."""
    net_mwh = 1_000_000.0
    rows = [
        {
            "iso": "NEISO",
            "plant_id": PLANT,
            "unit_id": "1",
            "year": y,
            "primary_fuel": "Pipeline Natural Gas",
            "unit_type": "Combined cycle",
            "net_mwh": net_mwh,
            # tonnes/MWh is kg/MWh ÷ 1000 at the loader boundary
            "co2_kg": rate_t_per_mwh * 1000.0 * net_mwh,
            "nox_kg": 0.02 * 1000.0 * net_mwh,
            "so2_kg": 0.001 * 1000.0 * net_mwh,
        }
        for y in (2023, 2024, 2025)
    ]
    path = tmp / "plant_emission_rates_v2.parquet"
    pd.DataFrame(rows).to_parquet(path)
    return path


def _host(unit_id: str = "HOST", fuel_type: str = "gas_cc") -> Generator:
    """A gas CC pinned to ``PLANT``, carrying its own measured host rate."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="Z0",
        fuel_type=fuel_type,
        pmax_mw=500.0,
        heat_rate=7.5101,
        vom=2.0,
        emission_rate_co2=HOST_RATE,
        online_year=2015,
        plant_code=PLANT,
    )


def _screen(fleet, year: int = 2028, **overrides):
    """Run the retrofit screen on ``fleet`` at the shipped defaults."""
    cfg = ScenarioConfig(
        iso="NEISO",
        mode="forecast",
        start_year=year,
        end_year=year,
        # Pin the two fields this seam asserts on, so the test states the
        # arithmetic it checks rather than riding a default that may move
        # (the capx D41 / G-32 fixture-pin discipline).
        ccs_retrofit_capture_rate=CAPTURE,
        ccs_retrofit_hr_penalty=HR_PENALTY,
        **overrides,
    )
    return apply_ccs_retrofit(
        fleet,
        HIGH_PRICES,
        year,
        cfg,
        "NEISO",
        gas_price_per_mmbtu=4.0,
        carbon_price=100.0,
        zone_names=["Z0"],
    )


class TestCaptureSurvivesMeasuredRateRestoration(unittest.TestCase):
    """The D77 defect, at unit grain, in both directions."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.v2 = _v2_artifact(self.tmp)
        self.cfg = ScenarioConfig(
            iso="NEISO",
            mode="forecast",
            start_year=2028,
            end_year=2028,
            use_plant_emission_rates_v2=True,
        )
        self.addCleanup(self._tmp.cleanup)

    def _restore(self, fleet, year: int = 2028) -> int:
        return apply_plant_emission_rates_v2(
            fleet, self.v2, iso="NEISO", year=year, mode="forecast", config=self.cfg
        )

    def test_the_matcher_still_reaches_a_converted_unit(self):
        """The premise of the defect: conversion does not escape the match."""
        self.assertEqual(fuel_class("gas_cc"), "gas")
        self.assertEqual(fuel_class("gas_cc_ccs"), "gas")

    def test_rate_across_the_retrofit_year_is_captured(self):
        """THE regression: retrofit, then restore — the capture must hold."""
        gen = _host()
        fleet, log = _screen([gen])
        self.assertEqual(len(log), 1, "fixture must actually retrofit")

        # ccs.py's own four writes.
        self.assertEqual(gen.fuel_type, "gas_cc_ccs")
        self.assertAlmostEqual(gen.heat_rate, 7.5101 * (1 + HR_PENALTY), places=6)
        self.assertAlmostEqual(gen.ccs_capture_fraction, CAPTURE, places=9)
        self.assertAlmostEqual(gen.emission_rate_co2, HOST_RATE * 0.10, places=9)

        # ...and then the per-year restoration runs over the same object.
        self.assertEqual(self._restore(fleet), 1)
        self.assertAlmostEqual(gen.emission_rate_co2, HOST_RATE * 0.10, places=9)

        # Stated as the identity, not as a literal: the measured HOST rate
        # still enters (rule 13 [R-MEASURED]) and the capture rides on top.
        self.assertAlmostEqual(
            gen.emission_rate_co2, HOST_RATE * (1.0 - CAPTURE), places=9
        )
        # The pre-D77 value, named so a regression is unambiguous.
        self.assertNotAlmostEqual(gen.emission_rate_co2, HOST_RATE, places=4)

    def test_the_other_three_writes_are_untouched_by_the_restoration(self):
        """Heat rate, VOM and fuel type never entered the defect; keep it so."""
        gen = _host()
        fleet, _ = _screen([gen])
        hr, vom, fuel = gen.heat_rate, gen.vom, gen.fuel_type
        self._restore(fleet)
        self.assertEqual(gen.heat_rate, hr)
        self.assertEqual(gen.vom, vom)
        self.assertEqual(gen.fuel_type, fuel)

    def test_the_rate_does_not_follow_the_heat_rate_rise(self):
        """DELIBERATE, and asserted so nobody 'repairs' it into a new DOF.

        WS2b flagged that the retrofit raises the heat rate 12 % while the CO2
        rate did not move, and reasoned that a rate re-derived from the new
        heat rate would have RISEN. It is not re-derived: the forward-year rate
        is a plant-keyed CAMPD **measurement** (rule 13 [R-MEASURED]), not a
        function of the model's heat rate, so no heat-rate linkage exists on
        this path for either an abated or an unabated unit.

        Whether the parasitic load should raise the *gross* stack rate before
        capture (making the residual ``host × (1 + pen) × (1 - capture)``) is a
        SEPARATE second-order question about ``ccs.py``'s own capture
        arithmetic — it would move the screen's §45Q and transport economics,
        so it is routed to the director in the D77 finding §8, not decided
        here. This test pins the shipped semantics: ``× (1 - capture)`` exactly.
        """
        gen = _host()
        fleet, _ = _screen([gen])
        self._restore(fleet)
        self.assertAlmostEqual(gen.emission_rate_co2, HOST_RATE * 0.10, places=9)
        self.assertNotAlmostEqual(
            gen.emission_rate_co2, HOST_RATE * (1 + HR_PENALTY) * 0.10, places=6
        )

    def test_no_unit_outside_the_cohort_moves(self):
        """An unabated sibling at the SAME plant books the measured rate flat."""
        sib = _host("SIB")
        sib.emission_rate_co2 = 0.0  # force the override to do the work
        self.assertEqual(self._restore([sib]), 1)
        self.assertAlmostEqual(sib.emission_rate_co2, HOST_RATE, places=9)
        self.assertEqual(sib.ccs_capture_fraction, 0.0)

    def test_restoration_is_idempotent_across_later_years(self):
        """2029 and 2030 re-run the same override on the same object."""
        gen = _host()
        fleet, _ = _screen([gen])
        for year in (2028, 2029, 2030):
            self._restore(fleet, year=year)
            self.assertAlmostEqual(gen.emission_rate_co2, HOST_RATE * 0.10, places=9)

    def test_nox_and_so2_are_not_scaled_by_capture(self):
        """No capture co-benefit parameter exists; inventing one is a new DOF."""
        gen = _host()
        fleet, _ = _screen([gen])
        self._restore(fleet)
        self.assertAlmostEqual(gen.nox_rate, 0.02, places=9)
        self.assertAlmostEqual(gen.so2_rate, 0.001, places=9)

    def test_v1_legacy_override_carries_the_same_repair(self):
        """``apply_plant_emission_rates`` is the same seam without the mask."""
        path = self.tmp / "plant_emission_rates.parquet"
        pd.DataFrame(
            [
                {
                    "plant_id": PLANT,
                    "year": 0,  # the v1 loader reads the POOLED rows only
                    "mixed": False,
                    "co2_kg_per_mwh_net": HOST_RATE * 1000.0,
                    "nox_kg_per_mwh_net": 20.0,
                    "so2_kg_per_mwh_net": 1.0,
                }
            ]
        ).to_parquet(path)
        gen = _host()
        fleet, _ = _screen([gen])
        self.assertEqual(apply_plant_emission_rates(fleet, path), 1)
        self.assertAlmostEqual(gen.emission_rate_co2, HOST_RATE * 0.10, places=9)


class TestUnabatedFleetIsByteIdentical(unittest.TestCase):
    """Every fleet with no capture island is untouched by the D77 factor."""

    def test_default_capture_fraction_is_zero(self):
        self.assertEqual(
            Generator(
                unit_id="U", name="U", zone="Z0", fuel_type="gas_cc", pmax_mw=1.0
            ).ccs_capture_fraction,
            0.0,
        )

    def test_override_on_an_unabated_fleet_reproduces_the_measured_rate(self):
        with tempfile.TemporaryDirectory() as d:
            v2 = _v2_artifact(Path(d))
            fleet = [_host(f"U{i}") for i in range(3)]
            for g in fleet:
                g.emission_rate_co2 = 0.0
            cfg = ScenarioConfig(
                iso="NEISO",
                mode="forecast",
                start_year=2028,
                end_year=2028,
                use_plant_emission_rates_v2=True,
            )
            apply_plant_emission_rates_v2(
                fleet, v2, iso="NEISO", year=2028, mode="forecast", config=cfg
            )
            for g in fleet:
                self.assertAlmostEqual(g.emission_rate_co2, HOST_RATE, places=9)


if __name__ == "__main__":
    unittest.main()
