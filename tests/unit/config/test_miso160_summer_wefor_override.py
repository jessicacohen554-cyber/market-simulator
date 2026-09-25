"""miso-160: the measured seasonal forced-outage shape override.

``ScenarioConfig.summer_wefor_share_override`` (default ``None``) replaces the
uncited ``SUMMER_WEFOR_SHARE = 0.30`` heuristic with a per-ISO value derived
from a published ticket-based outage record (MISO first: R* = 1.0599, the
pooled 2023-2025 Jun-Sep/annual ratio of the MISO MOM record's unplanned
offline MW; PREREG-miso160-summer-wefor-measured-share-2026-08-16.md).

Pinned here:

1. ``None`` is byte-inert — the availability arrays are identical to the
   pre-field behavior (the constant applies);
2. an armed share moves EXACTLY the seasonal WEFOR split — summer down by
   ``(share - const) x WEFOR``, shoulder up by the conserving amount, winter
   untouched — for a governed (non-coal thermal) unit;
3. a share > 1 puts summer availability BELOW the annual base and the
   shoulder ABOVE the flat-WEFOR level (the measured sign), still conserving
   the annual mean;
4. COAL under ``coal_drop_pof=True`` stays exempt (its branch never reads the
   share).
"""

import unittest

import numpy as np

from market_sim.config.fuel_trajectories import SUMMER_WEFOR_SHARE
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays

# The branch-deciding flags of the MISO keeper (2026-08-15-miso-159-cod-vintage
# run_config.json), the config this override is chartered against.
KEEPER_FLAGS = dict(
    mode="backcast",
    outage_source="historic",
    wefor_residual=None,
    coal_drop_pof=True,
    cc_nameplate_summer_derate=False,
    maintenance_monthly_shape=False,
)

R_STAR = 1.0599  # the MISO derived value (probe _miso160_wefor_shape_instrument)


def _availability(group, fuel, override, online_year=2005):
    """(8760,) availability of one unit under the given override value."""
    gen = Generator(
        unit_id="g1",
        name="g1",
        zone="North",
        fuel_type=fuel,
        pmax_mw=100.0,
        pmin_mw=0.0,
        heat_rate=8.0,
        vom=2.0,
        emission_rate_co2=0.4,
        online_year=online_year,
        plant_group=group,
        efficiency_bin=group,
    )
    cfg = ScenarioConfig(
        weather_year=2023,
        summer_wefor_share_override=override,
        **KEEPER_FLAGS,
    )
    fa = generators_to_fleet_arrays([gen], ["North"], config=cfg)
    return fa.availability[0]


def _season_masks():
    import pandas as pd

    from market_sim.data.fleet.arrays import _CC_SHOULDER_MONTHS, _SUMMER_MONTHS

    m = pd.date_range("2023-01-01", periods=8760, freq="h").month.to_numpy()
    summer = np.isin(m, sorted(_SUMMER_MONTHS))
    shoulder = np.isin(m, sorted(_CC_SHOULDER_MONTHS))
    return summer, shoulder, ~summer & ~shoulder


class TestSummerWeforShareOverride(unittest.TestCase):
    def test_none_is_byte_inert(self):
        base = _availability("CT_PEAKER", "gas_ct", None)
        # Explicit None equals a config that never mentions the field.
        cfg = ScenarioConfig(weather_year=2023, **KEEPER_FLAGS)
        gen = Generator(
            unit_id="g1",
            name="g1",
            zone="North",
            fuel_type="gas_ct",
            pmax_mw=100.0,
            pmin_mw=0.0,
            heat_rate=8.0,
            vom=2.0,
            emission_rate_co2=0.4,
            online_year=2005,
            plant_group="CT_PEAKER",
            efficiency_bin="CT_PEAKER",
        )
        fa = generators_to_fleet_arrays([gen], ["North"], config=cfg)
        np.testing.assert_array_equal(base, fa.availability[0])

    def test_armed_share_moves_exactly_the_seasonal_split(self):
        # ST_GAS: no SUMMER_CLASS_DERATE entry and (under coal_drop_pof) no
        # shoulder POF, so the seasonal WEFOR split is the ONLY seasonal term
        # and the deltas are exact. (CT_PEAKER would carry the flat ambient
        # derate multiplier in summer with basis-aware off.)
        from market_sim.data.fleet.arrays import _thermal_outage

        summer, shoulder, winter = _season_masks()
        base = _availability("ST_GAS", "gas_st", None)
        armed = _availability("ST_GAS", "gas_st", R_STAR)
        d = armed - base
        _, wefor, _ = _thermal_outage("ST_GAS", 2023 - 2005)
        s2s = summer.sum() / shoulder.sum()

        # Winter: untouched, exactly.
        self.assertEqual(float(np.abs(d[winter]).max()), 0.0)
        # Summer: down by (R* - const) x WEFOR, exactly.
        np.testing.assert_allclose(
            d[summer], -(R_STAR - SUMMER_WEFOR_SHARE) * wefor, atol=1e-12
        )
        # Shoulder: up by the conserving amount, exactly.
        np.testing.assert_allclose(
            d[shoulder], (R_STAR - SUMMER_WEFOR_SHARE) * wefor * s2s, atol=1e-12
        )
        # Net: the annual mean is conserved.
        self.assertAlmostEqual(float(d.mean()), 0.0, places=12)

    def test_share_above_one_has_the_measured_sign(self):
        from market_sim.data.fleet.arrays import _thermal_outage

        summer, shoulder, _ = _season_masks()
        base = _availability("ST_GAS", "gas_st", None)
        armed = _availability("ST_GAS", "gas_st", R_STAR)
        _, wefor, derate = _thermal_outage("ST_GAS", 2023 - 2005)
        # Summer availability sits BELOW the flat-WEFOR level (share > 1
        # means summer forced-outage rate ABOVE annual — the measured sign)...
        flat = 1.0 - wefor - derate
        self.assertLess(float(armed[summer].mean()), flat)
        # ...while under the 0.30 heuristic it sat ABOVE it,
        self.assertGreater(float(base[summer].mean()), flat)
        # ...and the shoulder RISES (its displaced-outage add-back inverts).
        self.assertGreater(float(armed[shoulder].mean()), float(base[shoulder].mean()))

    def test_coal_stays_exempt(self):
        base = _availability("COAL_BIT", "coal", None)
        armed = _availability("COAL_BIT", "coal", R_STAR)
        np.testing.assert_array_equal(base, armed)


if __name__ == "__main__":
    unittest.main()
