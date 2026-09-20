"""Tests for the CAISO daily-spot gas LEVEL swap (caiso-84).

``caiso_citygate_spot_level`` (FINDING-caiso-winter-gas-level-2026-07-15) re-levels
the CAISO gas hub overlay from the EIA N3050CA3 monthly citygate *survey*
(acquisition cost) onto the measured California Composite Average daily citygate
*spot* series the marginal cost-based DEB actually bids at, keeping both the
within-month shape and the monthly level on the daily series. It is a pure LEVEL
swap on the keeper's covered month-set:

  * flag OFF -> the daily leg is byte-identical to the survey-mean-preserving
    ``gas_hub_basis_daily`` path, and ``apply_hub_basis_overlay`` is unchanged;
  * flag ON  -> covered months are levelled at the daily-spot monthly mean
    (Jan-2023 ~$16.6/MMBtu incl. transport vs the survey's ~$28), the sign of
    the survey-vs-spot wedge reverses in Mar/Oct-2023 (a fit-chasing knob
    could not raise those months), coverage is unchanged (a survey-uncovered
    month such as CAISO 2025 Sep-Nov stays uncovered), and non-CAISO ISOs are
    untouched.

Skipped when the committed measured inputs (basis CSV + daily citygate spot)
are absent.
"""

import types
import unittest

import numpy as np

from market_sim.config.constants import CAISO_CITYGATE_TRANSPORT_ADDER
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import fuel
from market_sim.data.fleet import FUEL_TYPE_MAP

_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = tuple(int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(12))
_HOURS = 8760

_HAVE_DATA = fuel.iso_hub_monthly_gas_prices(
    ScenarioConfig(iso="CAISO", hours=_HOURS), 2023
) is not None and bool(fuel._caiso_citygate_daily_dated(None).get(2023))


def _month_mean(series: np.ndarray, m: int) -> float:
    s = _MONTH_START_HOUR[m]
    seg = series[s : s + _DAYS_IN_MONTH[m] * 24]
    return float(np.nanmean(seg)) if np.isfinite(seg).any() else float("nan")


@unittest.skipUnless(_HAVE_DATA, "CAISO basis CSV or daily citygate spot not on disk")
class TestCaisoCitygateSpotLevel(unittest.TestCase):
    def _cfg(self, spot_level: bool) -> ScenarioConfig:
        return ScenarioConfig(
            iso="CAISO",
            # The measured CA daily citygate spot series is a backcast-only
            # overlay (FFR-1D rule-13 guard, audit FR-11).
            mode="backcast",
            hours=_HOURS,
            gas_hub_basis_overlay=True,
            caiso_citygate_spot_level=spot_level,
        )

    def test_default_leg_byte_identical_and_mean_preserving(self) -> None:
        """spot_level=False leaves the daily leg exactly as before (mean-preserving)."""
        cfg = ScenarioConfig(iso="CAISO", hours=_HOURS)
        for year in (2023, 2024, 2025):
            survey = fuel.iso_hub_monthly_gas_prices(cfg, year)
            default_leg = fuel._caiso_hub_daily_gas_prices(cfg, year)
            spot_off = fuel._caiso_hub_daily_gas_prices(cfg, year, spot_level=False)
            # spot_level=False is the literal default argument.
            np.testing.assert_array_equal(default_leg, spot_off)
            # The default daily leg is mean-preserving to the survey monthly.
            for m in range(12):
                if not np.isnan(survey[m]):
                    self.assertAlmostEqual(
                        _month_mean(default_leg, m), float(survey[m]), places=6
                    )

    def test_jan_2023_levelled_at_daily_spot(self) -> None:
        """Jan-2023 covered gas prices sit at the daily-spot mean (~$17.3), not $28."""
        cfg = self._cfg(spot_level=True)
        spot = fuel._caiso_hub_daily_gas_prices(cfg, 2023, spot_level=True)
        jan = _month_mean(spot, 0) + CAISO_CITYGATE_TRANSPORT_ADDER
        # Measured CA Composite daily-spot Jan-2023 mean + $0.46 transport.
        # caiso-288 (2026-09-20): 16.58 -> 17.33, a SOURCE-COVERAGE re-derivation
        # under rule 23 [R-FROZEN-DERIVE] and NOT a residual (the C3a residual is
        # a 2022 object and this constant is 2023). The committed daily series
        # had no print before 2023-01-05, because EIA publishes no Weekly Update
        # over the New Year and carries the skipped weeks as EXTRA LIVE TABLES on
        # the catch-up page, which fetch_caiso_citygate_daily's re.search
        # discarded. Jan 1-4 were therefore back-filled from the Jan-5 print
        # ($16.55); they now carry their own measured prints (Jan-3 $23.66,
        # Jan-4 $18.37), which are higher, so the month mean RISES. The repair
        # moves this constant AGAINST the direction a fit would want.
        self.assertAlmostEqual(jan, 17.33, delta=0.30)
        # Far below the survey level the keeper prices Jan at (~$28/MMBtu).
        survey = fuel.iso_hub_monthly_gas_prices(cfg, 2023)
        self.assertLess(jan, float(survey[0]) - 8.0)

    def test_sign_reversal_months_move_up(self) -> None:
        """Mar/Oct-2023 (survey BELOW spot) rise; Jan/Feb (survey ABOVE) fall.

        A residual-fitted knob could not raise the shoulder months — only a
        genuine survey->spot basis-source swap flips the sign of the wedge.
        """
        cfg = self._cfg(spot_level=True)
        survey = fuel.iso_hub_monthly_gas_prices(cfg, 2023)
        spot = fuel._caiso_hub_daily_gas_prices(cfg, 2023, spot_level=True)
        # Winter: survey over-prices -> spot below survey.
        for m in (0, 1):  # Jan, Feb
            self.assertLess(_month_mean(spot, m), float(survey[m]))
        # Shoulder: survey under-prices -> spot above survey.
        for m in (2, 9):  # Mar, Oct
            self.assertGreater(_month_mean(spot, m), float(survey[m]))

    def test_coverage_month_set_unchanged(self) -> None:
        """spot_level covers exactly the survey-covered months (2025 Sep-Nov stay out)."""
        cfg = self._cfg(spot_level=True)
        for year in (2023, 2024, 2025):
            default_leg = fuel._caiso_hub_daily_gas_prices(cfg, year)
            spot = fuel._caiso_hub_daily_gas_prices(cfg, year, spot_level=True)
            self.assertEqual(np.isnan(default_leg).tolist(), np.isnan(spot).tolist())
        # 2025 Sep/Oct/Nov have no basis row -> uncovered in both.
        spot_2025 = fuel._caiso_hub_daily_gas_prices(cfg, 2025, spot_level=True)
        for m in (8, 9, 10):
            self.assertTrue(np.isnan(_month_mean(spot_2025, m)))

    def test_overlay_off_byte_identical(self) -> None:
        """apply_hub_basis_overlay with the flag off matches the survey overlay exactly."""
        fleet = types.SimpleNamespace(
            fuel_type_idx=np.array(
                [FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["coal"]], dtype=int
            )
        )
        base = np.full((2, _HOURS), 5.0)
        off = base.copy()
        fuel.apply_hub_basis_overlay(off, fleet, self._cfg(spot_level=False), 2023)
        # Independent survey-monthly reconstruction of the covered gas row.
        survey = fuel.iso_hub_monthly_gas_prices(self._cfg(False), 2023)
        expected = base.copy()
        for m in range(12):
            if np.isnan(survey[m]):
                continue
            s = _MONTH_START_HOUR[m]
            e = s + _DAYS_IN_MONTH[m] * 24
            expected[0, s:e] = float(survey[m]) + CAISO_CITYGATE_TRANSPORT_ADDER
        np.testing.assert_allclose(off[0], expected[0])
        # Coal row never touched.
        np.testing.assert_array_equal(off[1], base[1])

    def test_overlay_on_reprices_gas_at_spot(self) -> None:
        """Flag on drops the covered gas rows to the daily-spot level + transport."""
        fleet = types.SimpleNamespace(
            fuel_type_idx=np.array(
                [FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["coal"]], dtype=int
            )
        )
        base = np.full((2, _HOURS), 5.0)
        on = base.copy()
        fuel.apply_hub_basis_overlay(on, fleet, self._cfg(spot_level=True), 2023)
        # Jan-2023 covered gas price == daily-spot mean + transport.
        spot = fuel._caiso_hub_daily_gas_prices(self._cfg(True), 2023, spot_level=True)
        jan_expected = _month_mean(spot, 0) + CAISO_CITYGATE_TRANSPORT_ADDER
        self.assertAlmostEqual(_month_mean(on[0], 0), jan_expected, places=4)
        # Coal row untouched.
        np.testing.assert_array_equal(on[1], base[1])

    def test_non_caiso_flag_is_noop(self) -> None:
        """The routing guard keeps the flag inert for non-CAISO ISOs."""
        cfg = ScenarioConfig(
            iso="NEISO",
            mode="backcast",
            hours=_HOURS,
            gas_hub_basis_overlay=True,
            caiso_citygate_spot_level=True,
        )
        fleet = types.SimpleNamespace(
            fuel_type_idx=np.array([FUEL_TYPE_MAP["gas_cc"]], dtype=int)
        )
        a = np.full((1, _HOURS), 5.0)
        b = a.copy()
        # Same config but with the flag off must give the identical result for NEISO.
        fuel.apply_hub_basis_overlay(a, fleet, cfg, 2023)
        cfg_off = cfg.with_overrides(caiso_citygate_spot_level=False)
        fuel.apply_hub_basis_overlay(b, fleet, cfg_off, 2023)
        np.testing.assert_array_equal(a, b)


if __name__ == "__main__":
    unittest.main()
