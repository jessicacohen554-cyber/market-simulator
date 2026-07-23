"""Tests for the gas-offer net-revenue margin (markup compression) mechanism.

Covers the two halves of ``gas_offer_net_revenue_margin`` (design doc
``docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md``):

* the tranche-side markup decomposition (``gas_offer_margin_markup_mult`` +
  the ``offer_markup_hr`` computed in ``bins_to_fleet``), and
* the mc-side compression (``apply_gas_offer_margin``),

with the charter's trivial case first: one generator, gas swept $2 → $7 —
the fixed margin must be gas-INVARIANT under the reformed offer while the
multiplier form's markup scales linearly, and the two forms must coincide
exactly at the anchor. Composition guards: default-off byte-identity, the
neutral (no phys keys) fallback, non-gas rows untouched, hourly-varying
(post-dual-fuel) fuel rows, and the rule-23 tie of the registered NEISO
phys_* keys to the measured CAMPD marginal-HR artifact.
"""

import csv
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import bins_to_fleet
from market_sim.data.offer_curves import (
    apply_gas_offer_margin,
    gas_offer_margin_markup_mult,
)

ZONE_NAMES = get_iso_config("ERCOT").zone_names

# NEISO-style CT_PEAKER band dict with the measured physical basis keys
# (values from data/raw/reference/neiso_campd_marginal_hr_summary.csv p50s).
CT_BANDS = {
    "committed": 1.35,
    "econ_low": 1.0,
    "econ_high": 1.0,
    "peak": 4.0,
    "econ_low_share": 0.526,
    "pct_peaking": 7.0,
    "phys_committed": 0.985,
    "phys_econ_low": 0.745,
    "phys_econ_high": 0.700,
    "phys_peak": 1.0,
}

# CC-style rising econ ramp for the smoothing-slice interpolation tests.
CC_BANDS = {
    "committed": 1.27,
    "econ_low": 1.00,
    "econ_high": 1.15,
    "peak": 2.25,
    "econ_low_share": 0.50,
    "pct_peaking": 8.0,
    "phys_committed": 1.107,
    "phys_econ_low": 0.854,
    "phys_econ_high": 0.940,
    "phys_peak": 2.25,
}

CT_HR = 10.6  # synthetic plant base heat rate (MMBtu/MWh)
ANCHOR = 4.0  # test anchor ($/MMBtu)


def _bin(group: str, fuel: str, hr: float, plant: int = 1) -> pd.DataFrame:
    """One-row synthetic per-plant bin frame (test_campd_bins convention)."""
    return pd.DataFrame(
        [
            {
                "Plant_Group": group,
                "ERCOT_Zone": "Houston",
                "Bin_Number": 1,
                "Bin_Label": f"TEST{plant}",
                "Plant_Code": plant,
                "Plant_Name": f"Test Plant {plant}",
                "capacity_mw": 1000.0,
                "hr_weighted": hr,
                "hr_mr": hr,
                "hr_mc": hr,
                "hr_econ": hr,
                "hr_peak": hr,
                "pct_mr": 0,
                "pct_mc": 30,
                "pct_econ": 55,
                "pct_peak": 15,
                "min_run": 0,
                "min_down": 0,
                "plant_count": 1,
                "plant_codes": [plant],
                "fuel": fuel,
            }
        ]
    )


def _margin_config(**overrides) -> ScenarioConfig:
    """Config with the mechanism armed on the CT test curve."""
    base = dict(
        gas_offer_net_revenue_margin=True,
        gas_offer_margin_anchor=ANCHOR,
        offer_curve_by_group={"CT_PEAKER": dict(CT_BANDS)},
    )
    base.update(overrides)
    return ScenarioConfig(**base)


def _mc_and_fuel(fleet, gas: float, hours: int = 4):
    """Manual multiplier-form mc (heat_rate × fuel + vom) + flat fuel rows."""
    n = len(fleet)
    fuel = np.full((n, hours), float(gas))
    hr = np.array([g.heat_rate for g in fleet])
    vom = np.array([g.vom for g in fleet])
    return hr[:, None] * fuel + vom[:, None], fuel


class TestMarkupMultResolution(unittest.TestCase):
    """Band → markup resolution of ``gas_offer_margin_markup_mult``."""

    def test_committed_markup_above_physical(self):
        self.assertAlmostEqual(
            gas_offer_margin_markup_mult("committed", 1.35, CT_BANDS), 0.365
        )

    def test_committed_bid_below_physical_clips_to_zero(self):
        # Price-taker committed bands (CC_CHP 1.15 < block avg 1.399) never
        # produce a negative margin.
        bands = dict(CC_BANDS, phys_committed=1.399)
        self.assertEqual(gas_offer_margin_markup_mult("committed", 1.15, bands), 0.0)

    def test_committed_ramp_slices_use_slice_mult(self):
        self.assertAlmostEqual(
            gas_offer_margin_markup_mult("committed03", 1.40, CT_BANDS),
            1.40 - 0.985,
        )

    def test_econ_endpoints(self):
        self.assertAlmostEqual(
            gas_offer_margin_markup_mult("econlo", 1.0, CT_BANDS), 0.255
        )
        self.assertAlmostEqual(
            gas_offer_margin_markup_mult("econhi", 1.0, CT_BANDS), 0.300
        )

    def test_econ_slice_interpolates_physical_basis(self):
        # Slice at the ramp midpoint (mult 1.075 on the 1.00→1.15 ramp):
        # phys = 0.854 + (0.940-0.854)×0.5 = 0.897 → markup 0.178.
        self.assertAlmostEqual(
            gas_offer_margin_markup_mult("econc03", 1.075, CC_BANDS),
            1.075 - 0.897,
            places=9,
        )

    def test_econ_degenerate_flat_ramp_uses_midpoint(self):
        # lo == hi (the CT curve): a smoothing slice takes the midpoint basis.
        self.assertAlmostEqual(
            gas_offer_margin_markup_mult("econc00", 1.0, CT_BANDS),
            1.0 - (0.745 + 0.700) / 2.0,
        )

    def test_peak_and_ladder_rungs(self):
        self.assertAlmostEqual(gas_offer_margin_markup_mult("peak", 4.0, CT_BANDS), 3.0)
        self.assertAlmostEqual(
            gas_offer_margin_markup_mult("peak3", 4.4, CT_BANDS), 3.4
        )

    def test_bands_without_phys_keys_are_neutral(self):
        bare = {k: v for k, v in CT_BANDS.items() if not k.startswith("phys_")}
        for suffix, mult in (("committed", 1.35), ("econlo", 1.0), ("peak", 4.0)):
            self.assertEqual(gas_offer_margin_markup_mult(suffix, mult, bare), 0.0)

    def test_mustrun_and_sync_never_marked_up(self):
        self.assertEqual(gas_offer_margin_markup_mult("mustrun", 2.0, CT_BANDS), 0.0)
        self.assertEqual(gas_offer_margin_markup_mult("sync", 2.0, CT_BANDS), 0.0)


class TestBinsToFleetMarkup(unittest.TestCase):
    """``offer_markup_hr`` lands on the right tranches in ``bins_to_fleet``."""

    def _tranche_markups(self, config) -> dict[str, float]:
        fleet, _ = bins_to_fleet(_bin("CT_PEAKER", "gas_ct", CT_HR), ZONE_NAMES, config)
        return {
            g.unit_id.split("_")[-1]: g.offer_markup_hr
            for g in fleet
            if g.plant_code == 1
        }

    def test_flag_on_sets_markup_hr_per_band(self):
        marks = self._tranche_markups(_margin_config())
        self.assertAlmostEqual(marks["committed"], CT_HR * 0.365, places=6)
        self.assertAlmostEqual(marks["econlo"], CT_HR * 0.255, places=6)
        self.assertAlmostEqual(marks["econhi"], CT_HR * 0.300, places=6)
        self.assertAlmostEqual(marks["peak"], CT_HR * 3.0, places=6)

    def test_flag_off_leaves_markup_zero_and_offers_unchanged(self):
        cfg_off = ScenarioConfig(offer_curve_by_group={"CT_PEAKER": dict(CT_BANDS)})
        marks = self._tranche_markups(cfg_off)
        self.assertTrue(all(v == 0.0 for v in marks.values()))
        # The phys_* keys themselves never change the tranche heat rates.
        fleet_on, _ = bins_to_fleet(
            _bin("CT_PEAKER", "gas_ct", CT_HR), ZONE_NAMES, _margin_config()
        )
        fleet_off, _ = bins_to_fleet(
            _bin("CT_PEAKER", "gas_ct", CT_HR), ZONE_NAMES, cfg_off
        )
        for g_on, g_off in zip(fleet_on, fleet_off):
            self.assertEqual(g_on.unit_id, g_off.unit_id)
            self.assertAlmostEqual(g_on.heat_rate, g_off.heat_rate, places=9)
            self.assertAlmostEqual(g_on.pmax_mw, g_off.pmax_mw, places=9)

    def test_neutral_curve_class_gets_zero_markup(self):
        # A class whose curve carries no phys_* keys (every non-NEISO ISO, and
        # NEISO's CT_CHP) is inert even with the flag armed (rule 24).
        cfg = _margin_config(
            offer_curve_by_group={
                "CT_PEAKER": {
                    k: v for k, v in CT_BANDS.items() if not k.startswith("phys_")
                }
            }
        )
        marks = self._tranche_markups(cfg)
        self.assertTrue(all(v == 0.0 for v in marks.values()))


class TestGasSweepInvariance(unittest.TestCase):
    """The charter's trivial case: 1 gen, gas $2 → $7."""

    @classmethod
    def setUpClass(cls):
        cls.config = _margin_config()
        cls.fleet, _ = bins_to_fleet(
            _bin("CT_PEAKER", "gas_ct", CT_HR), ZONE_NAMES, cls.config
        )
        cls.rows = {g.unit_id.split("_")[-1]: i for i, g in enumerate(cls.fleet)}

    def _margins(self, gas: float) -> dict[str, tuple[float, float]]:
        """(multiplier-form markup, reformed margin) over TRUE band cost."""
        mc, fuel = _mc_and_fuel(self.fleet, gas)
        raw = mc.copy()
        apply_gas_offer_margin(mc, self.fleet, fuel, self.config)
        out = {}
        for band, phys in (
            ("committed", 0.985),
            ("econlo", 0.745),
            ("econhi", 0.700),
            ("peak", 1.0),
        ):
            g = self.fleet[self.rows[band]]
            true_cost = phys * CT_HR * gas + g.vom
            out[band] = (
                raw[self.rows[band], 0] - true_cost,
                mc[self.rows[band], 0] - true_cost,
            )
        return out

    def test_scarcity_margin_invariant_while_multiplier_markup_scales(self):
        sweep = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        peak_margins = [self._margins(g)["peak"] for g in sweep]
        mult_markups = [m[0] for m in peak_margins]
        fixed_margins = [m[1] for m in peak_margins]
        # Multiplier form: markup = 3.0 × HR × gas — linear in gas.
        for gas, mk in zip(sweep, mult_markups):
            self.assertAlmostEqual(mk, 3.0 * CT_HR * gas, places=6)
        self.assertAlmostEqual(mult_markups[-1] / mult_markups[0], 3.5, places=6)
        # Reformed: the scarcity margin is the SAME fixed $/MWh at every gas.
        for m in fixed_margins:
            self.assertAlmostEqual(m, 3.0 * CT_HR * ANCHOR, places=6)
        self.assertAlmostEqual(max(fixed_margins) - min(fixed_margins), 0.0, places=9)

    def test_every_band_margin_is_fuel_invariant(self):
        m2, m7 = self._margins(2.0), self._margins(7.0)
        for band in ("committed", "econlo", "econhi", "peak"):
            self.assertAlmostEqual(m2[band][1], m7[band][1], places=9)

    def test_exact_identity_at_anchor(self):
        mc, fuel = _mc_and_fuel(self.fleet, ANCHOR)
        raw = mc.copy()
        apply_gas_offer_margin(mc, self.fleet, fuel, self.config)
        np.testing.assert_allclose(mc, raw, rtol=0, atol=1e-12)

    def test_compression_is_two_sided(self):
        # Above anchor the offer sits BELOW the multiplier form (compression);
        # below anchor it sits ABOVE (the summer-undershoot half).
        for gas, sign in ((7.0, -1.0), (2.0, +1.0)):
            mc, fuel = _mc_and_fuel(self.fleet, gas)
            raw = mc.copy()
            apply_gas_offer_margin(mc, self.fleet, fuel, self.config)
            delta = mc[self.rows["peak"], 0] - raw[self.rows["peak"], 0]
            self.assertGreater(sign * delta, 0.0)


class TestApplyComposition(unittest.TestCase):
    """Gate, error, non-gas and post-dual-fuel composition of the apply."""

    def setUp(self):
        self.config = _margin_config()
        self.fleet, _ = bins_to_fleet(
            _bin("CT_PEAKER", "gas_ct", CT_HR), ZONE_NAMES, self.config
        )

    def test_flag_off_is_a_noop(self):
        mc, fuel = _mc_and_fuel(self.fleet, 6.0)
        raw = mc.copy()
        apply_gas_offer_margin(mc, self.fleet, fuel, ScenarioConfig())
        np.testing.assert_array_equal(mc, raw)

    def test_flag_on_without_anchor_raises(self):
        mc, fuel = _mc_and_fuel(self.fleet, 6.0)
        cfg = ScenarioConfig(gas_offer_net_revenue_margin=True)
        with self.assertRaises(ValueError):
            apply_gas_offer_margin(mc, self.fleet, fuel, cfg)

    def test_zero_markup_rows_untouched(self):
        # Rows outside the mechanism (markup 0 — e.g. a coal tranche or any
        # neutral band) never move, whatever the gas price.
        mc, fuel = _mc_and_fuel(self.fleet, 6.5)
        raw = mc.copy()
        zero_rows = [i for i, g in enumerate(self.fleet) if g.offer_markup_hr == 0.0]
        apply_gas_offer_margin(mc, self.fleet, fuel, self.config)
        for i in zero_rows:
            np.testing.assert_array_equal(mc[i], raw[i])

    def test_margin_keys_on_post_switch_fuel_rows(self):
        # The compression uses whatever delivered price the row carries — the
        # post-dual-fuel (oil-parity-capped) series included. Margin over the
        # physical part stays the fixed $/MWh in EVERY hour of a varying row.
        peak = next(i for i, g in enumerate(self.fleet) if g.unit_id.endswith("_peak"))
        n, hours = len(self.fleet), 5
        fuel = np.full((n, hours), 3.0)
        fuel[peak, :] = [2.0, 4.0, 9.0, 18.0, ANCHOR]  # cold-snap + oil parity
        hr = np.array([g.heat_rate for g in self.fleet])
        vom = np.array([g.vom for g in self.fleet])
        mc = hr[:, None] * fuel + vom[:, None]
        apply_gas_offer_margin(mc, self.fleet, fuel, self.config)
        g = self.fleet[peak]
        margins = mc[peak, :] - (1.0 * CT_HR * fuel[peak, :] + g.vom)
        np.testing.assert_allclose(
            margins, np.full(hours, 3.0 * CT_HR * ANCHOR), atol=1e-9
        )


class TestNeisoPhysRegistryProvenance(unittest.TestCase):
    """The registered NEISO phys_* keys tie to the measured CAMPD artifact."""

    def test_phys_keys_match_marginal_hr_summary(self):
        from market_sim.pipeline.backcast_config import _NEISO_OFFER_CURVE

        path = (
            Path(__file__).resolve().parents[1]
            / "data/raw/reference/neiso_campd_marginal_hr_summary.csv"
        )
        rows = {r["class"]: r for r in csv.DictReader(open(path))}
        expected = {
            # committed → avg_committed_p50 (block-average burn); econ →
            # marg_econ_{low,high}_p50 (incremental burn). Design doc table.
            "CC_REGULAR": (
                "avg_committed_p50",
                "marg_econ_low_p50",
                "marg_econ_high_p50",
            ),
            "CC_CHP": ("avg_committed_p50", "marg_econ_low_p50", "marg_econ_high_p50"),
            "CT_PEAKER": (
                "avg_committed_p50",
                "marg_econ_low_p50",
                "marg_econ_high_p50",
            ),
            "ST_GAS": ("avg_committed_p50", "marg_econ_low_p50", "marg_econ_high_p50"),
        }
        for cls, (c_col, lo_col, hi_col) in expected.items():
            bands = _NEISO_OFFER_CURVE[cls]
            src = rows[cls if cls != "CC_CHP" else "CC_CHP"]
            self.assertAlmostEqual(
                bands["phys_committed"], float(src[c_col]), places=3, msg=cls
            )
            self.assertAlmostEqual(
                bands["phys_econ_low"], float(src[lo_col]), places=3, msg=cls
            )
            self.assertAlmostEqual(
                bands["phys_econ_high"], float(src[hi_col]), places=3, msg=cls
            )
        # CT_CHP stays neutral (n=1 — not identifiable).
        self.assertFalse(
            any(k.startswith("phys_") for k in _NEISO_OFFER_CURVE["CT_CHP"])
        )
        # The registered anchor is the derive script's output.
        from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ISO

        self.assertAlmostEqual(GAS_OFFER_MARGIN_ANCHOR_BY_ISO["NEISO"], 4.0763)


if __name__ == "__main__":
    unittest.main()
