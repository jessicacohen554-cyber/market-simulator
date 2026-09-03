"""Measured ST_GAS PEAK band at the ``ST_GAS_PEAKER_PLANTS`` bypass (caiso-240).

The band-disjoint sibling of ``test_caiso_st_gas_committed_measured`` (rule 19
``[R-ONE-MECH]``). ``offer_curves._offer_curve_for_group`` returns ``None`` for
every ``ST_GAS_PEAKER_PLANTS`` member, so those plants never reach
``peak_hr = base_hr x offer["peak"]`` in ``bins_to_fleet`` and fall through to
the uncited ERCOT-lineage class default
``campd_bins._DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]["peak"] = 1.10`` — the second of
the two cells the caiso-240 census measured still live on the CAISO keeper, and
the only one of them whose measured counterpart is at the model's own grain.
``ScenarioConfig.caiso_st_gas_peak_measured`` replaces it with the ISO's own
measured peak-band offer multiplier, which is ALREADY the value the CAISO ST_GAS
class band carries — the bypass is what keeps it from the plants the measured CT
bucket contains.

These tests pin the gate's six contracts: byte-identical OFF; the measured
multiplier ON; EXACTLY ONE band moves; the caiso-239 sibling is band-disjoint
from it, so arming both moves exactly two bands and neither interferes; a
non-bypassed ST_GAS plant is untouched either way; and an ISO with no registry
entry is a HARD ERROR rather than a silent fallback to the class default.
"""

import unittest

import pandas as pd

from market_sim.config.constants import (
    ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO,
    ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import bins_to_fleet
from market_sim.data.outages import ST_GAS_PEAKER_PLANTS

ZONE_NAMES = get_iso_config("CAISO").zone_names
ZONE = ZONE_NAMES[0]

#: AES Alamitos — a CAISO member of the bypass set (data/outages.py).
BYPASSED_PLANT = 315
#: A plant code outside the bypass set, so it resolves the class offer curve.
NORMAL_PLANT = 999001

BASE_HR = 11.85
#: campd_bins._DEFAULT_HR_MULT_BY_GROUP["ST_GAS"] — the values a bypassed bin
#: takes today. Mirrored here so a change to that table fails this test loudly.
CLASS_DEFAULTS = {"mr": 1.10, "mc": 1.15, "econ": 1.00, "peak": 1.10}
MEASURED_PEAK = ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO["CAISO"]
MEASURED_COMMITTED = ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO["CAISO"]

ST_GAS_BANDS = {
    "committed": 0.81,
    "econ_low": 1.145,
    "econ_high": 1.166,
    "peak": 1.166,
    "econ_low_share": 0.5,
    "pct_peaking": 15.0,
}


def _bin(plant: int) -> dict:
    """One synthetic per-plant ST_GAS bin row with the class-default band HRs."""
    return {
        "Plant_Group": "ST_GAS",
        "ERCOT_Zone": ZONE,  # the bin sheet's zone column, whatever the ISO
        "Bin_Number": 1,
        "Bin_Label": f"TEST{plant}",
        "Plant_Code": plant,
        "Plant_Name": f"Test Plant {plant}",
        "capacity_mw": 1000.0,
        "hr_weighted": BASE_HR,
        "hr_mr": BASE_HR * CLASS_DEFAULTS["mr"],
        "hr_mc": BASE_HR * CLASS_DEFAULTS["mc"],
        "hr_econ": BASE_HR * CLASS_DEFAULTS["econ"],
        "hr_peak": BASE_HR * CLASS_DEFAULTS["peak"],
        "pct_mr": 0,
        "pct_mc": 7,
        "pct_econ": 78,
        "pct_peak": 15,
        "min_run": 0,
        "min_down": 0,
        "plant_count": 1,
        "plant_codes": [plant],
        "fuel": "gas_st",
    }


def _config(iso: str = "CAISO", **overrides) -> ScenarioConfig:
    # mode="backcast" is REQUIRED, not incidental: this gate is a member of
    # _BACKCAST_ONLY_OVERLAY_FIELDS (rule 13 [R-MEASURED] — it arms measured
    # OASIS BID conduct keyed to a specific year's record), so arming it in
    # forecast mode is a hard error. Its caiso-239 sibling, which arms a
    # measured PHYSICAL heat-rate ratio, is deliberately NOT in that family and
    # needs no mode. `test_forecast_mode_is_a_hard_error` pins the difference.
    base = dict(
        iso=iso,
        mode="backcast",
        offer_curve_by_group={"ST_GAS": dict(ST_GAS_BANDS)},
    )
    base.update(overrides)
    return ScenarioConfig(**base)


def _band_hrs(config: ScenarioConfig, plant: int) -> dict[str, float]:
    """``{band suffix: heat rate}`` for one plant's tranches."""
    fleet, _ = bins_to_fleet(pd.DataFrame([_bin(plant)]), ZONE_NAMES, config)
    return {g.unit_id.rsplit("_", 1)[-1]: g.heat_rate for g in fleet}


class TestCaisoStGasPeakMeasured(unittest.TestCase):
    def test_bypass_set_contains_the_caiso_otc_steamers(self):
        """The premise: 315/335/350 really are bypassed (caiso-239 §1 F-1)."""
        for plant in (315, 335, 350):
            self.assertIn(plant, ST_GAS_PEAKER_PLANTS)

    def test_off_is_the_class_default(self):
        """OFF: the bypassed plant's peak band is base_hr x 1.10."""
        hrs = _band_hrs(_config(), BYPASSED_PLANT)
        self.assertAlmostEqual(hrs["peak"], BASE_HR * CLASS_DEFAULTS["peak"], places=9)
        # ...and NOT the class band multiplier, which is the whole defect: the
        # measured 1.166 sits in the class band and never reaches this plant.
        self.assertNotAlmostEqual(hrs["peak"], BASE_HR * ST_GAS_BANDS["peak"], places=6)

    def test_on_is_the_measured_multiplier(self):
        """ON: the peak band takes the ISO's measured peak-band multiplier."""
        hrs = _band_hrs(_config(caiso_st_gas_peak_measured=True), BYPASSED_PLANT)
        self.assertAlmostEqual(hrs["peak"], BASE_HR * MEASURED_PEAK, places=9)

    def test_exactly_one_band_moves(self):
        """Every band except ``peak`` is byte-identical armed or not."""
        off = _band_hrs(_config(), BYPASSED_PLANT)
        on = _band_hrs(_config(caiso_st_gas_peak_measured=True), BYPASSED_PLANT)
        self.assertEqual(set(off), set(on))
        moved = {b for b in off if off[b] != on[b]}
        self.assertEqual(moved, {"peak"})

    def test_the_two_siblings_are_band_disjoint(self):
        """Rule 19 [R-ONE-MECH]: caiso-239 owns ``committed``, caiso-240 ``peak``.

        Arming both moves exactly two bands, each to its own measured value, and
        neither mechanism perturbs the other's band.
        """
        off = _band_hrs(_config(), BYPASSED_PLANT)
        both = _band_hrs(
            _config(
                caiso_st_gas_committed_measured=True,
                caiso_st_gas_peak_measured=True,
            ),
            BYPASSED_PLANT,
        )
        moved = {b for b in off if off[b] != both[b]}
        self.assertEqual(moved, {"committed", "peak"})
        self.assertAlmostEqual(both["peak"], BASE_HR * MEASURED_PEAK, places=9)
        self.assertAlmostEqual(
            both["committed"], BASE_HR * MEASURED_COMMITTED, places=9
        )

    def test_non_bypassed_plant_is_untouched(self):
        """A plant that resolves the offer curve keeps the class band, ON or OFF."""
        expected = BASE_HR * ST_GAS_BANDS["peak"]
        for armed in (False, True):
            hrs = _band_hrs(_config(caiso_st_gas_peak_measured=armed), NORMAL_PLANT)
            self.assertAlmostEqual(hrs["peak"], expected, places=9)

    def test_unregistered_iso_is_a_hard_error(self):
        """Rule 25: no cross-ISO transfer, and no silent class-default fallback."""
        config = _config(iso="ERCOT", caiso_st_gas_peak_measured=True)
        with self.assertRaises(ValueError) as ctx:
            bins_to_fleet(pd.DataFrame([_bin(BYPASSED_PLANT)]), ZONE_NAMES, config)
        self.assertIn("ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO", str(ctx.exception))

    def test_forecast_mode_is_a_hard_error(self):
        """Rule 13: this gate arms measured BID conduct, so it is backcast-only.

        The contrast with its caiso-239 sibling is the point and is asserted
        both ways: the physical-ratio mechanism carries no mode restriction.
        """
        with self.assertRaises(ValueError) as ctx:
            ScenarioConfig(
                iso="CAISO", mode="forecast", caiso_st_gas_peak_measured=True
            )
        self.assertIn("caiso_st_gas_peak_measured", str(ctx.exception))
        # The sibling is NOT backcast-only — a measured physical heat-rate ratio
        # regenerates for a forward year.
        ScenarioConfig(
            iso="CAISO", mode="forecast", caiso_st_gas_committed_measured=True
        )

    def test_registry_value_matches_the_committed_artifact(self):
        """The registry value IS the committed OASIS bid artifact's peak (rule 23).

        And it is the SAME number the CAISO ST_GAS class band already carries —
        which is what makes this a delivery of an existing measurement to its own
        population rather than a new one (rule 21 ``[R-DOF]``: zero free
        parameters).
        """
        import json

        from market_sim.config import paths

        path = paths.RAW_DIR / "_validation-source" / "caiso_offer_curve_measured.json"
        artifact = json.loads(path.read_text())
        self.assertAlmostEqual(
            float(artifact["CT_PEAKER"]["bands"]["peak"]), MEASURED_PEAK, places=6
        )
        self.assertAlmostEqual(float(ST_GAS_BANDS["peak"]), MEASURED_PEAK, places=6)


if __name__ == "__main__":
    unittest.main()
