"""FR-7 / FR-8 — the thermal fleet ages on the SOLVE year (forecast-readiness
audit §3.2; session FFR-1B).

Two defect families, both rooted in ``_availability_matrix`` keying its year
semantics off ``config.weather_year``:

* **FR-7** — the age-based WEFOR/derate escalation froze every unit at its
  weather-year age for the whole forecast horizon, and a model-built entrant
  (``online_year`` > ``weather_year``) got a NEGATIVE age. The age now keys the
  solve year (the ``year`` argument), falling back to ``weather_year`` only
  when no solve year is threaded — which is exactly the backcast, where the
  harness pins the two equal (byte-identity there).
* **FR-8** — the measured single-event ``BIN_FORCED_DERATE_BY_YEAR`` table
  (Martin Lake 2025) leaked into forecast/crossover years whenever the pinned
  ``weather_year`` matched an entry. Every read site is now gated
  ``mode == "backcast"``.
"""

import unittest
from unittest import mock

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays

_HOURS = 8760


def _thermal_gen(**kw) -> Generator:
    """A plain merchant CC — no floors, no bins, no per-plant overrides."""
    base = dict(
        unit_id="cc1",
        name="Test CC",
        zone="North",
        fuel_type="gas_cc",
        pmax_mw=400.0,
        pmin_mw=0.0,
        heat_rate=7.0,
        eford=0.05,
        plant_group="CC_REGULAR",
        online_year=2000,
        plant_code=0,
    )
    base.update(kw)
    return Generator(**base)


def _availability(config: ScenarioConfig, gens, year):
    fa = generators_to_fleet_arrays(
        gens, ["North"], hours=_HOURS, iso="ERCOT", config=config, year=year
    )
    return fa.availability


class TestSolveYearAge(unittest.TestCase):
    """FR-7: the age model keys the solve year, not the weather pin."""

    def _forecast_cfg(self, **kw) -> ScenarioConfig:
        return ScenarioConfig(mode="forecast", weather_year=2024, hours=_HOURS, **kw)

    def test_entrant_age_never_negative(self):
        """A 2035 entrant in a 2040 solve is aged 5, never 2024-2035 = -11.

        Records every age handed to the outage model — the acceptance
        assertion of audit row P1-b (`entrant age >= 0 asserted in a unit
        test`).
        """
        from market_sim.data.fleet import arrays as arrays_mod

        seen_ages: list[float] = []
        real = arrays_mod._thermal_outage

        def _recording(category, age):
            seen_ages.append(float(age))
            return real(category, age)

        cfg = self._forecast_cfg()
        entrant = _thermal_gen(unit_id="new_cc", online_year=2035)
        with mock.patch.object(arrays_mod, "_thermal_outage", _recording):
            _availability(cfg, [entrant], year=2040)
        self.assertTrue(seen_ages, "outage model never consulted")
        self.assertTrue(
            all(a >= 0.0 for a in seen_ages),
            f"negative entrant age reached the outage model: {seen_ages}",
        )
        self.assertIn(2040 - 2035, [int(a) for a in seen_ages])

    def test_fleet_ages_monotonically_through_forecast_horizon(self):
        """The same unit's availability never rises as the horizon advances.

        Pre-FR-7 every solve year returned the frozen weather-year age, so
        this sequence was constant; an aging unit past its escalation onset
        (CC online 2000, onset 20y) must now decline.
        """
        cfg = self._forecast_cfg()
        unit = [_thermal_gen()]
        means = [
            float(np.mean(_availability(cfg, unit, year=y)))
            for y in (2026, 2030, 2040, 2050)
        ]
        for earlier, later in zip(means, means[1:]):
            self.assertGreater(
                earlier,
                later,
                f"availability did not age monotonically: {means}",
            )

    def test_same_age_same_availability_regardless_of_solve_year(self):
        """Age is the ONLY thing the solve year moves (weather pin fixed).

        A unit aged 5 in a 2040 solve (online 2035) must match a unit aged 5
        in a 2029 solve (online 2024) on the same weather 8760 — pinning that
        the fix rides ONLY the age term, not some other year-keyed input.
        """
        cfg = self._forecast_cfg()
        a_2040 = _availability(cfg, [_thermal_gen(online_year=2035)], year=2040)
        a_2029 = _availability(cfg, [_thermal_gen(online_year=2024)], year=2029)
        np.testing.assert_array_equal(a_2040, a_2029)

    def test_backcast_fallback_is_value_identical(self):
        """year=None falls back to weather_year — the legacy-caller contract.

        In backcast the harness pins weather_year == solve year, so the
        threaded and fallback paths must agree bit-for-bit (the keeper
        byte-identity invariant of this change).
        """
        cfg = ScenarioConfig(mode="backcast", weather_year=2024, hours=_HOURS)
        unit = [_thermal_gen()]
        np.testing.assert_array_equal(
            _availability(cfg, unit, year=2024),
            _availability(cfg, unit, year=None),
        )


class TestForcedDerateBackcastGate(unittest.TestCase):
    """FR-8: the measured event table is reachable in backcast mode only."""

    _TABLE = {"T_CC9": {2025: 0.5}}

    def _avail_mean(self, mode: str, weather_year: int, year: int) -> float:
        cfg = ScenarioConfig(mode=mode, weather_year=weather_year, hours=_HOURS)
        gen = _thermal_gen(bin_label="T_CC9")
        with mock.patch(
            "market_sim.data.fleet.arrays.BIN_FORCED_DERATE_BY_YEAR", self._TABLE
        ):
            return float(np.mean(_availability(cfg, [gen], year=year)))

    def test_backcast_applies_the_measured_derate(self):
        derated = self._avail_mean("backcast", 2025, 2025)
        clean = self._avail_mean("backcast", 2024, 2024)  # no 2024 entry
        self.assertLess(derated, clean * 0.6)  # the 0.5 multiplier landed

    def test_forecast_same_calendar_year_is_untouched(self):
        """mode, not the year, is the gate: a 2025 forecast year skips it."""
        forecast = self._avail_mean("forecast", 2025, 2025)
        backcast = self._avail_mean("backcast", 2025, 2025)
        self.assertGreater(forecast, backcast / 0.5 * 0.9)

    def test_crossover_weather_pin_cannot_leak_the_event(self):
        """The FR-8 reproduction: weather_year=2025 pinned, forward solve year.

        Pre-gate this multiplied every crossover solve year by the 2025
        event; the forward year must now match a derate-free forecast build.
        """
        pinned = self._avail_mean("forecast", 2025, 2026)
        unpinned = self._avail_mean("forecast", 2024, 2026)
        self.assertAlmostEqual(pinned, unpinned, places=12)

    def test_martin_lake_entry_still_fires_in_backcast_2025(self):
        """The real N_COAL4 entry keeps carrying the destroyed unit (rule 14).

        The gate must not orphan the retained registry-test-pinned entry:
        a backcast 2025 COAL unit binned N_COAL4 still loses ~33%.
        """
        cfg = ScenarioConfig(mode="backcast", weather_year=2025, hours=_HOURS)
        binned = _thermal_gen(
            unit_id="ml", plant_group="COAL_BIT", fuel_type="coal", bin_label="N_COAL4"
        )
        plain = _thermal_gen(
            unit_id="ml0", plant_group="COAL_BIT", fuel_type="coal", bin_label=""
        )
        avail = _availability(cfg, [binned, plain], year=2025)
        ratio = float(np.mean(avail[0]) / np.mean(avail[1]))
        self.assertAlmostEqual(ratio, 0.67, places=6)


if __name__ == "__main__":
    unittest.main()
