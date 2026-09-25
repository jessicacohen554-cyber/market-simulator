"""Tests for the per-year coal `_peak` offer LEVEL (ercot-192).

``ScenarioConfig.coal_peak_offer_yearly_level`` — matrix §5.1 item 13, owner
signature **B1** on ``docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md``
card B. What must hold (the precommit's construction contract,
``docs/PRECOMMIT-ercot192-coal-limbs-2023-reapplication-2026-08-12.md`` §4):

- a solve year PRESENT in the year table prices `_peak` at
  ``level_year + GAS_HR × (gas_cc(t) − anchor)``;
- a solve year ABSENT from the table is **BYTE-IDENTICAL** to the static
  ERCOT-140 path — the G-BIT kill's unit-level face, and the reason 2024/2025
  cannot move in the A/B;
- the SLOPE and the SHARED gas anchor are untouched: only the level swaps
  (rule 19 ``[R-ONE-MECH]`` — one gas identification point for the whole offer
  surface);
- `_mustrun` and committed/econ rows are untouched — each end of the curve
  keeps its own measured owner;
- arming without ``coal_peak_offer_margin``, without a resolved table, or
  without a solve year is a hard error (rule 24 ``[R-REGISTRY]``).

Trivial fixtures per the repo testing pattern: one coal plant with three
tranches plus the one CC_REGULAR row the mechanism's gas reference series
needs, 24 hours.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fleet.legacy_bins import apply_coal_tranches, assemble_mc

COAL_HR = 10.0
COAL_VOM = 4.5
COAL_FUEL = 1.45
GAS_FUEL = 2.60
PLANT = 6180

STATIC_LEVEL = 35.1989
GAS_HR = 10.4100
ANCHOR = 2.2494
YEAR_LEVEL = 71.3378  # constants.COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO ERCOT 2023
HOURS = 24


def _gen(unit_id: str, pmax: float, fuel: str, group: str) -> Generator:
    return Generator(
        unit_id=unit_id,
        name="t",
        zone="N",
        fuel_type=fuel,
        efficiency_bin="subcritical",
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=COAL_HR,
        vom=COAL_VOM,
        emission_rate_co2=0.0,
        nox_rate=0.0,
        eford=0.05,
        online_year=1980,
        is_campd_bin=True,
        plant_group=group,
        bin_label="X",
        plant_code=PLANT,
    )


def _fleet():
    """Three coal tranches plus the CC_REGULAR row gas_cc(t) is built from."""
    return [
        _gen(f"COAL_N_{PLANT}_mustrun", 300.0, "coal", "COAL_BIT"),
        _gen(f"COAL_N_{PLANT}_econhi", 150.0, "coal", "COAL_BIT"),
        _gen(f"COAL_N_{PLANT}_peak", 150.0, "coal", "COAL_BIT"),
        _gen("CC_N_9999_committed", 400.0, "gas_cc", "CC_REGULAR"),
    ]


def _mc(config: ScenarioConfig, year: int | None):
    gens = _fleet()
    fa = generators_to_fleet_arrays(gens, ["N"], config=config, hours=HOURS)
    fuel = np.empty((len(gens), HOURS))
    fuel[:3, :] = COAL_FUEL
    fuel[3, :] = GAS_FUEL
    mc = assemble_mc(fa, fuel, 0.0, 0.0)
    base = mc.copy()
    apply_coal_tranches(mc, gens, fa, [1.0] * len(gens), fuel, config, year=year)
    return mc, base, fa


def _cfg(yearly: bool, table=None, margin: bool = True) -> ScenarioConfig:
    kw = dict(
        hours=HOURS,
        coal_peak_offer_margin=margin,
        coal_peak_offer_level=STATIC_LEVEL,
        coal_peak_offer_gas_hr=GAS_HR,
        gas_offer_margin_anchor=ANCHOR,
    )
    if yearly:
        kw["coal_peak_offer_yearly_level"] = True
        kw["coal_peak_offer_level_yearly"] = table
    return ScenarioConfig(**kw)


#: The peak row's resolved all-in bid at a given level, with the assembled
#: coal fuel + VOM removed exactly as the ERCOT-140 branch removes them.
def _expected_peak(level: float) -> float:
    return level + GAS_HR * (GAS_FUEL - ANCHOR)


class YearLevelApplication(unittest.TestCase):
    def test_year_in_table_uses_the_year_level(self) -> None:
        mc, _base, _fa = _mc(_cfg(True, {2023: YEAR_LEVEL}), 2023)
        np.testing.assert_allclose(mc[2, :], _expected_peak(YEAR_LEVEL))

    def test_year_absent_falls_through_bit_identically(self) -> None:
        """G-BIT's unit-level face: 2024/2025 must be byte-identical."""
        static, _b, _f = _mc(_cfg(False), 2024)
        yearly, _b2, _f2 = _mc(_cfg(True, {2023: YEAR_LEVEL}), 2024)
        self.assertTrue(np.array_equal(static, yearly))
        np.testing.assert_allclose(yearly[2, :], _expected_peak(STATIC_LEVEL))

    def test_slope_and_anchor_are_untouched(self) -> None:
        """Only the LEVEL swaps — the gas response is identical either way."""
        static, _b, _f = _mc(_cfg(False), 2023)
        yearly, _b2, _f2 = _mc(_cfg(True, {2023: YEAR_LEVEL}), 2023)
        np.testing.assert_allclose(
            yearly[2, :] - static[2, :], YEAR_LEVEL - STATIC_LEVEL
        )

    def test_other_tranches_untouched(self) -> None:
        """`_mustrun` and econ rows keep their own owners (rule 19)."""
        static, _b, _f = _mc(_cfg(False), 2023)
        yearly, _b2, _f2 = _mc(_cfg(True, {2023: YEAR_LEVEL}), 2023)
        np.testing.assert_array_equal(static[0, :], yearly[0, :])
        np.testing.assert_array_equal(static[1, :], yearly[1, :])
        np.testing.assert_array_equal(static[3, :], yearly[3, :])

    def test_string_keys_are_accepted(self) -> None:
        """A JSON round-trip through run_config yields string year keys."""
        mc, _b, _f = _mc(_cfg(True, {"2023": YEAR_LEVEL}), 2023)
        np.testing.assert_allclose(mc[2, :], _expected_peak(YEAR_LEVEL))


class YearLevelGuards(unittest.TestCase):
    def test_armed_without_table_is_a_hard_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            _mc(_cfg(True, None), 2023)
        self.assertIn("coal_peak_offer_level_yearly", str(ctx.exception))

    def test_armed_without_solve_year_is_a_hard_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            _mc(_cfg(True, {2023: YEAR_LEVEL}), None)
        self.assertIn("solve year", str(ctx.exception))

    def test_inert_without_the_margin_gate(self) -> None:
        """The year table has no meaning without ERCOT-140 armed."""
        mc, base, _f = _mc(_cfg(True, {2023: YEAR_LEVEL}, margin=False), 2023)
        np.testing.assert_array_equal(mc[2, :], base[2, :])


if __name__ == "__main__":
    unittest.main()
