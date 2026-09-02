"""Measured ST_GAS committed band at the ``ST_GAS_PEAKER_PLANTS`` bypass (caiso-239).

``offer_curves._offer_curve_for_group`` returns ``None`` for every
``ST_GAS_PEAKER_PLANTS`` member, so those plants never reach
``committed_hr = base_hr x offer["committed"]`` in ``bins_to_fleet`` and fall
through to the uncited ERCOT-lineage class default
``campd_bins._DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]["mc"] = 1.15`` instead — an
off-registry channel (rule 24 ``[R-REGISTRY]``) carrying an out-of-ISO fitted
value (rule 25 ``[R-ISO-SCOPE]``) on CAISO's whole OTC steam fleet, invisible in
every ``run_config.json``. ``ScenarioConfig.caiso_st_gas_committed_measured``
replaces it with the ISO's own measured min-load block-average burn ratio.

These tests pin the gate's five contracts: byte-identical OFF; the measured
multiplier ON; EXACTLY ONE band moves; a non-bypassed ST_GAS plant (one that
resolves an offer curve) is untouched either way; and an ISO with no registry
entry is a HARD ERROR rather than a silent fallback to the class default.
"""

import unittest

import pandas as pd

from market_sim.config.constants import ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO
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
MEASURED = ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO["CAISO"]

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
    base = dict(iso=iso, offer_curve_by_group={"ST_GAS": dict(ST_GAS_BANDS)})
    base.update(overrides)
    return ScenarioConfig(**base)


def _band_hrs(config: ScenarioConfig, plant: int) -> dict[str, float]:
    """``{band suffix: heat rate}`` for one plant's tranches."""
    fleet, _ = bins_to_fleet(pd.DataFrame([_bin(plant)]), ZONE_NAMES, config)
    return {g.unit_id.rsplit("_", 1)[-1]: g.heat_rate for g in fleet}


class TestCaisoStGasCommittedMeasured(unittest.TestCase):
    def test_bypass_set_contains_the_caiso_otc_steamers(self):
        """The premise: 315/335/350 really are bypassed (caiso-239 §1 F-1)."""
        for plant in (315, 335, 350):
            self.assertIn(plant, ST_GAS_PEAKER_PLANTS)

    def test_off_is_the_class_default(self):
        """OFF: the bypassed plant's committed band is base_hr x 1.15."""
        hrs = _band_hrs(_config(), BYPASSED_PLANT)
        self.assertAlmostEqual(
            hrs["committed"], BASE_HR * CLASS_DEFAULTS["mc"], places=9
        )
        # ...and NOT the class band multiplier, which is what makes the
        # chartered scalar inert on these plants.
        self.assertNotAlmostEqual(
            hrs["committed"], BASE_HR * ST_GAS_BANDS["committed"], places=6
        )

    def test_on_is_the_measured_multiplier(self):
        """ON: the committed band takes the measured avg_committed_p50."""
        hrs = _band_hrs(_config(caiso_st_gas_committed_measured=True), BYPASSED_PLANT)
        self.assertAlmostEqual(hrs["committed"], BASE_HR * MEASURED, places=9)

    def test_exactly_one_band_moves(self):
        """Every band except ``committed`` is byte-identical armed or not."""
        off = _band_hrs(_config(), BYPASSED_PLANT)
        on = _band_hrs(_config(caiso_st_gas_committed_measured=True), BYPASSED_PLANT)
        self.assertEqual(set(off), set(on))
        moved = {b for b in off if off[b] != on[b]}
        self.assertEqual(moved, {"committed"})

    def test_non_bypassed_plant_is_untouched(self):
        """A plant that resolves the offer curve keeps the class band, ON or OFF."""
        expected = BASE_HR * ST_GAS_BANDS["committed"]
        for armed in (False, True):
            hrs = _band_hrs(
                _config(caiso_st_gas_committed_measured=armed), NORMAL_PLANT
            )
            self.assertAlmostEqual(hrs["committed"], expected, places=9)

    def test_unregistered_iso_is_a_hard_error(self):
        """Rule 25: no cross-ISO transfer, and no silent class-default fallback."""
        config = _config(iso="ERCOT", caiso_st_gas_committed_measured=True)
        with self.assertRaises(ValueError) as ctx:
            bins_to_fleet(pd.DataFrame([_bin(BYPASSED_PLANT)]), ZONE_NAMES, config)
        self.assertIn("ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO", str(ctx.exception))

    def test_registry_value_matches_the_committed_artifact(self):
        """The registry value IS the committed CAMPD artifact's p50 (rule 23)."""
        import csv

        from market_sim.config import paths

        path = paths.RAW_DIR / "reference" / "caiso_campd_marginal_hr_summary.csv"
        row = next(r for r in csv.DictReader(path.open()) if r["class"] == "ST_GAS")
        self.assertAlmostEqual(float(row["avg_committed_p50"]), MEASURED, places=6)
        # The population that makes this a substitution rather than a transplant.
        self.assertEqual(int(row["n_units"]), 10)


if __name__ == "__main__":
    unittest.main()
