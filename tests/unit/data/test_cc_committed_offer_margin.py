"""Tests for the CC committed-block measured offer level (ERCOT-139).

``ScenarioConfig.cc_committed_offer_margin`` — the coal min-load net-revenue
margin's gas-CC analogue: the CC_REGULAR ``_committed`` tranche is repriced
from its band multiplier to full delivered-fuel tracking plus a
fuel-invariant measured margin, landing EXACTLY on the measured RT SCED curve
bottom (``cc_committed_offer_level``) at the SHARED delivered-gas anchor.
Trivial fixtures first, per the repo testing pattern (1 generator, 24 hours).

The scope assertions are the rule-19 / rule-18 contract from the precommit:
CC_REGULAR ``_committed*`` rows only — ``econ*``/``peak*`` rows, CC_CHP, and
the legacy non-CAMPD path are all untouched, so the mechanism REPLACES the
band multiplier on exactly one row family and stacks on nothing.
"""

import unittest

import numpy as np

from market_sim.config.constants import (
    CC_COMMITTED_OFFER_LEVEL_BY_ISO,
    GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
)
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fleet.legacy_bins import assemble_mc
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.offer_curves import apply_cc_committed_offer_margin

ANCHOR = GAS_OFFER_MARGIN_ANCHOR_BY_ISO["ERCOT"]  # 2.2494 $/MMBtu, SHARED
LEVEL = CC_COMMITTED_OFFER_LEVEL_BY_ISO["ERCOT"]  # 10.354 $/MWh, measured
HOURS = 24
HR = 7.476  # the keeper's CC committed tranche HR (0.998 x base 7.491)
VOM = 2.0


def _cc(
    unit_id: str = "CC_H_p1_committed",
    group: str = "CC_REGULAR",
    campd: bool = True,
    heat_rate: float = HR,
) -> Generator:
    """One trivial gas-CC tranche row."""
    return Generator(
        unit_id=unit_id,
        name="t",
        zone="N",
        fuel_type="gas_cc",
        efficiency_bin="f_class",
        pmax_mw=100.0,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        vom=VOM,
        emission_rate_co2=0.38,
        nox_rate=0.0,
        eford=0.05,
        online_year=2005,
        is_campd_bin=campd,
        plant_group=group,
        bin_label="X",
        plant_code=1,
    )


def _armed(**kw) -> ScenarioConfig:
    """A config with the mechanism armed at the registered constants."""
    return ScenarioConfig(
        hours=HOURS,
        cc_committed_offer_margin=True,
        cc_committed_offer_level=LEVEL,
        gas_offer_margin_anchor=ANCHOR,
        **kw,
    )


def _mc(gens: list[Generator], config: ScenarioConfig, fuel_mmbtu: float):
    """Assemble base MC for ``gens`` and apply the ERCOT-139 seam."""
    fa = generators_to_fleet_arrays(gens, ["N"], config=config, hours=HOURS)
    fuel = np.full((len(gens), HOURS), fuel_mmbtu)
    mc = assemble_mc(fa, fuel, 0.0, 0.0)
    apply_cc_committed_offer_margin(mc, gens, fa, config)
    return mc


class TestCcCommittedOfferMargin(unittest.TestCase):
    """The measured form's identity, fuel tracking, scope and hard errors."""

    def test_flag_off_is_byte_identical(self):
        """Default-off keeps the band-multiplier bid exactly (rule: no-op)."""
        cfg = ScenarioConfig(hours=HOURS)
        mc = _mc([_cc()], cfg, ANCHOR)
        self.assertAlmostEqual(float(mc[0, 0]), HR * ANCHOR + VOM, places=9)

    def test_bid_at_anchor_is_exactly_the_measured_level(self):
        """The identification point: at fuel == anchor the bid IS the level."""
        mc = _mc([_cc()], _armed(), ANCHOR)
        self.assertAlmostEqual(float(mc[0, 0]), LEVEL, places=9)

    def test_full_delivered_fuel_tracking_off_anchor(self):
        """Off anchor the bid moves at the tranche's OWN heat rate."""
        for fuel in (1.5, ANCHOR, 3.232, 6.0):
            with self.subTest(fuel=fuel):
                mc = _mc([_cc()], _armed(), fuel)
                self.assertAlmostEqual(
                    float(mc[0, 0]), HR * (fuel - ANCHOR) + LEVEL, places=9
                )

    def test_margin_is_fuel_invariant(self):
        """bid − physical fuel cost is the same $/MWh at every gas price."""
        margins = {
            round(float(_mc([_cc()], _armed(), f)[0, 0]) - HR * f, 9)
            for f in (1.5, 2.2494, 3.232, 6.0)
        }
        self.assertEqual(len(margins), 1)
        self.assertAlmostEqual(margins.pop(), LEVEL - HR * ANCHOR, places=9)

    def test_per_tranche_heat_rate_not_a_fleet_constant(self):
        """Two plants with different HRs keep their own fuel slopes."""
        gens = [
            _cc(unit_id="CC_A_p1_committed", heat_rate=6.5),
            _cc(unit_id="CC_B_p1_committed", heat_rate=8.5),
        ]
        mc = _mc(gens, _armed(), 3.232)
        self.assertAlmostEqual(
            float(mc[0, 0]), 6.5 * (3.232 - ANCHOR) + LEVEL, places=9
        )
        self.assertAlmostEqual(
            float(mc[1, 0]), 8.5 * (3.232 - ANCHOR) + LEVEL, places=9
        )
        # Both land on the level together at the anchor.
        mc_a = _mc(gens, _armed(), ANCHOR)
        self.assertAlmostEqual(float(mc_a[0, 0]), LEVEL, places=9)
        self.assertAlmostEqual(float(mc_a[1, 0]), LEVEL, places=9)

    def test_committed_ramp_slices_are_in_scope(self):
        """``committedNN`` rising slices share the committed block's vocabulary.

        A non-zero ``committed_ramp_spread`` renders the block as
        ``committed`` + ``committed01``.. (``_econ_curve_steps`` in
        ``fleet/assembly.py``); all of them are the measured block.
        """
        for sfx in ("committed", "committed01", "committed07"):
            with self.subTest(suffix=sfx):
                mc = _mc([_cc(unit_id=f"CC_H_p1_{sfx}")], _armed(), ANCHOR)
                self.assertAlmostEqual(float(mc[0, 0]), LEVEL, places=9)

    def test_econ_peak_and_mustrun_rows_untouched(self):
        """Rule 19: only the committed block is repriced (econ/peak keep owners)."""
        for sfx in ("econlo", "econhi", "econc03", "peak", "peak2", "mustrun"):
            with self.subTest(suffix=sfx):
                gen = _cc(unit_id=f"CC_H_p1_{sfx}")
                mc = _mc([gen], _armed(), ANCHOR)
                self.assertAlmostEqual(float(mc[0, 0]), HR * ANCHOR + VOM, places=9)

    def test_cc_chp_is_out_of_scope(self):
        """CC_CHP is never pooled into the measured CC control (rule 18/19)."""
        mc = _mc([_cc(group="CC_CHP")], _armed(), ANCHOR)
        self.assertAlmostEqual(float(mc[0, 0]), HR * ANCHOR + VOM, places=9)

    def test_other_classes_are_out_of_scope(self):
        """CT/ST/coal committed rows keep their own mechanisms."""
        for group in ("CT_PEAKER", "ST_GAS", "COAL", "CT_CHP"):
            with self.subTest(group=group):
                mc = _mc([_cc(group=group)], _armed(), ANCHOR)
                self.assertAlmostEqual(float(mc[0, 0]), HR * ANCHOR + VOM, places=9)

    def test_legacy_non_campd_path_is_inert(self):
        """Scope is the CAMPD tranche path only (mirrors the coal form)."""
        mc = _mc([_cc(campd=False)], _armed(), ANCHOR)
        self.assertAlmostEqual(float(mc[0, 0]), HR * ANCHOR + VOM, places=9)

    def test_armed_without_level_is_a_hard_error(self):
        """Rule 25: no silent fallback in the offer path."""
        cfg = ScenarioConfig(
            hours=HOURS,
            cc_committed_offer_margin=True,
            gas_offer_margin_anchor=ANCHOR,
        )
        with self.assertRaises(ValueError) as ctx:
            _mc([_cc()], cfg, ANCHOR)
        self.assertIn("cc_committed_offer_level", str(ctx.exception))

    def test_armed_without_shared_anchor_is_a_hard_error(self):
        """The anchor is SHARED with the gas margin form and must be resolved."""
        cfg = ScenarioConfig(
            hours=HOURS,
            cc_committed_offer_margin=True,
            cc_committed_offer_level=LEVEL,
        )
        with self.assertRaises(ValueError) as ctx:
            _mc([_cc()], cfg, ANCHOR)
        self.assertIn("gas_offer_margin_anchor", str(ctx.exception))

    def test_default_cache_key_is_byte_stable(self):
        """The new fields are registered as dropped-at-default (rule 24)."""
        self.assertEqual(ScenarioConfig().cache_key(), "e5ecd4105ada3e58")

    def test_armed_cache_key_is_a_distinct_scenario(self):
        """An armed run must not collide with the default's cached results."""
        self.assertNotEqual(_armed().cache_key(), ScenarioConfig().cache_key())


class TestCcCommittedOfferLevelIdentification(unittest.TestCase):
    """The registered constant matches its committed-artifact derivation."""

    def test_registered_level_matches_the_derive(self):
        """constants entry == derive_cc_committed_offer_margin.py output."""
        import importlib.util
        from pathlib import Path

        repo = Path(__file__).resolve().parents[3]
        path = repo / "scripts/data/derive_cc_committed_offer_margin.py"
        spec = importlib.util.spec_from_file_location("_d139", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = mod.derive_ercot()
        self.assertAlmostEqual(out["level_usd_mwh"], LEVEL, places=4)
        self.assertAlmostEqual(out["anchor_usd_mmbtu"], ANCHOR, places=4)
        # The form's own falsifier: a physically sensible CC offer heat rate,
        # and an anchored dispersion far tighter than the raw one.
        self.assertGreater(out["primary"]["hr_implied_mmbtu_per_mwh"], 5.5)
        self.assertLess(out["primary"]["hr_implied_mmbtu_per_mwh"], 11.0)
        self.assertLess(
            out["primary"]["dispersion_anchored_pct"],
            out["primary"]["dispersion_raw_pct"] / 3.0,
        )
        # Independent Min-Gen-Cost instrument corroborates within 10 %.
        self.assertLess(out["corroboration_spread_pct"], 10.0)


if __name__ == "__main__":
    unittest.main()
